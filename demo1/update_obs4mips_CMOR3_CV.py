#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 13:49:08 2016

This script generates all json files required to run obs4MIPs data creation and
then calls cmor3 to generate two example files.

The file is split into 3 sections:
    1 - creates controlled vocabulary (CV) json inputs for CMOR3
    2 - creates an Omon (ocean monthly) json input for generating a 'tos'
        variable from a CF-compliant input
    3 - creates an fx (fixed field) json input for generating an 'areacello'
        variable from a CF-compliant input

PJD 20 Jul 2016     - Removed source_id
PJD 20 Jul 2016     - Further tweaks to enhance readability
                    - TODO:

@author: durack1
"""

#%% Import statements
import cmor,gc,json,os,ssl,sys,urllib2

#%% Set local path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1])) ; # Extract path from executing file
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/' ; # Hard code path
#homePath = '/sync/git/obs4MIPs-cmor-tables/demo' ; # Hard code path
os.chdir(homePath)

#%% Function definitions

# Loop through input tables
def readJsonCreateDict(buildList):
    '''
    Documentation for readJsonCreateDict(buildList):
    -------
    The readJsonCreateDict() function reads web-based json files and writes
    their contents to a dictionary in memory

    Author: Paul J. Durack : pauldurack@llnl.gov

    Usage:
    ------
        >>> from runCMOR3 import readJsonCreateDict
        >>> readJsonCreateDict(['Omon','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_Omon.json'])

    Notes:
    -----
        ...
    '''
    # Test for list input of length == 2
    if len(buildList[0]) != 2:
        print 'Invalid inputs, exiting..'
        sys.exit()
    # Create urllib2 context to deal with lab/LLNL web certificates
    ctx                 = ssl.create_default_context()
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE
    # Iterate through buildList and write results to jsonDict
    jsonDict = {}       
    for count,table in enumerate(buildList):
        print 'Processing:',table[0]
        # Read web file
        jsonOutput = urllib2.urlopen(table[1], context=ctx)
        tmp = jsonOutput.read()
        vars()[table[0]] = tmp
        jsonOutput.close()
        # Write local json
        tmpFile = open('tmp.json','w')
        tmpFile.write(eval(table[0]))
        tmpFile.close()
        # Read local json
        vars()[table[0]] = json.load(open('tmp.json','r'))
        os.remove('tmp.json')
        jsonDict[table[0]] = eval(table[0]) ; # Write to dictionary
    
    return jsonDict

#%% SECTION 1 - Integrate all controlled vocabularies (CVs) into master file - create obs4MIPs_CV.json
jsonCVs = 'obs4MIPs_CV.json'
obs4mips_repo = 'https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/'
cmip6_repo = 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/'
buildList = [
 ['activity_id', obs4mips_repo + 'obs4MIPs_activity_id.json'],
 ['frequency', obs4mips_repo + 'obs4MIPs_frequency.json'],
 ['further_info_url', obs4mips_repo + 'obs4MIPs_further_info_url.json'],
 ['grid_label', obs4mips_repo + 'obs4MIPs_grid_label.json'],
 ['institution_id', obs4mips_repo + 'obs4MIPs_institution_id.json'],
 ['mip_era', obs4mips_repo + 'obs4MIPs_mip_era.json'],
 ['nominal_resolution', obs4mips_repo + 'obs4MIPs_nominal_resolution.json'],
 ['product', obs4mips_repo + 'obs4MIPs_product.json'],
 ['realm', obs4mips_repo + 'obs4MIPs_realm.json'],
 ['required_global_attributes', obs4mips_repo + 'obs4MIPs_required_global_attributes.json'],
 ['source_type', obs4mips_repo + 'obs4MIPs_source_type.json'],
 ['source_version_number', obs4mips_repo + 'obs4MIPs_source_version_number.json'],
 ['table_id', obs4mips_repo + 'obs4MIPs_table_id.json'],
 ['tracking_id', obs4mips_repo + 'obs4MIPs_tracking_id.json'],
 ['variant_label', obs4mips_repo + 'obs4MIPs_variant_label.json'],
 ['coordinate', cmip6_repo + 'CMIP6_coordinate.json'],
 ['formula_terms', cmip6_repo + 'CMIP6_formula_terms.json']
 ] ;



# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
	vars()[table] = tmp[table].get(table)
#	if table == 'coordinate':
#		vars()[table] = tmp[table].get(table)
#	else:
#		vars()[table] = tmp[table]
del(tmp,count,table) ; gc.collect()

# Rebuild dictionaries
obs4MIPs_CV = {}
obs4MIPs_CV['CV'] = {}
for count,CV in enumerate(buildList):
    CVName1 = CV[0]
    if CVName1 in ['coordinate','formula_terms','grids']:
        continue
    else:
        obs4MIPs_CV['CV'][CVName1] = eval(CVName1)

outFilePairs = {'obs4MIPs_CV':'obs4MIPs_CV.json',
                'coordinate':'CMIP6_coordinate.json',
                'formula_terms':'CMIP6_formula_terms.json'}

try:
  os.mkdir('obs4MIPs_CMOR_tables')
except:
  pass

outFile = 'obs4MIPs_CMOR_tables/obs4MIPs_CV.json'
# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

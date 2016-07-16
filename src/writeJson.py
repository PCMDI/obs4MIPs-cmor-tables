#!/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 16:11:44 2016

Paul J. Durack 12th July 2016

This script generates all json files residing this this subdirectory

PJD 12 Jul 2016     - Started
PJD 13 Jul 2016     - Updated to download existing tables
PJD 14 Jul 2016     - Successfully loaded dictionaries
PJD 15 Jul 2016     - Tables successfully created, coordinates from CMIP6_CVs
PJD 15 Jul 2016     - TODO:

@author: durack1
"""

#%% Import statements
import gc,json,os,ssl,time,urllib2
#homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
homePath = '/export/durack1/git/obs4MIPs-cmor-tables/'
print homePath
os.chdir(homePath)

#%% urllib2 config
# Create urllib2 context to deal with lab certs
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% List target tables
masterTargets = [
 'coordinate',
 'Amon',
 'Lmon',
 'Omon',
 'SImon'
 ] ;

#%% Tables
tableSource = [
 'https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_coordinate.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Amon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Lmon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Omon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SImon.json'
 ] ;

#%% Loop through tables and create in-memory objects
# Loop through input tables
for count,table in enumerate(tableSource):
    print count,masterTargets[count],table
    # Read web file
    jsonOutput                      = urllib2.urlopen(table, context=ctx)
    tmp                             = jsonOutput.read()
    vars()[masterTargets[count]]    = tmp
    jsonOutput.close()
    # Write local json
    tmpFile                         = open('tmp.json','w')
    tmpFile.write(eval(masterTargets[count]))
    tmpFile.close()
    # Read local json
    vars()[masterTargets[count]]    = json.load(open('tmp.json','r'))
    os.remove('tmp.json')
    del(tmp,jsonOutput)
    del(count,table) ; gc.collect()

#%% Cleanup by extracting only variable lists
for table in masterTargets:
    if table == 'coordinate':
        pass
    else:
        eval(table).pop('axis_entry')
        eval(table)['Header'].pop('generic_levels')
        eval(table)['Header']['table_date'] = time.strftime('%d %B %Y')

#%% Cleanup realms
Amon['Header']['realm']     = 'atmos'
Lmon['Header']['realm']     = 'land'
Omon['Header']['realm']     = 'ocean'
SImon['Header']['realm']    = 'seaIce'

#%% Write variables to files
for jsonName in masterTargets:
    # Clean experiment formats
    if jsonName in ['coordinate','experiment_id','grid','formula_terms']:
        dictToClean = eval(jsonName)
        for key, value in dictToClean.iteritems():
            for values in value.iteritems():
                string = dictToClean[key][values[0]]
                if not isinstance(string, list):
                    string = string.strip() ; # Remove trailing whitespace
                    string = string.strip(',.') ; # Remove trailing characters
                    string = string.replace(' + ',' and ')  ; # Replace +
                    string = string.replace(' & ',' and ')  ; # Replace +
                    string = string.replace('   ',' ') ; # Replace '  ', '   '
                    string = string.replace('anthro ','anthropogenic ') ; # Replace anthro
                    string = string.replace('  ',' ') ; # Replace '  ', '   '
                dictToClean[key][values[0]] = string
        vars()[jsonName] = dictToClean
    # Write file
    if jsonName == 'mip_era':
        outFile = ''.join(['../',jsonName,'.json'])
    else:
        outFile = ''.join(['../obs4MIPs_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    fH = open(outFile,'w')
    json.dump(eval(jsonName),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

del(jsonName,outFile) ; gc.collect()

# Validate - only necessary if files are not written by json module

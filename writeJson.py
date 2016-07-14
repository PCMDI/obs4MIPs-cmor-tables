#!/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 16:11:44 2016

Paul J. Durack 12th July 2016

This script generates all json files residing this this subdirectory

PJD 12 Jul 2016     - Started
PJD 13 Jul 2016     - Updated to download existing tables
PJD 14 Jul 2016     - Successfully loaded dictionaries
PJD 14 Jul 2016     - TODO:

@author: durack1
"""

#%% Import statements
import gc,json,os,ssl,urllib2
#homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
homePath = '/export/durack1/git/obs4MIPs-cmor-tables/'
print homePath
os.chdir(homePath)

#%% List target tables
masterTargets = [
 'Amon',
 'Lmon',
 'Omon',
 'SImon'
 ] ;

#%% Tables
tableSource = [
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Amon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Lmon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Omon.json',
 'https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SImon.json'
 ] ;
    
#%% Loop through tables and create in-memory objects
# Create urllib2 context to deal with lab certs
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE
# Loop through input tables
for count,table in enumerate(tableSource):
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

#%% Cleanup

Amon.get('axis_entry').keys()
sorted(Amon.get('axis_entry').keys())

#%%    
tmpFile = open('tmp.json','w')
tmpFile.write(Amon)
tmpFile.close()
newDict = json.load(open('tmp.json','r'))

#json.dump(eval(masterTargets[count]),tmpFile,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
#json.dump(tmpFile,eval(test),ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
#tmpFile.close()
    
    
#%%

experiment  = exps['CV']['experiment_ids'] ;
# Fix issues
experiment['1pctCO2Ndep']['experiment']             = '1 percent per year increasing CO2 experiment with increasing N-deposition'
experiment['omip1'] = experiment.pop('omipv1')


#%% Write variables to files
for jsonName in masterTargets:
    # Clean formats
    for key, value in experiment.iteritems():
        for values in value.iteritems():
            string = experiment[key][values[0]]
            string = string.strip() ; # Remove whitespace
            string = string.strip(',.') ; # Remove trailing characters
            experiment[key][values[0]] = string.replace(' + ',' and ')  ; # Replace +
    # Write file
    if 'mip_era' == jsonName:
        outFile = ''.join(['../',jsonName,'.json'])
    else:
        outFile = ''.join(['../CMIP6_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    fH = open(outFile,'w')
    json.dump(eval(jsonName),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

     # Validate - only necessary if files are not written by json module

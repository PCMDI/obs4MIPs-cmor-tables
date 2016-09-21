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

execfile('read_json_fcns.py')


#%% Import statements
import cmor,gc,json,os,ssl,sys,urllib2
import cdms2 as cdm
import numpy as np

#%% Set local path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1])) ; # Extract path from executing file
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/' ; # Hard code path
#homePath = '/sync/git/obs4MIPs-cmor-tables/demo' ; # Hard code path
os.chdir(homePath)


#%% SECTION 2 - Integrate Omon into master file - create obs4MIPs_Omon_composite.json
jsonOmon = 'obs4MIPs_Omon_composite.json'
jsonAmon = 'obs4MIPs_Amon.json'
buildList = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_coordinate.json'],
#['Omon','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_Omon.json'],
 ['Amon','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_Amon.json']
 ] ;

# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
    vars()[table] = tmp[table]
del(tmp,count,table) ; gc.collect()

# Rebuild
table = {}
for count,CV in enumerate(buildList):
    CVName1 = CV[0]
    if CVName1 == 'coordinate':
        table['axis_entry'] = eval(CVName1)
    else:
        keys = eval(CVName1).keys()
        for count in range(len(keys)):
            table[keys[count]] = eval(CVName1).get(keys[count])



outtable = jsonAmon

try:
  os.mkdir('obs4MIPs_CMOR_tables')
except:
  pass

outFile = 'obs4MIPs_CMOR_tables/' + outtable

# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(table,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

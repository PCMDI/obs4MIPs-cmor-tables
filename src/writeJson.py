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
PJD 18 Jul 2016     - Generate CVs and tables from CMIP6_CVs and CMIP6-cmor-tables
PJD 19 Jul 2016     - Remove activity_id - no longer in A/O/etc tables
PJD 20 Jul 2016     - Removed target_mip from required_global_attributes
PJD 20 Jul 2016     - Removed source_id
                    - TODO:

@author: durack1
"""

#%% Import statements
import gc,json,os,ssl,time,urllib2
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/'
os.chdir(homePath)

#%% urllib2 config
# Create urllib2 context to deal with lab certs
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% List target tables
masterTargets = [
 'Amon',
 'Lmon',
 'Omon',
 'SImon',
 'fx',
 'coordinate',
 'frequency',
 'grid',
 'grid_label',
 'grid_resolution',
 'institution_id',
 'mip_era',
 'product',
 'realm',
 'required_global_attributes',
 'table_id'
 ] ;

#%% Tables
tableSource = [
 ['coordinate','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_coordinate.json'],
 ['fx','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_fx.json'],
 ['grid','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_grid.json'],
 ['Amon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Amon.json'],
 ['Lmon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Lmon.json'],
 ['Omon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Omon.json'],
 ['SImon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SImon.json']
 ] ;

#%% Loop through tables and create in-memory objects
# Loop through input tables
for count,table in enumerate(tableSource):
    # Read web file
    jsonOutput                      = urllib2.urlopen(table[1], context=ctx)
    tmp                             = jsonOutput.read()
    vars()[table[0]]                = tmp
    jsonOutput.close()
    # Write local json
    tmpFile                         = open('tmp.json','w')
    tmpFile.write(eval(table[0]))
    tmpFile.close()
    # Read local json
    vars()[table[0]]    = json.load(open('tmp.json','r'))
    os.remove('tmp.json')
    del(tmp,jsonOutput)
    del(count,table) ; gc.collect()

# Cleanup by extracting only variable lists
for count2,table in enumerate(tableSource):
    tableName = table[0]
    if tableName in ['coordinate','grid']:
        continue
    else:
        eval(tableName).pop('axis_entry')
        eval(tableName)['Header'].pop('generic_levels')
        eval(tableName)['Header']['table_date'] = time.strftime('%d %B %Y')

# Cleanup realms
Amon['Header']['realm']     = 'atmos'
Lmon['Header']['realm']     = 'land'
Omon['Header']['realm']     = 'ocean'
SImon['Header']['realm']    = 'seaIce'
fx['Header']['realm']       = 'fx'

#%% Frequencies
frequency = ['3hr', '3hrClim', '6hr', 'day', 'decadal', 'fx', 'mon', 'monClim', 'subhr', 'yr'] ;

#%% Grid
# Read web file
sourceFile = 'https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_grid.json'
jsonOutput = urllib2.urlopen(sourceFile, context=ctx)
tmp = jsonOutput.read()
jsonOutput.close()
# Write local json
if os.path.exists('tmp.json'):
    os.remove('tmp.json')
tmpFile = open('tmp.json','w')
tmpFile.write(tmp)
tmpFile.close()
# Read local json
tmp = json.load(open('tmp.json','r'))
os.remove('tmp.json')
del(jsonOutput) ; gc.collect()
# Allocate grid
grid = tmp
del(tmp,sourceFile) ; gc.collect()

#%% Grid labels
grid_label = ['gn', 'gr', 'gr1', 'gr2', 'gr3', 'gr4', 'gr5', 'gr6', 'gr7', 'gr8', 'gr9'] ;

#%% Grid resolutions
grid_resolution = [
 '10 km',
 '100 km',
 '1000 km',
 '10000 km',
 '1x1 degree',
 '25 km',
 '250 km',
 '2500 km',
 '5 km',
 '50 km',
 '500 km',
 '5000 km'
 ] ;

#%% Institutions
institution_id = {
 'PCMDI': 'Program for Climate Model Diagnosis and Intercomparison, Lawrence Livermore National Laboratory, Livermore, CA 94550, USA'
 } ;

 #%% Product
mip_era = ['CMIP6'] ;

#%% Product
product = [
 'composite',
 'remote-sensed',
 'satellite',
 'surface-gridded-insitu',
 'surface-radar'
 ] ;

#%% Realms
realm = [
 'aerosol',
 'atmos',
 'atmosChem',
 'land',
 'landIce',
 'ocean',
 'ocnBgchem',
 'seaIce'
 ] ;

#%% Required global attributes
required_global_attributes = [
 'activity_id',
 'Conventions',
 'creation_date',
 'dataset_version_number',
 'further_info_url',
 'frequency',
 'grid',
 'grid_label',
 'grid_resolution',
 'institution_id',
 'license',
 'mip_era',
 'product',
 'realm',
 'source_id',
 'table_id',
 'tracking_id',
 'variable_id'
 ];

#%% Table IDs
table_id = ['Amon', 'Lmon', 'Omon', 'SImon'] ;

#%% Write variables to files
for jsonName in masterTargets:
    # Clean experiment formats
    if jsonName in ['coordinate','grid']: #,'Amon','Lmon','Omon','SImon']:
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
                    string = string.replace('decidous','deciduous') ; # Replace decidous
                    string = string.replace('  ',' ') ; # Replace '  ', '   '
                dictToClean[key][values[0]] = string
        vars()[jsonName] = dictToClean
    # Write file
    if jsonName in ['Amon','Lmon','Omon','SImon','fx']:
        outFile = ''.join(['../Tables/obs4MIPs_',jsonName,'.json'])
    else:
        outFile = ''.join(['../obs4MIPs_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    if not os.path.exists('../Tables'):
        os.mkdir('../Tables')
    fH = open(outFile,'w')
    json.dump(eval(jsonName),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

del(jsonName,outFile) ; gc.collect()

# Validate - only necessary if files are not written by json module

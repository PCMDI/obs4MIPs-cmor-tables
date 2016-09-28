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
PJD 28 Sep 2016     - Update to deal with new json (embedded key) formats
                    - TODO:

@author: durack1
"""

#%% Import statements
import cmor,gc,json,os,ssl,sys,urllib2
import cdms2 as cdm
import numpy as np

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
buildList = [
 ['frequency','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_frequency.json'],
 ['grid_label','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid_label.json'],
 ['grid_resolution','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid_resolution.json'],
 ['grid','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid.json'],
 ['institution_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_institution_id.json'],
 ['mip_era','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_mip_era.json'],
 ['product','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_product.json'],
 ['realm','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_realm.json'],
 ['required_global_attributes','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_required_global_attributes.json'],
 ['table_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_table_id.json'],
 ] ;

# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
    vars()[table] = tmp[table]
del(tmp,count,table) ; gc.collect()

# Rebuild grid_labels
grid_labels = {}
grid_labels['gs1x1'] = { "grid_resolution":"1x1 degree" }
grid_labels['gs1x1 gn'] = { "grid_resolution":"1x1 degree" }
grid_labels['gs1x1 gr'] = { "grid_resolution":"1x1 degree" }
for count,grid in enumerate(grid_label):
    if count < 2:
        grid_labels[grid] = grid_resolution
    else:
        grid_labels[grid] = {}

# Rebuild
obs4MIPs_CV = {}
obs4MIPs_CV['CV'] = {}
obs4MIPs_CV['CV']['grid_labels'] = grid_labels
for count,CV in enumerate(buildList):
    CVName1 = CV[0]
    if CVName1 in ['grid','grid_label','grid_resolution']:
        continue ; # Exclude
    if CVName1 == 'coordinate':
        CVName2 = CVName1
        CVName1 = 'axis_entry'
    elif CVName1 == 'institution_id':
        CVName2 = CVName1
        CVName1 = 'institution_ids'
    elif CVName1 == 'source_id':
        CVName2 = CVName1
        CVName1 = 'source_ids'
    else:
        CVName2 = CVName1
    obs4MIPs_CV['CV'][CVName1] = eval(CVName2)

outFile = 'obs4MIPs_CV.json'
# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()


#%% SECTION 2 - Integrate Omon into master file - create obs4MIPs_Omon_composite.json
jsonOmon = 'obs4MIPs_Omon_composite.json'
buildList = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_coordinate.json'],
 ['Omon','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_Omon.json']
 ] ;

# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
    if table == 'coordinate':
        vars()[table] = tmp[table].get(table)
    else:
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

outFile = jsonOmon
# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(table,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

# Process variable (with time axis)
cmor.setup(inpath='../Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json('drive_obs4MIPs.json') ; # Update contents of this file to set your global_attributes
f       = cdm.open('amipobs_tos_360x180_v1.1.0_187001-187112.nc')
d       = f['tos']
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'obs4MIPs_Omon_composite.json' ; # Amon,Lmon,Omon,SImon
obs4MIPsOmonID = cmor.load_table(table) ; # Load target table (above), axis info (coordinates, grid*) and CVs
axes    = [ {'table_entry': 'time',
             'units': 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat.getBounds()},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon.getBounds()},
          ]
axis_ids = list()
for axis in axes:
    axis_id = cmor.axis(**axis)
    axis_ids.append(axis_id)
varid   = cmor.variable('tos',d.units,axis_ids)
values  = np.array(d[:],np.float32)
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 ; CMOR 3.0.6+
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
f.close()
cmor.close()
# Cleanup
del(f,d,lat,lon,time) ; gc.collect()


#%% SECTION 3 - Integrate fx into master file - create obs4MIPs_fx_composite.json
jsonFx = 'obs4MIPs_fx_composite.json'
buildList = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_coordinate.json'],
 ['fx','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_fx.json']
 ] ;

# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
    if table == 'coordinate':
        vars()[table] = tmp[table].get(table)
    else:
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

table['Header']['realm'] = 'ocean' ; # Overwrite realm info

outFile = jsonFx
# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(table,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

# Process fixed field
cmor.setup(inpath='../Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json('drive_obs4MIPs.json') ; # Update contents of this file to set your global_attributes
f       = cdm.open('amipbc_areacello_360x180_v1.1.0.nc')
d       = f['areacello']
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'obs4MIPs_fx_composite.json' ; # Amon,Lmon,Omon,SImon
cmor.load_table(table)
axes    = [  {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat.getBounds()},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon.getBounds()},
          ]
axis_ids = list()
for axis in axes:
    axis_id = cmor.axis(**axis)
    axis_ids.append(axis_id)
varid   = cmor.variable('areacello',d.units,axis_ids)
values  = np.array(d[:],np.float32)
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 ; CMOR 3.0.6+
cmor.write(varid,values) ; # Write fixed variable
f.close()
cmor.close()
# Cleanup
del(outFile,f,d,lat,lon,time) ; gc.collect()

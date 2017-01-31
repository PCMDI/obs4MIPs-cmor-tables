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
PJD 30 Jan 2017     - Update to deal with new tables
PJD 31 Jan 2017     - Updated to work with CMOR 3.2.1
                    - TODO:

@author: durack1
"""

#%% Import statements
import cmor,gc,json,os
import cdms2 as cdm
import numpy as np
from durolib import readJsonCreateDict

#%% Set local path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1])) ; # Extract path from executing file
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/' ; # Linux hard code path
#homePath = '/sync/git/obs4MIPs-cmor-tables/demo' ; # OS-X hard code path
os.chdir(homePath)

#%% SECTION 1 - Integrate all controlled vocabularies (CVs) into master file - create obs4MIPs_CV.json
jsonCVs = 'obs4MIPs_CV.json'
buildList = [
 ['frequency','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_frequency.json'],
 ['grid_label','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid_label.json'],
 ['institution_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_institution_id.json'],
 ['mip_era','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_mip_era.json'],
 ['nominal_resolution','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_nominal_resolution.json'],
 ['product','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_product.json'],
 ['realm','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_realm.json'],
 ['required_global_attributes','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_required_global_attributes.json'],
 ['table_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_table_id.json'],
 ['coordinate','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_coordinate.json'],
 ['formula_terms','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_formula_terms.json']
 ] ;

# Loop through buildList and create output tables
tmp = readJsonCreateDict(buildList)
for count,table in enumerate(tmp.keys()):
    if table in ['coordinate','formula_terms']:
        vars()[table] = tmp[table]
    else:
        vars()[table] = tmp[table].get(table)
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

# Loop through dictionary and write files
for count,pair in enumerate(outFilePairs):
    if os.path.exists(outFilePairs[pair]):
        print 'File existing, purging:',outFilePairs[pair]
        os.remove(outFilePairs[pair])
    fH = open(outFilePairs[pair],'w')
    json.dump(eval(pair),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

# Cleanup
del(CVName1,buildList,coordinate,count,formula_terms,frequency,grid_label,homePath,institution_id,jsonCVs,
    mip_era,nominal_resolution,obs4MIPs_CV,outFilePairs,pair,product,realm,
    required_global_attributes,table_id)

#%% SECTION 2 - Integrate Omon into master file - create obs4MIPs_Omon_composite.json
buildList = [
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

outFile = 'obs4MIPs_Omon_composite.json'
# Check file exists
if os.path.exists(outFile):
    print 'File existing, purging:',outFile
    os.remove(outFile)
fH = open(outFile,'w')
json.dump(Omon,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

# Process variable (with time axis)
print 'starting cmor'
cmor.setup(inpath='../Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
print 'cmor.setup complete'
cmor.dataset_json('drive_obs4MIPs.json') ; # Update contents of this file to set your global_attributes
print 'cmor.dataset_json complete'
f       = cdm.open('amipobs_tos_360x180_v1.1.0_187001-187112.nc')
d       = f['tos']
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'obs4MIPs_Omon_composite.json' ; # Amon,Lmon,Omon,SImon
obs4MIPsOmonID = cmor.load_table(table) ; # Load target table (above), axis info (coordinates, grid*) and CVs
print 'cmor.load_table complete'
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
print 'cmor.variable complete'
values  = np.array(d[:],np.float32)
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 ; CMOR 3.0.6+
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
f.close()
cmor.close()
# Cleanup
del(f,d,lat,lon,time) ; gc.collect()


#%% SECTION 3 - Integrate fx into master file - create obs4MIPs_fx_composite.json
buildList = [
 ['Ofx','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Ofx.json']
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
    keys = eval(CVName1).keys()
    for count in range(len(keys)):
        table[keys[count]] = eval(CVName1).get(keys[count])

table['Header']['realm'] = 'ocean' ; # Overwrite realm info

outFile = 'obs4MIPs_Ofx_composite.json'
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
table   = 'obs4MIPs_Ofx_composite.json' ; # Amon,Lmon,Omon,SImon
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

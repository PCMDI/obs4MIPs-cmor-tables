#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 13:49:08 2016

@author: durack1
"""

import cmor,gc,json,os,ssl,urllib2
import cdms2 as cdm
import numpy as np

#%% Import statements
#homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/'
homePath = '/sync/git/obs4MIPs-cmor-tables/demo'
os.chdir(homePath)

#%% urllib2 config
# Create urllib2 context to deal with lab certs
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% Integrate all CVs into master file
jsonCVs = 'obs4MIPs_CV.json'
buildList = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_coordinate.json'],
 ['frequency','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_coordinate.json'],
 ['grid_label','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid_label.json'],
 ['grid_resolution','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid_resolution.json'],
 ['grid','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_grid.json'],
 ['institution_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_institution_id.json'],
 ['mip_era','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_mip_era.json'],
 ['product','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_product.json'],
 ['realm','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_realm.json'],
 ['required_global_attributes','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_required_global_attributes.json'],
 ['source_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_source_id.json'],
 ['table_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_table_id.json'],
 ] ;

# Loop through input tables
for count,table in enumerate(buildList):
    print 'Processing:',table[0]
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

# Rebuild
obs4MIPs_CV = {}
obs4MIPs_CV['CV'] = {}
for count,CV in enumerate(buildList):
    CVName1 = CV[0]
    if CVName1 == 'coordinate':
        CVName2 = CVName1
        CVName1 = 'axis_entry'
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

#%% Process variable (with time axis)
cmor.setup(inpath='../Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json("drive_obs4MIPs.json")
f       = cdm.open('amipobs_tos_360x180_v1.1.0_187001-187112.nc')
d       = f['tos']
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'obs4MIPs_Omon.json' ; # Amon,Lmon,Omon,SImon
cmor.load_table(table) ; # Load target table (above), axis info (coordinates, grid*) and CVs
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
cmor.write(varid,values,time_vals=time[:])
f.close()
cmor.close()
# Cleanup
del(f,d,lat,lon,time) ; gc.collect()

#%% Process fixed field
cmor.setup(inpath='CMOR/input4MIPs-cmor-tables/Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json("CMOR/drive_input4MIPs_obs.json")
f       = cdm.open(outFile)
d       = f[var.id]
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'input4MIPs.json'
cmor.load_table(table)
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
varid   = cmor.variable(var.id,var.units,axis_ids)
values  = np.array(d[:],np.float32)
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 ; CMOR 3.0.6+
#cmor.write(varid,values,time_vals=d.getTime()[:],time_bnds=d.getTime().genGenericBounds()) ; # Not valid for time
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds())
f.close()
cmor.close()
# Cleanup
del(outFile,var,f,d,lat,lon,time) ; gc.collect()
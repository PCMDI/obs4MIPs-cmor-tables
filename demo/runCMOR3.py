#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 13:49:08 2016

@author: durack1
"""

cmor.setup(inpath='CMOR/input4MIPs-cmor-tables/Tables',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json("CMOR/drive_input4MIPs_bcs.json")
f       = cdm.open(outFile)
d       = f[var.id]
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
table   = 'input4MIPs.json'
cmor.load_table(table)
axes    = [ {'table_entry': 'time2',
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
cmor.write(varid,values,time_vals=time[:])
f.close()
cmor.close()
# Cleanup
del(outFile,var,f,d,lat,lon,time) ; gc.collect()
import cmor
import cdms2 as cdm
import numpy as np

#%% Process variable (with time axis)
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


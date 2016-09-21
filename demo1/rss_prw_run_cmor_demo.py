import cmor
import cdms2 as cdm
import numpy as np
import pdb
import sys
import argparse
import MV2

inp = './obs4MIPs_CMOR_tables'
input_json = './prw_rss_mo_input.json' 
input_data_path = '/clim_obs/orig/data/RSS/rss_ssmi_pw_v06.6-demo.nc' 
input_var_name = 'prw'
cmor_table = './obs4MIPs_CMOR_tables/obs4MIPs_Amon.json' 
output_units = 'kg m-2'
output_var_name = 'prw'

### BETTER IF THE USER DOES NOT HAVE TO CHANGE ANYTHING BELOW THIS LINE... 
 
#%% Process variable (with time axis)
cmor.setup(inpath=inp,netcdf_file_action=cmor.CMOR_REPLACE_4)
#cmor.dataset_json('./drive_obs4MIPs.json') ; # Update contents of this file to set your global_attributes
cmor.dataset_json(input_json) ; # Update contents of this file to set your global_attributes

f       = cdm.open(input_data_path)
d       = f(input_var_name)
lat     = d.getLatitude()
lon     = d.getLongitude()
time    = d.getTime()
time   = d.getAxis(0)
time.axis = 'T'

#cmor.set_cur_dataset_attribute('history',f.history) ; # Force local file attribute as history
#table   = '../obs4MIPs_Omon_composite.json' ; # Amon,Lmon,Omon,SImon
table   = cmor_table ; # Amon,Lmon,Omon,SImon

obs4MIPsAmonID = cmor.load_table(table) ; # Load target table (above), axis info (coordinates, grid*) and CVs
axes    = [ {'table_entry': 'time',
             'units': time.units,   #'days since 1870-01-01',
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

#pdb.set_trace()

d.units = output_units 
varid   = cmor.variable(output_var_name,d.units,axis_ids,missing_value=d.missing)
values  = np.array(d[:],np.float32)
cdm.setAutoBounds('on')   # PJG  CAUTION WITH THIS ONE! 

cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 ; CMOR 3.0.6+
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
f.close()
cmor.close()


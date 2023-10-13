import cmor
import xcdat as xc
import xarray as xr
import numpy as np
import json

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'GPCP_NCEI_v02r03.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '~/files-obs4MIPs/NCEI/GPCP/gpcp_v02r03_monthly_d201801_c20180409.nc'    # change to location on user's machine
inputVarName = 'precip'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file
f = xr.open_dataset(inputFilePath, decode_times=False, decode_cf=False)
d = f[inputVarName]

lat = f.latitude
lon = f.longitude
time = f.time
time_bounds = f.time_bounds
lon_bounds = f.lon_bounds
lat_bounds = f.lat_bounds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f.history) 
axes    = [ {'table_entry': 'time',
             'units': time.units,
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat.values,
              'cell_bounds': lat_bounds.values},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon.values,
              'cell_bounds': lon_bounds.values},
          ]
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=d.missing_value)
values  = np.array(d.values,np.float32)
values  = values/86400. # NCEI GPCP array is in units of mm/day. Must be converted to kg m-2 s-1


# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',d.valid_range[0]/86400)   
cmor.set_variable_attribute(varid,'valid_max','f',d.valid_range[-1]/86400)


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
f.close()
cmor.close()

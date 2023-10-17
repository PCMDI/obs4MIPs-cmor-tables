import cmor
import xcdat as xc
import xarray as xr
import numpy as np
import json


#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'RSS_PRW_v07r02.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'tpw_v07r02_198801_202212.nc4.nc'    # change to location on user's machine
inputVarName = 'precipitable_water'
outputVarName = 'prw'
outputUnits = 'kg m-2'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file
f = xr.open_dataset(inputFilePath, decode_times=False, decode_cf=False) # two 'time' variables in file. Must use xarray
d = f[inputVarName]

lat = f.latitude
lon = f.longitude
time = f.time
time_bounds = f.time_bounds
lon_bounds = f.longitude_bounds
lat_bounds = f.latitude_bounds

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
varid   = cmor.variable(outputVarName,d.units,axisIds,missing_value=d._FillValue)
values  = np.array(d.values,np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',float(d.valid_min))   # d.valid_min is np.float32, which cmor does not like. Must convert to 'float'
cmor.set_variable_attribute(varid,'valid_max','f',float(d.valid_max))   # d.valid_max is np.float32, which cmor does not like. Must convert to 'float'

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
f.close()
cmor.close()

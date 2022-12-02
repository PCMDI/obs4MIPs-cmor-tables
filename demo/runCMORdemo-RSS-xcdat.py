import cmor
import cdms2 as cdm
import numpy as np
import xcdat as xc
import xarray as xr
import json

#%% User provided input
cmorTable = '../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'RSS_prw_v07r01.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/home/gleckler1/tpw_v07r01_198801_202112.nc4.nc'
inputVarName = 'precipitable_water'
outputVarName = 'prw'
outputUnits = 'kg m-2'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file
#f = cdm.open(inputFilePath)
#d = f(inputVarName)
#lat = d.getLatitude()
#lon = d.getLongitude()
#time = d.getAxis(0) ; # Rather use a file dimension-based load statement

f = xr.open_dataset(inputFilePath)

f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds
d = f[inputVarName]

time = f.time.values
lat = f.latitude.values
lon = f.longitude.values
time_bounds = f.time_bounds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f.history)  
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
axes    = [ {'table_entry': 'time',
             'units': time.units, # 'days since 1870-01-01',
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
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
d.units = outputUnits
varid   = cmor.variable(outputVarName,d.units,axisIds,missing_value=d.missing)
values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
f.close()
cmor.close()

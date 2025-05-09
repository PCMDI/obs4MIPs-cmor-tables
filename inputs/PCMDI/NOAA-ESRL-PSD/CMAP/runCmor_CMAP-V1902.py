import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import numpy.ma as ma
import json
import sys

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CMAP-V1902-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/'
inputFilePathend = 'NOAA-ESRL-PSD/CMAP/'
inputFileName = 'precip.mon.mean.nc'
inputFilePath = inputFilePathbgn + inputFilePathend + inputFileName
inputVarName = 'precip'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
f = xr.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values
lon = f.lon.values
time = f.time.values ; # Rather use a file dimension-based load statement
f = f.bounds.add_bounds("X")
f = f.bounds.add_bounds("Y")
f = f.bounds.add_bounds("T")
# CONVERT UNITS FROM mm/day to kg/m2/s 
d = np.divide(d,86400.)
d = np.where(np.isnan(d),ma.masked,d)

#w = sys.stdin.readline()


#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f.history)

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
axes    = [ {'table_entry': 'time',
             'units': f.time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': f.lat_bnds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': f.lon_bnds},
          ]
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#d['units'] = outputUnits
varid   = cmor.variable(outputVarName,outputUnits, axisIds, missing_value=1.e20)
values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
print('ABOVE WRITE')
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time[:],time_bnds= f.time_bnds.values)  #time.getBounds()) ; # Write variable with time axis
print('BELOW WRITE')
f.close()

cmor.close()

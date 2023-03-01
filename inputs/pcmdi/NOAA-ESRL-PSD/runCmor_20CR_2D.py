import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = '20CR-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = 'NOAA-ESRL-PSD/20CR/'
inputFileName = ['slp_monthly/prmsl.mon.mean.nc','air_temperature_monthly/air.sfc.mon.mean.nc']
inputVarName = ['prmsl','air']
outputVarName = ['psl','ts']
outputUnits = ['Pa','K']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file

  f = xr.open_dataset(inputFilePath+inputFileName[fi],decode_times=False)
  d = f[inputVarName[fi]]
  lat = f.lat.values
  lon = f.lon.values
  time = f.time.values ; # Rather use a file dimension-based load statement
  f = f.bounds.add_bounds("X")
  f = f.bounds.add_bounds("Y")
  f = f.bounds.add_bounds("T")
  print(d.shape)

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units':'hours since 1800-1-1 00:00:0.0' # 'days since 1979-01-01', #time.units, # 'days since 1870-01-01',
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

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
# d.units = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],outputUnits[fi],axisIds,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
  f.close()

  cmor.close()

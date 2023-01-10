import cmor
import xarray as xr
import xcdat as xc
import numpy as np

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CERES4.0-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/CERES_SURFACE/'
inputFileName = 'CERES_EBAF-Surface_Ed4.0_Subset_200003-201803.nc' 
inputVarName = ['sfc_lw_up_all_mon','sfc_sw_up_all_mon','sfc_sw_up_clr_mon','sfc_sw_down_all_mon','sfc_sw_down_clr_mon']
outputVarName = ['rlus','rsus','rsuscs','rsds','rsdscs']
outputUnits = ['W m-2','W m-2','W m-2','W m-2','W m-2']
outpos = ['up','up','up','down','down']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = xr.open_dataset(inputFilePath+inputFileName,decode_times=False)
  d = f[inputVarName[fi]]
  darr = f[inputVarName[fi]].values
  lat = f.lat.values
  lon = f.lon.values
  time = f.time.values
  d['positive']= outpos[fi]
  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")  #, width=0.5)
  f = f.bounds.add_bounds("T")
  d['positive'] = outpos[fi]

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
  d['units'] = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],outputUnits[fi],axisIds,missing_value=1.e20,positive=outpos[fi])
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
  f.close()

  cmor.close()

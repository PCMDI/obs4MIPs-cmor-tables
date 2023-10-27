import cmor
import xcdat as xc
import numpy as np

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CERES4.2-input.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/NASA-LaRC/CERES_EBAF4.2/'

inputFileName = 'CERES_EBAF_Ed4.2_Subset_200003-202306.nc' 
inputVarName = ['sfc_lw_up_all_mon','sfc_sw_up_all_mon','sfc_sw_up_clr_c_mon','sfc_lw_down_all_mon','sfc_lw_down_clr_c_mon','sfc_sw_down_all_mon','sfc_sw_down_clr_c_mon'] #,'sfc_cre_net_sw_mon','sfc_cre_net_lw_mon','sfc_cre_net_tot_mon']
outputVarName = ['rlus','rsus','rsuscs','rlds','rldscs','rsds','rsdscs'] #,'rsscre','rlscre','rnscre']
outputUnits = ['W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2']
outpos = ['up','up','up','down','down','down','down','down','down','down']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):

  print(fi, inputVarName[fi])
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = xc.open_dataset(inputFilePath+inputFileName, decode_times=False, decode_cf=False) # both need to be set to get time units and missing value data
  d = f[inputVarName[fi]]

  # Added for xCDAT 0.6.0 to include time bounds.
  f = f.bounds.add_bounds("T")

  lat = f.lat
  lon = f.lon
  time = f.time
  time_bounds = f.time_bnds
  lon_bounds = f.lon_bnds
  lat_bounds = f.lat_bnds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units': time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat.values,
              'cell_bounds': lat_bounds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon.values,
              'cell_bounds': lon_bounds},
          ]
  axisIds = list() ; # Create list of axes
  for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName[fi],d.units,axisIds,missing_value=d._FillValue,positive=outpos[fi])
  values  = np.array(d.values,np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_variable_attribute(varid,'valid_min','c',d.valid_min) # CERES defines this as a string in the EBAF netCDF4 files.  Must be saved as such
  cmor.set_variable_attribute(varid,'valid_max','c',d.valid_max)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
  f.close()

  cmor.close()


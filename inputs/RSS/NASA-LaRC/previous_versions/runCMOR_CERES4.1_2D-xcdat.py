import cmor
import cdms2 as cdm
import xcdat as xc
import numpy as np

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CERES4.1-input.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/home/rss_user/files-obs4MIPs/NASA-LaRC/CERES-EBAF-TOA/'
inputFilePath = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/CERES_EBAF4.1/'

inputFileName = 'CERES_EBAF-TOA_Ed4.1_Subset_200003-202203.nc'
inputVarName = ['toa_lw_all_mon','toa_sw_all_mon','toa_sw_clr_c_mon','toa_lw_clr_c_mon','toa_net_all_mon','solar_mon','toa_cre_lw_mon','toa_cre_sw_mon']
outputVarName = ['rlut','rsut','rsutcs','rlutcs','rt','rsdt','rltcre','rstcre']
outputUnits = ['W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2']
outpos = ['up','up','up','up','','down','up','up']


### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):

  inputFileName = 'CERES_EBAF-TOA_Ed4.1_Subset_200003-201905.nc' 
  if inputVarName[fi] in ['toa_cre_lw_mon','toa_cre_sw_mon']: inputFileName = 'CERES_EBAF_Ed4.1_Subset_200003-202203-CRE.nc'

  print(fi, inputVarName[fi])
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = xc.open_dataset(inputFilePath+inputFileName, decode_times=False, decode_cf=False) # both need to be set to get time units and missing value data
  d = f[inputVarName[fi]]

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


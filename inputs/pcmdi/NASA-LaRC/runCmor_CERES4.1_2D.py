import cmor
import xarray as xr
import xcdat as xc
import numpy as np

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = './CERES4.1-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/CERES_EBAF4.1/TOA_separatefile/'

inputFileName = 'CERES_EBAF-TOA_Ed4.1_Subset_200003-201906.nc'
inputVarName = ['toa_lw_all_mon','toa_sw_all_mon','toa_sw_clr_c_mon','toa_lw_clr_c_mon','toa_net_all_mon','solar_mon','toa_cre_lw_mon','toa_cre_sw_mon']
outputVarName = ['rlut','rsut','rsutcs','rlutcs','rt','rsdt','rltcre','rstcre']
outputUnits = ['W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2','W m-2']
outpos = ['up','up','up','up','','down','up','up']

#inputVarName = ['toa_cre_lw_mon']
#outputVarName = ['rltcre']
#outputUnits = ['W m-2']
#outpos = ['up']

for fi in range(len(inputVarName)):
  inputFileName = 'CERES_EBAF-TOA_Ed4.1_Subset_200003-201906.nc' 
  if inputVarName[fi] in ['toa_cre_lw_mon','toa_cre_sw_mon']: inputFileName = 'CERES_EBAF_Ed4.1_Subset_200003-201905-CRE.nc'

  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
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

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d['units'] = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],outputUnits[fi],axisIds,missing_value=1.e20,positive=outpos[fi])
  values  = f[inputVarName[fi]].values   #np.array(d[:],np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,darr,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
  f.close()
  cmor.close()

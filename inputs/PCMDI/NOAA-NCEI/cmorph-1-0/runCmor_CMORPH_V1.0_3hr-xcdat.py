import cmor
import xcdat 
import xarray as xr
import glob
import numpy as np
import sys, glob

#%% User provided input

targetgrid = 'orig'
#targetgrid = '2deg'

cmorTable = '../../../../Tables/obs4MIPs_A3hr.json' 

if targetgrid == 'orig':
  inputJson = 'CMORPH_V1.0_3hr-input.json' ; 
  subdir = '3hr.center/'

if targetgrid == '2deg':
  inputJson = 'CMORPH_V1.0_3hr-input-250km.json' ;
  subdir = '3hr.center_2deg/'

inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/'
inputFilePathend = '/NOAA-NCEI/CMOPRH_mahn_v20210719/CMORPH_v1.0/' + subdir

#lstall = glob.glob(inputFilePathbgn+inputFilePathend + '*2002*.nc')
lstall = glob.glob(inputFilePathbgn+inputFilePathend + '*.nc')

#lstall = [inputFilePathbgn+inputFilePathend + 'CMORPH_v1.0_0.25deg_3hr_200201.nc']

print(len(lstall),' ', lstall)
#w = sys.stdin.readline()

inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#for fi in range(len(inputVarName)):
for fi in lstall:
  print(fi)
# f = cdm.open(inputFilePath+inputFileName[fi])
  f = xr.open_dataset(fi,decode_times=False)
  d = f[inputVarName]
  d = np.divide(d,3600.)

  lat = f.latitude.values  #f.getLatitude()
  lon = f.longitude.values  #d.getLongitude()
  time = f.time.values   #d.get

  if targetgrid == 'orig': f = f.drop_vars(["lat_bounds","lon_bounds"])
  if targetgrid == '2deg': f = f.drop_vars(["bounds_latitude","bounds_longitude"])

  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")  
  f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
#####del(time_bounds) ; # Cleanup

# print('above cmor')
#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units': f.time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': f.latitude_bnds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': f.longitude_bnds},
          ]
  axisIds = list() ; # Create list of axes
  for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# print('above cmor.write')
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
  cmor.close()
  f.close()
  print('done cmorizing ', fi)

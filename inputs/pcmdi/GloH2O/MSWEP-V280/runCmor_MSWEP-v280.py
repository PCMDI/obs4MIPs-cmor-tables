import cmor
import xcdat as xc 
import xarray as xr
import glob
import numpy as np
import sys, glob

#%% User provided input

targetgrid = 'orig'
#targetgrid = '2deg'

freq = 'Aday'  #'Amon'
opt = 'Past'

if freq == 'Amon': 
  cmorTable = '../../../../Tables/obs4MIPs_Amon.json' 
  avgp = 'Monthly'
if freq == 'Aday':
  cmorTable = '../../../../Tables/obs4MIPs_Aday.json'
  avgp = 'Daily'



if targetgrid == 'orig':
  inputJson = 'MSWEP-v280-input.json' ; 
subdir = opt + '/' + avgp + '/'

if targetgrid == '2deg':
  inputJson = 'MSWEP-v280-input.json' ;

inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' 
inputFilePathend = subdir

lsttmp = glob.glob(inputFilePathbgn+inputFilePathend + '*.nc')  # TRAP ALL FILES
lsttmp.sort()

lstyrs = []  # TRAP ALL YEARS
for i in lsttmp:
  stryr = i.split(avgp+'/')[1].split('.nc')[0][0:4]
  if stryr not in lstyrs:lstyrs.append(stryr)
lstyrs.sort()
 
#w = sys.stdin.readline()

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds


inputVarName = 'precipitation'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

for yr in lstyrs[3:4]:
  print('yr is', yr)
  tmp = inputFilePathbgn+inputFilePathend + '*' + yr + '*.nc'
  print(tmp)
  lstall = glob.glob(inputFilePathbgn+inputFilePathend + '*' + yr + '*.nc')
  lstall.sort()
  print('len of lstall', len(lstall))
#  w = sys.stdin.readline()

# f = xr.open_mfdataset(lstall[0:30],mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
  f = xc.open_mfdataset(lstall[0:30],add_bounds=True)

  d = f[inputVarName]
  d = np.divide(d,3600.)
  print('d read')
  time = f.time
  lat = f.lat
  lon = f.lon   #.values

  time['axis'] = "T"
  lat['axis'] = "Y"
  lon['axis'] = "X"

  time["units"] = "days since 1900-1-1 00:00:00"
  tunits = "days since 1900-1-1 00:00:00"


  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")  
  f = f.bounds.add_bounds("T")

  print('above cmor', yr)
# w = sys.stdin.readline()
#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= 'cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units': tunits, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat.values,
              'cell_bounds': f.lat_bnds.values},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon.values,
              'cell_bounds': f.lon_bnds.values},
          ]
  axisIds = list() ; # Create list of axes
  for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)


  print('above varid')
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=1.e20)
  values  = np.array(d[:],np.float32)
  print('below values')

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

  print('above cmor.write')
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time.values,time_bnds=f.time_bnds.values) ; # Write variable with time axis
  cmor.close()
  f.close()
  print('done cmorizing ', yr)

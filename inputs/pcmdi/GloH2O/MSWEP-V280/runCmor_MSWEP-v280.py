import cmor
import xcdat 
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


#if freq == 'day': cmorTable = '../../../../Tables/obs4MIPs_Aday.json'
#if freq == '3hr': cmorTable = '../../../../Tables/obs4MIPs_A3hr.json'




if targetgrid == 'orig':
  inputJson = 'MSWEP-v280-input.json' ; 
subdir = opt + '/' + avgp + '/'

if targetgrid == '2deg':
  inputJson = 'MSWEP-v280-input.json' ;

inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' 
inputFilePathend = subdir

#lstall = glob.glob(inputFilePathbgn+inputFilePathend + '*2002*.nc')
lstall = glob.glob(inputFilePathbgn+inputFilePathend + '2017*.nc')


def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds


print(len(lstall),' ', lstall)
#w = sys.stdin.readline()

inputVarName = 'precipitation'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#for fi in range(len(inputVarName)):
#for fi in lstall:
for a in [1]:
# f = cdm.open(inputFilePath+inputFileName[fi])
  f = xr.open_mfdataset(lstall,mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
  d = f[inputVarName]
  d = np.divide(d,3600.)
  print('d read')
  time = f.time
  lat = f.lat  #.values
  lon = f.lon  #.values

  time['axis'] = "T"
  lat['axis'] = "Y"
  lon['axis'] = "X"

  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")  
  f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
#####del(time_bounds) ; # Cleanup

  print('above cmor')
  w = sys.stdin.readline()
#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= 'cmorLog.txt')
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


  print('above varid')
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=1.e20)
  values  = np.array(d[:],np.float32)
  print('below values')

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

import cmor
import xcdat as xc
import numpy as np
import numpy.ma as ma
import json
import sys
import glob
from calendar import monthrange

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

def dom(yr,mo):
  if mo in ['01','03','05','07','08','10','12']: endofMoDay = '31' 
  if mo in ['04','06','09','11']: endofMoDay = '30'
  if mo == '02': endofMoDay = '28'
  if mo == '02' and yr in ['1980','1984', '1988', '1992', '1996', '2000','2004', '2008', '2012', '2016', '2020']: endofMoDay = '29'
  return endofMoDay


#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'livneh_NOAA-PSL_inputs.json' ; # Update contents of this file to set your global_attributes
inputDatasets = '/p/user_pub/PCMDIobs/obs4MIPs_input/NOAA-ESRL-PSD/Livney_monthly/*.mean.nc'
inputVarName = 'PPT'
#outputVarName = 'pr'
#outputUnits = 'kg m-2 s-1'

lst = glob.glob(inputDatasets)

print('Number of files ', len(lst))
#w = sys.stdin.readline()

# Opening and concatenating files from the dataset
# Due to the way the data are stored + how CMOR outputs data, it is helpful to set 'mask_and_scale' to 'True' here

for varFile in lst:

 inputVarName  = varFile.split('.mon.mean.nc')[0].split('/')
 inputVarName = inputVarName[len(inputVarName)-1]

 print('working on', inputVarName)

 f = xc.open_dataset(varFile, mask_and_scale=True, decode_times=True)
 f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds

 g = xc.open_dataset(varFile, mask_and_scale=True, decode_times=False)
 time_units = g.time.units
 time_bounds_values = np.array(g.time_bnds,np.float64)
 time_values = np.array(g.time,np.float64) 

 d = f[inputVarName]

 time = f.time
 lat = f.lat.values
 lon = f.lon.values

 lat_bounds = f.lat_bnds
 lon_bounds = f.lon_bnds
#time_bounds = f.time_bnds

 if inputVarName == 'prec':
   outputVarName = 'pr'
   outputUnits = 'kg m-2 s-1'

   for t in range(d.shape[0]-1):
       ds = f['prec'].isel(time=slice(t,t+1))
       year = ds.time.values.tolist()[0].year
       month = ds.time.values.tolist()[0].month
       num_days = monthrange(year, month)[1]
#      print('num days', num_days)
       conv = 3600.*24.*float(num_days) 
       d[t] = np.divide(d[t],conv)
     
   
 if inputVarName == 'tmax':
   outputVarName = 'tasmax'
   outputUnits = 'K'

 if inputVarName == 'tmin':
   outputVarName = 'tasmin'
   outputUnits = 'K'

 if inputVarName == 'TMEAN':
   outputVarName = 'tas'
   outputUnits = 'K'

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
 cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
 cmor.dataset_json(inputJson)
 cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history)
 axes    = [ {'table_entry': 'time',
             'units': time_units,
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat_bounds.values},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon_bounds.values},
          ]

 axisIds = list() ; # Create list of axes
 for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 d["units"] = outputUnits
 varid   = cmor.variable(outputVarName,str(d.units.values),axisIds,missing_value=-9999.)
 d = np.where(np.isnan(d),ma.masked,d)
 values  = np.array(d[:],np.float32)

# Since 'analysed_sst' is stored as a 'short' integer array in these data files,
# it is easiest to 'mask_and_scale' the data (as we do in 'xc.open_dataset' above)
# and apply the conversion to degrees Celsius and set the missing data values here.
 values  = values 
#values[np.isnan(values)] = -9999.

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_variable_attribute(varid,'valid_min','f',-1.8) # set manually for the time being
 cmor.set_variable_attribute(varid,'valid_max','f',45.)


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid,values,time_vals=time_values[:],time_bnds=time_bounds_values[:]) ; # Write variable with time axis
 f.close()
 cmor.close()
#sys.exit()
 print('done processing ', varFile)

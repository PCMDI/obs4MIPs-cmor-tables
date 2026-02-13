

import xarray as xr
import xcdat
import numpy as np
import datetime,cftime
import cmor
import glob
import pandas as pd
import os

#Input files
input_dir = '/mnt/c/Users/venalaip/OneDrive - Ilmatieteen laitos/Documents/MATLAB/CCI_SWE_datasets/NetCDF/snow_cci_v4/'
input_path = input_dir+'*.nc'

#User provided input
cmorTable = '../../Tables/obs4MIPs_Aday.json' 
inputJson = 'CCI-SWE-v4-0.json' # File to set global attributes

inputVarName = 'swe'
outputVarName = 'sweLut'
outputUnits = 'm'

#get filelist
filelist = glob.glob(input_path)
print('Number of files to process:',len(filelist))

#Open one file to get lat/lon values
ds_i = xcdat.open_dataset(filelist[0])

latitude_units = ds_i['lat'].units
latitude_values = ds_i['lat'].values 
latitude_bounds  = ds_i['lat_bnds'].values.copy()
latitude_bounds  = np.round(latitude_bounds, 5)

longitude_units = ds_i['lon'].units
longitude_values = ds_i['lon'].values
longitude_bounds = ds_i['lon_bnds'].values.copy()
longitude_bounds = np.round(longitude_bounds, 5)

nlat = latitude_values.size
nlon = longitude_values.size

# Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)#,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
axes    = [ {'table_entry': 'time',
             'units': 'days since 1950-01-01 00:00:00', 
             },
             {'table_entry': 'latitude',
              'units': latitude_units,
              'coord_vals': latitude_values,
              'cell_bounds': latitude_bounds},
             {'table_entry': 'longitude',
              'units': longitude_units,
              'coord_vals': longitude_values,
              'cell_bounds': longitude_bounds},
            ]       

axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

# # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
missing = -9999.0   
varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=missing)

# #prepare variable for writing
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data

# Base time for time coordinate
base_time = cftime.DatetimeGregorian(1950, 1, 1, 0, 0, 0)

#Build full date range for checking
dates = pd.date_range(
    start="1979-01-01",
    end="2023-12-31",
    freq="D"
)

#Create a map of date to file name
file_map = {}
for f in filelist:
    fname = os.path.basename(f)
    date_str = fname.split("-")[0] 
    file_map[pd.to_datetime(date_str)] = f

#Go through all dates
for date in dates:

    if date in file_map:
        ds = xcdat.open_dataset(file_map[date])
    
        # Extract swe variable
        values = ds['swe'].values.astype('float32')
        values[values < 0] = missing      # flags to NaN
        values[values > 0] /= 1000.0     # mm → m

        ds.close()
    else:
        # Missing days → NaNs
        values = np.full(
            (nlat, nlon),
            missing,
            dtype="float32"
        )
   
   # Numeric time (hours since 1950)
    cf_date = cftime.DatetimeGregorian(
    date.year, date.month, date.day, 0, 0, 0
    )
    coord_val = np.array([
        (cf_date - base_time).total_seconds() / 86400.0 
    ], dtype="float64")
    
   # Time bounds if present
    time_bnds = np.array([[coord_val[0]-0.5, coord_val[0]+0.5]])

    # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.write(varid,values,time_vals=coord_val,time_bnds=time_bnds)  # Write variable with time axis


#close file
cmor.close()

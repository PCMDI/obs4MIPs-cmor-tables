"""
    This code was written to show users how they can take multiple gridded data netCDF4 files
    with only one associated time stamp and concatenate them in order to make them readable by CMOR
    and, thus, output them as a singular obs4MIPs compliant dataset.  For this example, monthly
    Remote Sensing Systems (RSS) SMAP sea surface salinity (SSS) data are used.
    Written by AManaster - November 2022
""" 

import cmor
import xcdat as xc
import numpy as np
import json
import sys

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'RSS_smap_v05r01.json' ; # Update contents of this file to set your global_attributes
inputDatasets = '/mnt/athena/public/ftp/smap/SSS/V05.0/FINAL/L3/monthly/2018/*.nc' # change to local path on user's machine where files are stored
inputVarName = 'sss_smap'
outputVarName = 'sos'
outputUnits = '0.001'


# Opening and concatenating files from the dataset
f = xc.open_mfdataset(inputDatasets, mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')

f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds
d = f[inputVarName]

time = f.time
lat = f.lat.values
lon = f.lon.values

lat_bounds = f.lat_bnds
lon_bounds = f.lon_bnds
time_bounds = f.time_bnds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f.history)
axes    = [ {'table_entry': 'time',
             'units': time.units,
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat_bounds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon_bounds},
          ]

axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
d["units"] = outputUnits
varid   = cmor.variable(outputVarName,str(d.units.values),axisIds,missing_value=d._FillValue)
values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',15.0)
cmor.set_variable_attribute(varid,'valid_max','f',45.0)


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values[:],time_bnds=time_bounds.values[:]) ; # Write variable with time axis
f.close()
cmor.close()
sys.exit()

import cmor
import xcdat as xc
import xarray as xr
import numpy as np
import datetime as dt
import json
import sys

#cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'RSS_tmt_v04r01.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/mnt/sagan/g/obs4MIPs/msu_data/RSS_Tb_Maps_ch_TMT_V4_0.nc'    # change to location on user's machine
inputVarName = 'brightness_temperature'
outputVarName = 'tmt'
outputUnits = 'K'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file
f = xc.open_dataset(inputFilePath, decode_times=False, decode_cf=False)

# Ran into an issue where the first value of the "months" variable (in units of months since 1978-1-1 0:0:0)
# was equal to zero.  This created an issue where the bounds were negative.
# The following few lines put the time relative to Epoch (i.e., 1970-01-01 00:00:00
dataset_time = f["months"].values

tunits = f["months"].units.split()
tstart = tunits[2]
dataset_dt = dt.datetime.strptime(f"{tstart}", "%Y-%m-%d")
epoch_dt = dt.datetime(1970,1,1)

months_since_epoch = (dataset_dt.year - epoch_dt.year)*12 + (dataset_dt.month - epoch_dt.month)

dataset_units = f"months since {epoch_dt.strftime('%Y-%m-%d %H:%M:%S')}"

f["months"] = dataset_time + months_since_epoch
f["months"].attrs = {"units": dataset_units}

f = f.rename(name_dict={"months":"time"}) # need to rename "months" to "time" in order to create time bounds


f = f.bounds.add_missing_bounds()
d = f[inputVarName]

# Temperature units were listed as'degrees K', which CMOR misinterpreted, leading to incorrect output
# changing to 'K' here
d.attrs = {"units": "K", "_FillValue":-9999.}


lat = f.latitude
lon = f.longitude
time = f.time
time_bounds = f.time_bnds
lon_bounds = f.longitude_bounds
lat_bounds = f.latitude_bounds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
# cmor.set_cur_dataset_attribute('history',f.history) 
axes    = [ {'table_entry': 'time',
             'units': time.units,
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat.values,
              'cell_bounds': lat_bounds.values},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon.values,
              'cell_bounds': lon_bounds.values},
          ]
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,d.units,axisIds,missing_value=d._FillValue)
values  = np.array(d.values,np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',0.0)
cmor.set_variable_attribute(varid,'valid_max','f',300.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
f.close()
cmor.close()

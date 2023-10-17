
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
cmorTable = '../../../Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'MUR25-v4.2.json' ; # Update contents of this file to set your global_attributes
inputDatasets = '~/files-obs4MIPs/NASA-JPL/GHRSST/MUR-025/*.nc' # change to local path on user's machine where files are stored
inputVarName = 'analysed_sst'
outputVarName = 'tos'
outputUnits = 'degC'

# Opening and concatenating files from the dataset
# Due to the way the data are stored + how CMOR outputs data, it is helpful to set 'mask_and_scale' to 'True' here
f = xc.open_mfdataset(inputDatasets, mask_and_scale=True, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')

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
varid   = cmor.variable(outputVarName,str(d.units.values),axisIds,missing_value=-9999.)
values  = np.array(d[:],np.float32)

# Since 'analysed_sst' is stored as a 'short' integer array in these data files,
# it is easiest to 'mask_and_scale' the data (as we do in 'xc.open_dataset' above)
# and apply the conversion to degrees Celsius and set the missing data values here.
values  = values - 273.15
values[np.isnan(values)] = -9999.

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',-1.8) # set manually for the time being
cmor.set_variable_attribute(varid,'valid_max','f',45.)


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values[:],time_bnds=time_bounds.values[:]) ; # Write variable with time axis
f.close()
cmor.close()
sys.exit()

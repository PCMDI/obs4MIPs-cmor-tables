
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
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'IMERG-v06B-FINAL.json' ; # Update contents of this file to set your global_attributes
inputDatasets = '/mnt/sagan/g/ACCESS/output_files/_temp/imerg/12/*.RT-H5' # change to local path on user's machine where files are stored.  This code will work for HDF5 or RT-H5
inputVarName = 'precipitationCal'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'


# Opening and concatenating files from the dataset
f = xc.open_mfdataset(inputDatasets, group='Grid', mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date)

f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds
d = f[inputVarName]
d = d.transpose('time','lat','lon') # need to transpose the IMEG latitudes and longitudes


time = f.time
lat = f.lat.values
lon = f.lon.values


# Due to CMOR warnings related to the way latitudes and longitudes are read in/rounded
# need to round lat and lon bounds to 3 places after the decimal
lat_bounds = np.around(f.lat_bnds, 3)
lon_bounds = np.around(f.lon_bnds, 3)
time_bounds = f.time_bnds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
# cmor.set_cur_dataset_attribute('history',f.history) # commented.  Does not appear that there is a 'history' attribute for the read-in files
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
values  = np.array(d[:],np.float32)/3600. # IMERG data are in units of mm/hr. Converting to kg m-2 s-1 assuming density of water=1000 kg/m^3

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',0.0)
cmor.set_variable_attribute(varid,'valid_max','f',100.0/3600.) # setting these manually for the time being.


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time.values[:],time_bnds=time_bounds.values[:]) ; # Write variable with time axis
f.close()
cmor.close()
sys.exit()

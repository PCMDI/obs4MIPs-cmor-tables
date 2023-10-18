import cmor
import xcdat as xc
import numpy as np
import json
import sys
import glob

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
inputJson = 'livneh-unsplit_UCSD-SIO_inputs.json' ; # Update contents of this file to set your global_attributes
inputDatasets = '/p/user_pub/PCMDIobs/obs4MIPs_input/UCSD-SIO/nonsplit_precip/processed_monthly/Livneh_Unsplit_monthly_*1981-2005.nc' 
#outputVarName = 'pr'
#outputUnits = 'kg m-2 s-1'

lst = glob.glob(inputDatasets)
lst.sort()

print('Number of files ', len(lst))
#w = sys.stdin.readline()

# Opening and concatenating files from the datasnet
# Due to the way the data are stored + how CMOR outputs data, it is helpful to set 'mask_and_scale' to 'True' here

for varFile in lst:

 inputVarName  = varFile.split('Livneh_Unsplit')[1].split('_')[2] 

 print('working on', inputVarName)

#w = sys.stdin.readline()

 f = xc.open_mfdataset(varFile, mask_and_scale=True, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
 f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds

 d = f[inputVarName]
 time = f.time
 lat = f.lat.values
 lon = f.lon.values

 w = sys.stdin.readline()


 lat_bounds = f.lat_bnds[0]
 lon_bounds = f.lon_bnds[0]
 time_bounds = f.time_bnds

 if inputVarName == 'PRCP':
   outputVarName = 'pr'
   outputUnits = 'kg m-2 s-1'
   
 if inputVarName == 'Tmax':
   outputVarName = 'tasmax'
   outputUnits = 'K'

 if inputVarName == 'Tmin':
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
             'units': time.units,
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
#f["PRCP"].units = outputUnits
 varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=-9999.)
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
 cmor.write(varid,values,time_vals=time.values[:],time_bnds=time_bounds.values[:]) ; # Write variable with time axis
 f.close()
 cmor.close()
#sys.exit()
 print('done processing ', varFile)

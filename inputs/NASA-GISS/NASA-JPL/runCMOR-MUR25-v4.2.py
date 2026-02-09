
import cmor
import xcdat as xc
import numpy as np
import glob
import json
import sys
import cftime
import os

sys.path.append("../../../inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Oday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'MUR25-v4.2.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/NASA-JPL/MUR25-4-2' # change to local path on user's machine where files are stored
inputVarName = 'analysed_sst'
outputVarName = 'tos'
outputUnits = 'degC'
cmor_missing = np.float32(1.0e20)

for year in range(2002, 2027):  # put the years you want to process here
    for month in range(1,13):
        inputDatasets = []
        inputFiles = glob.glob(f"{inputFilePath}/{year}{month:02}??090000-JPL-L4_GHRSST-SSTfnd-MUR25-GLOB-v02.0-fv04.2.nc")
        inputFiles.sort() # to ensure data files are in chronological order. Code will break otherwise

        for inputFile in inputFiles:
            inputDatasets.append(inputFile)

        if len(inputDatasets) == 0:
            print(f'No data for {year}-{month:02}')
            continue
#       print(inputDatasets)
#       print(f'Datasets gathered for {year}-{month:02}')

        # Opening and concatenating files from the dataset for a specific month
        # Due to the way the data are stored + how CMOR outputs data, it is helpful to set 'mask_and_scale' to 'True' here
        f = xc.open_mfdataset(inputDatasets, mask_and_scale=True, decode_times=True, use_cftime=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
        
        f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds
        d = f[inputVarName]
        
        time = f.time
        lat = f.lat.values
        lon = f.lon.values
        
        lat_bounds = f.lat_bnds
        lon_bounds = f.lon_bnds
        time_bounds = f.time_bnds

        units = f.time.encoding["units"]
        calendar = f.time.encoding.get("calendar", "standard")
        time_vals = cftime.date2num(f.time.values, units=units, calendar=calendar).astype("float64")
        time_bnds_vals = cftime.date2num(time_bounds.values, units=units, calendar=calendar).astype("float64")
        
        #%% Initialize and run CMOR
        # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
        cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
        cmor.dataset_json(inputJson)
        cmor.load_table(cmorTable)
        cmor.set_cur_dataset_attribute('history',f.history)
        axes    = [ {'table_entry': 'time',
                     'units': time.encoding["units"],
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
        varid   = cmor.variable(outputVarName,str(d.units.values),axisIds,missing_value=cmor_missing)
        values  = np.array(d.values,np.float32)
        
        # Since 'analysed_sst' is stored as a 'short' integer array in these data files,
        # it is easiest to 'mask_and_scale' the data (as we do in 'xc.open_dataset' above)
        # and apply the conversion to degrees Celsius and set the missing data values here.
        fill = getattr(d, "_FillValue", None) 
        mask = ~np.isfinite(values) | (values == fill) 
        values = np.where(mask, cmor_missing, values-273.15)
        
        # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_variable_attribute(varid,'valid_min','f',-1.8) # set manually for the time being
        cmor.set_variable_attribute(varid,'valid_max','f',45.)
        
        # Provenance info
        git_commit_number = obs4MIPsLib.get_git_revision_hash()
        path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
        full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code.lstrip('/')}"
        cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")
        
        # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
        cmor.write(varid,values,time_vals=time_vals,time_bnds=time_bnds_vals) ; # Write variable with time axis
        f.close()
        cmor.close()

import cmor
import xcdat as xc
import numpy as np
import glob
import json
import os
import sys
sys.path.append("../../../../inputs/misc/") # Path to obs4MIPsLib

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
cmorTable = '../../../../Tables/obs4MIPs_Aday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'GPCP_Daily_v03r03.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/cdirs/m4581/obs4MIPs/obs4MIPs_input/NASA-GSFC/GPCP-3-3/daily' # change to location on user's machine
inputVarName = 'precip'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
cmor_missing = np.float32(1.0e20)


for year in range(1998, 2025):  # put the years you want to process here
    inputDatasets = []
    for month in range(1,13):
        inputFiles = glob.glob(f"{inputFilePath}/GPCPDAY_L3_{year}{month:02}??_V3.3.nc4")
        inputFiles.sort() # to ensure data files are in chronological order. Code will break otherwise
        for inputFile in inputFiles:
            inputDatasets.append(inputFile)

    ### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
    #%% Process variable (with time axis)
    # Open and read input netcdf file
    f = xc.open_mfdataset(inputDatasets, mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
    d = f[inputVarName]

    lat = f.lat
    lon = f.lon
    time = f.time
    time_bounds = f.time_bnds
    lon_bounds = f.lon_bnds
    lat_bounds = f.lat_bnds

    #%% Initialize and run CMOR
    # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
    cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)
    cmor.dataset_json(inputJson)
    cmor.load_table(cmorTable)
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

    unit = getattr(d, "units", "").lower()
    if "mm/day" in unit:
        sec = 86400.0
    elif "mm/hr" in unit or "mm/hour" in unit:
        sec = 3600.0
    else:
        raise ValueError(f"Unsupported unit: {unit}")

    # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing)
    values  = np.array(d.values,np.float32)
    fill = getattr(d, "_FillValue", None)
    mask = ~np.isfinite(values) | (values == fill)
    values = np.where(mask, cmor_missing, values / sec) #convert to kg m-2 s-1


    # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_variable_attribute(varid,'valid_min','f',float(d.valid_range[0]/86400)) #CMOR API requires a native Python float  
    cmor.set_variable_attribute(varid,'valid_max','f',float(d.valid_range[-1]/86400)) #CMOR API requires a native Python float

    # Provenance info
    git_commit_number = obs4MIPsLib.get_git_revision_hash()
    path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code.lstrip('/')}"
    cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

    print(f'CMOR begin for {year}')
    # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
    cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
    f.close()
    cmor.close()
    print(f'File created for {year}')
    print()

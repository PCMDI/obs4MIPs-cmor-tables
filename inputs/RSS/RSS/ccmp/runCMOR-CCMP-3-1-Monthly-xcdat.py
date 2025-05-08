import cmor
import xcdat as xc
import numpy as np
import json
import os
import sys
sys.path.append("/home/manaster1/obs4MIPs-cmor-tables/inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib
from fix_dataset_time import monthly_times

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CCMP_Monthly_v03r01.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/RSS/ccmp/v03.1/mon/' # change to location on user's machine
inputVarName = 'w'
outputVarName = 'sfcWind'
outputUnits = 'm s-1'

for year in range(1993, 2024):  # put the years you want to process here
    inputDatasets = []
    for month in range(1,13):
        inputFile = f"{inputFilePath}/CCMP_Wind_Analysis_{year}{month:02}_monthly_mean_V03.1_L4.nc"
        if not os.path.isfile(inputFile): continue
        inputDatasets.append(inputFile)

    print(f'Files acquired for {year}')
    ### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
    #%% Process variable (with time axis)
    # Open and read input netcdf files
    f = xc.open_mfdataset(inputDatasets, mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')

     # Added for xCDAT 0.6.0 to include time bounds.
    f = f.bounds.add_bounds("T")

    d = f[inputVarName]

    lat = f.latitude
    lon = f.longitude
    lon_bounds = f.longitude_bnds
    lat_bounds = f.latitude_bnds

    datumyr = f.time.units.split('since')[1][0:5] # reference year
    datummnth = f.time.units.split('since')[1][6:8] # reference month

    time, time_bounds, time_units = monthly_times(datumyr, year, datum_start_month=datummnth, start_month=1, end_month=12)

    #%% Initialize and run CMOR
    # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
    cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)
    cmor.dataset_json(inputJson)
    cmor.load_table(cmorTable)
    axes    = [ {'table_entry': 'time',
                'units': time_units,
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
    varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=d._FillValue)
    values  = np.array(d.values,np.float32)

    # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_variable_attribute(varid,'valid_min','f',float(d.valid_min))   # 'float' needs to be added for CMOR to register the 'valid_min' and 'valid_max'   
    cmor.set_variable_attribute(varid,'valid_max','f',float(d.valid_max))

    # Add GitHub commit ID attribute to output CMOR file
    gitinfo = obs4MIPsLib.getGitInfo("./")
    commit_num = gitinfo[0].split(':')[1].strip()

    paths = os.getcwd().split('/inputs')
    path_to_code = f"/inputs{paths[1]}"
    
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{commit_num}{path_to_code}"
    cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

    print(f'CMOR begin for {year}')
    # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
    cmor.write(varid,values,time_vals=time,time_bnds=time_bounds) ; # Write variable with time axis
    f.close()
    cmor.close()
    print(f'File created for {year}')
    print()
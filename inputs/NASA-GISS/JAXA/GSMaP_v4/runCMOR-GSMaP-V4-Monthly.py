import cmor
import xcdat as xc
import numpy as np
import glob
import os
import sys
import cftime
from datetime import datetime
sys.path.append("../../../../inputs/misc/") # Path to obs4MIPsLib
import obs4MIPsLib

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'GSMaP_v4_monthly.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/JAXA-20260422/GSMaP/monthly/version4'
inputVarName = 'monthlyPrecipRate'
inputUnits= 'mm/hr'
sec = 3600.0
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

for year in range(2014,2027):  # put the years you want to process here
    inputFiles = glob.glob(f"{inputFilePath}/GPMMRG_MAP_{str(year)[-2:]}??_M_L3S_MCN_04?.nc")
    if len(inputFiles) == 0:
        continue

    # Open and read input netcdf files
    # Process variable (with time axis)
    inputFiles.sort()
    data_list=[]
    times = []
    time_bnds_list = []
    for fn in inputFiles:
        f = xc.open_dataset(fn, mask_and_scale=True, decode_times=False)
        data_list.append(f[inputVarName].values)

        yymm = os.path.basename(fn).split('_')[2]   # e.g. '2012'
        month = int(yymm[2:])
        start = cftime.DatetimeGregorian(year, month, 1)
        if month == 12: 
            end = cftime.DatetimeGregorian(year+1, 1, 1)
        else:
            end = cftime.DatetimeGregorian(year, month+1, 1)
        mid = start + (end - start)/2
        times.append(mid)
        time_bnds_list.append([start, end])

    fill = getattr(f[inputVarName], "_FillValue", None)
    d = np.stack(data_list, axis=0)  # (time, lon, lat)
    d = np.transpose(d,(0,2,1)) # need to transpose the latitudes and longitudes

    lat = f.Latitude.values[0,:]
    lon = f.Longitude.values[:,0]
    dlat = np.abs(lat[1] - lat[0]) / 2
    dlon = np.abs(lon[1] - lon[0]) / 2
    lat_bnds = np.vstack([lat - dlat, lat + dlat]).T
    lon_bnds = np.vstack([lon - dlon, lon + dlon]).T

    # Due to CMOR warnings related to the way latitudes and longitudes are read in/rounded
    # need to round lat and lon bounds to 3 places after the decimal
    lat_bnds = np.around(lat_bnds, 3)
    lon_bnds = np.around(lon_bnds, 3)

    t_units = "days since 1950-01-01" 
    calendar = "standard"
    time = cftime.date2num(times, units=t_units, calendar=calendar).astype("float64")
    time_bnds = cftime.date2num(time_bnds_list, units=t_units, calendar=calendar).astype("float64")

    #%% Initialize and run CMOR
    # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
    cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
    cmor.dataset_json(inputJson)
    cmor.set_cur_dataset_attribute("version", run_version)
    cmor.load_table(cmorTable)

    axes = [
        {"table_entry": "time", "units": t_units},
        {"table_entry": "latitude", "units": "degrees_north",
         "coord_vals": lat, "cell_bounds": lat_bnds},
        {"table_entry": "longitude", "units": "degrees_east",
         "coord_vals": lon, "cell_bounds": lon_bnds},
    ]
    axisIds = [cmor.axis(**ax) for ax in axes]

    #create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    varid = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing)
    values = np.array(d,np.float32)
    fill = getattr(d, "_FillValue", None)
    mask = ~np.isfinite(values) | (values == fill)
    values = np.where(mask, cmor_missing, values/sec) #convert to kg m-2 s-1

    # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_variable_attribute(varid,'valid_min','f',0.0)
    cmor.set_variable_attribute(varid,'valid_max','f',100.0/86400.) # setting these manually for the time being.

    # Provenance info
    git_commit_number = obs4MIPsLib.get_git_revision_hash()
    path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code.lstrip('/')}"
    cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

    # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
    cmor.write(varid,values,time_vals=time,time_bnds=time_bnds) ; # Write variable with time axis
    f.close()
    cmor.close()
    print(f"File written for {year}")

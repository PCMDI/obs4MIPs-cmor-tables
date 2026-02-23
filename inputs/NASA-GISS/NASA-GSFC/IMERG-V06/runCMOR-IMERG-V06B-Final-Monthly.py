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

def has_bounds(ds, names):
    return any(n in ds.variables or n in ds.coords for n in names)

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'IMERG-V06B-Final-Monthly.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/NASA-GSFC/IMERG6/monthly'
inputVarName = 'precipitation'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

for year in range(2000, 2022):  # put the years you want to process here
    inputFiles = glob.glob(f"{inputFilePath}/3B-MO.MS.MRG.3IMERG.{year}??01-S000000-E235959.??.V06B.HDF5")
    if len(inputFiles) == 0:
        continue

    # Open and read input netcdf files
    # Process variable (with time axis)
    inputFiles.sort()
    f = xc.open_mfdataset(inputFiles, group='Grid', mask_and_scale=True, decode_times=True, use_cftime=True, combine='nested', concat_dim='time')
    if not has_bounds(f, ["time_bnds", "time_bounds"]):
        f = f.bounds.add_bounds("T")
    if not has_bounds(f, ["lat_bnds", "lat_bounds"]):
        f = f.bounds.add_bounds("Y")
    if not has_bounds(f, ["lon_bnds", "lon_bounds"]):
        f = f.bounds.add_bounds("X")

    d = f[inputVarName]
    d = d.transpose('time','lat','lon') # need to transpose the IMEG latitudes and longitudes

    lat = f.lat.values
    lon = f.lon.values
    # Due to CMOR warnings related to the way latitudes and longitudes are read in/rounded
    # need to round lat and lon bounds to 3 places after the decimal
    lat_bnds = np.around(f.get("lat_bnds", f.get("lat_bounds")).values, 3)
    lon_bnds = np.around(f.get("lon_bnds", f.get("lon_bounds")).values, 3)

    t_units = f.time.attrs.get("units") or f.time.encoding.get("units")
    calendar = f.time.attrs.get("calendar") or f.time.encoding.get("calendar", "standard")
    time = cftime.date2num(f.time.values, units=t_units, calendar=calendar).astype("float64")
    time_bnds = cftime.date2num(f.get("time_bnds", f.get("time_bounds")).values, units=t_units, calendar=calendar).astype("float64")

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

    # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    d_units = getattr(d, "units", "").lower()
    if "mm/day" in d_units:
        sec = 86400.0
    elif "mm/hr" in d_units or "mm/hour" in d_units:
        sec = 3600.0
    else:
        raise ValueError(f"Unsupported unit: {d_units}")

    varid = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing)
    values = np.array(d.values,np.float32)
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

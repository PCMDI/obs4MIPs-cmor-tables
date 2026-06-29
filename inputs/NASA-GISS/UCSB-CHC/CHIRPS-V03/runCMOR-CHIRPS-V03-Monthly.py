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
inputJson = 'CHIRPS-V03-Monthly.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/UCSB-CHC/CHIRPS-V3/monthly'
inputVarName = 'precip'
inputUnits= 'mm/month'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

inputFiles = f"{inputFilePath}/chirps-v3.0.monthly.nc"

# Open and read input netcdf files
# Process variable (with time axis)
f = xc.open_dataset(inputFiles, mask_and_scale=True, decode_times=True, use_cftime=True)
d = f[inputVarName]

lat = f.latitude.values
lon = f.longitude.values
f = f.bounds.add_bounds("Y")
f = f.bounds.add_bounds("X")
# Due to CMOR warnings related to the way latitudes and longitudes are read in/rounded
# need to round lat and lon bounds to 3 places after the decimal
lat_bnds = np.around(f["latitude_bnds"].values, 3)
lon_bnds = np.around(f["longitude_bnds"].values, 3)

t_units = f.time.attrs.get("units") or f.time.encoding.get("units")
calendar = f.time.attrs.get("calendar") or f.time.encoding.get("calendar", "standard")
time = cftime.date2num(f.time.values, units=t_units, calendar=calendar).astype("float64")
tbeg = f.time.values
tend = []
for t in tbeg:
    if t.month == 12:
        tend.append(cftime.DatetimeGregorian(t.year+1,1,1))
    else:
        tend.append(cftime.DatetimeGregorian(t.year,t.month+1,1))
time_bnds = cftime.date2num(np.column_stack([tbeg, tend]), units=t_units, calendar=calendar).astype("float64")

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
sec = np.array([t.daysinmonth * 86400.0 for t in f.time.values], dtype=np.float32)[:, None, None]
varid = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing)
values = np.array(d.values,np.float32)
fill = getattr(d, "_FillValue", None)
mask = ~np.isfinite(values) | (values == fill)
values = np.where(mask, cmor_missing, values/sec) #convert to kg m-2 s-1

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',0.0)
cmor.set_variable_attribute(varid,'valid_max','f',1000.0/86400.) # setting these manually for the time being.

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
print(f"File written for {inputVarName}")

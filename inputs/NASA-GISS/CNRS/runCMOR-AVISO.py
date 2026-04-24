import cmor
import xcdat as xc
import numpy as np
import glob,os,sys
import cftime
from datetime import datetime
sys.path.append("../../../inputs/misc/") # Path to obs4MIPsLib
import obs4MIPsLib

def has_bounds(ds, names):
    return any(n in ds.variables or n in ds.coords for n in names)

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'AVISO-input.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/CMEMS-20260316/AVISO-20260316' # change to local path on user's machine where files are stored
inputUnits = 'm'
inputVarName = 'adt'
outputVarName = 'zos'
outputUnits = 'm'
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

inputFiles = f"{inputFilePath}/adt_mon_1993_2025.nc"

# Open and read input netcdf files
# Process variable (with time axis)
f = xc.open_dataset(inputFiles, mask_and_scale=True, decode_times=True, use_cftime=True)
f = f.bounds.add_bounds("Y")
f = f.bounds.add_bounds("X")

d = f[inputVarName]

lat = f.latitude.values
lon = f.longitude.values
lat_bnds = f.latitude_bnds.values
lon_bnds = f.longitude_bnds.values

t_units = f.time.attrs.get("units") or f.time.encoding.get("units")
calendar = f.time.attrs.get("calendar") or f.time.encoding.get("calendar", "standard")
time = cftime.date2num(f.time.values, units=t_units, calendar=calendar).astype("float64")
#original time_bnds has gap, rebuild time_bnds
new_bnds = []
for t in f.time.values:
    start = cftime.DatetimeGregorian(t.year, t.month, 1)
    if t.month == 12:
        end = cftime.DatetimeGregorian(t.year + 1, 1, 1)
    else:
        end = cftime.DatetimeGregorian(t.year, t.month + 1, 1)
    new_bnds.append([start, end])
new_bnds = np.array(new_bnds, dtype=object)
time_bnds = cftime.date2num(new_bnds, units=t_units, calendar=calendar).astype("float64")

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
varid = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing)
values = np.array(d.values,np.float32)
fill = getattr(d, "_FillValue", None)
mask = ~np.isfinite(values) | (values == fill)
# --- remove global mean ---
weights_2d = (np.cos(np.deg2rad(lat)))[:, None]  # broadcast to (lat, lon)
values_masked = np.where(mask, np.nan, values)
gm = np.nansum(values_masked * weights_2d, axis=(1,2)) / np.nansum(weights_2d * (~mask), axis=(1,2))
values = values - gm[:, None, None]
#get valid_min/max from actual values
valid_values = values[~mask]
vmin = float(valid_values.min())
vmax = float(valid_values.max())

values = np.where(mask, cmor_missing, values)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',vmin)
cmor.set_variable_attribute(varid,'valid_max','f',vmax)

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
print(f"File written")

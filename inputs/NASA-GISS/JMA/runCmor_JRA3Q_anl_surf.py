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
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputJson = 'JMA-JRA3Q_anl_p_surf.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/JMA/JRA3Q_monthly/monthly2D'
inputVarName = [v + '-an-gauss-mn' for v in ['tmp2m-hgt','ugrd10m-hgt','vgrd10m-hgt','spfh2m-hgt','prmsl-msl']]
outputVarName = ['tas','uas','vas','huss','psl']  
outputUnits = ['K','m s-1','m s-1','1','Pa'] 
valid_min=[180.,-150.,-150.,0.,80000.]
valid_max=[340.,150.,150.,0.05,110000.]
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

for var, out_var, out_unit,out_min, out_max in zip(inputVarName, outputVarName, outputUnits,valid_min,valid_max):
    inputFiles = glob.glob(f"{inputFilePath}/{var}/*.{var}.jra3q-ms-mn.anl_surf.*.{var}.??????0100_????????18.nc")
    print(len(inputFiles))
    if len(inputFiles) == 0:
        continue

    # Open and read input netcdf files
    # Process variable (with time axis)
    inputFiles.sort()
    f = xc.open_mfdataset(inputFiles, mask_and_scale=True, decode_times=True, use_cftime=True)
    if not has_bounds(f, ["time_bnds", "time_bounds"]):
        f = f.bounds.add_bounds("T")
    if not has_bounds(f, ["lat_bnds", "lat_bounds"]):
        f = f.bounds.add_bounds("Y")
    if not has_bounds(f, ["lon_bnds", "lon_bounds"]):
        f = f.bounds.add_bounds("X")

    lat = f.lat.values
    lon = f.lon.values
    lat_bnds = f.get("lat_bnds", f.get("lat_bounds")).values
    lon_bnds = f.get("lon_bnds", f.get("lon_bounds")).values

    t_units = f.time.attrs.get("units") or f.time.encoding.get("units")
    calendar = f.time.attrs.get("calendar") or f.time.encoding.get("calendar", "standard")
    time = cftime.date2num(f.time.values, units=t_units, calendar=calendar).astype("float64")
    time_bnds = cftime.date2num(f.get("time_bnds", f.get("time_bounds")).values, units=t_units, calendar=calendar).astype("float64")

    d = f[var]

    #%% Initialize and run CMOR
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
    varid = cmor.variable(out_var,out_unit,axisIds,missing_value=cmor_missing)
    values = np.array(d.values,np.float32)
    fill = getattr(d, "_FillValue", None)
    mask = ~np.isfinite(values) | (values == fill)
    values = np.where(mask, cmor_missing, values)

    # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_variable_attribute(varid, 'valid_min', 'f', float(out_min))
    cmor.set_variable_attribute(varid, 'valid_max', 'f', float(out_max))

    # Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
    git_commit_number = obs4MIPsLib.get_git_revision_hash()
    path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
    cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

    # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
    cmor.write(varid,values,time_vals=time,time_bnds=time_bnds) ; # Write variable with time axis
    f.close()
    cmor.close()
    print(f"File written for {out_var}")

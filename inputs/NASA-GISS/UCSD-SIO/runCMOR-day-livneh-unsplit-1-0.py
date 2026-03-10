import cmor
import xcdat as xc
import numpy as np
import glob,os,sys
import cftime
from datetime import datetime
sys.path.append("../../../../inputs/misc/") # Path to obs4MIPsLib and code to fix times
import obs4MIPsLib

def has_bounds(ds, names):
    return any(n in ds.variables or n in ds.coords for n in names)

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Aday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'livneh-unsplit_UCSD-SIO_inputs.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/UCSD-SIO/nonsplit_precip/precip' 
inputVarName = ['PRCP']
inputUnits = ['mm']  #input units same as required (?) output units, no unit conversion needed
outputVarName = ['pr']
outputUnits = ['kg m-2 s-1']
unit_factor=[86400.]
valid_min=[0.]            #referenced from the actual input data values
valid_max=[0.005]         #referenced from the actual input data values
run_version = "v" + datetime.now().strftime("%Y%m%d") # fixed for entire run
cmor_missing = np.float32(1.0e20)

for fi in range(len(inputVarName)): #looping over varaibles
    for year in range(1915, 2019):  # put the years you want to process here
        inputFiles = f"{inputFilePath}/livneh_unsplit_precip.2021-05-02.{year}.nc"
        if len(inputFiles) == 0:
            continue

        f = xc.open_dataset(inputFiles, mask_and_scale=True, decode_times=False)
        f = f.rename({"Time": "time"})
        f = xc.decode_time(f)
        if not has_bounds(f, ["time_bnds", "time_bounds"]):
            f = f.bounds.add_bounds("T")
        if not has_bounds(f, ["lat_bnds", "lat_bounds"]):
            f = f.bounds.add_bounds("Y")
        if not has_bounds(f, ["lon_bnds", "lon_bounds"]):
            f = f.bounds.add_bounds("X")

        d = f[inputVarName[fi]]
    
        lat = f.lat.values
        lon = f.lon.values
        lat_bnds = f.get("lat_bnds", f.get("lat_bounds")).values
        lon_bnds = f.get("lon_bnds", f.get("lon_bounds")).values
    
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
        varid = cmor.variable(outputVarName[fi],outputUnits[fi],axisIds,missing_value=cmor_missing)
        values = np.array(d.values,np.float32)
        fill = getattr(d, "_FillValue", None)
        mask = ~np.isfinite(values) | (values == fill)
        if inputUnits[fi] == 'mm':
            values = np.where(mask, cmor_missing, values/unit_factor[fi])
#       elif inputUnits[fi] == 'degreesC':
#           values = np.where(mask, cmor_missing, values+unit_factor[fi])
        else:
            print('add unit convertsion')
    
        # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_variable_attribute(varid,'valid_min','f',valid_min[fi])
        cmor.set_variable_attribute(varid,'valid_max','f',valid_max[fi])
    
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
        print(f"File written for {inputVarName[fi]} for {year}")

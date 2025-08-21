import os, sys
import cmor
import xarray as xr
import numpy as np
try:
    import simplejson as json
except ImportError:
    import json
from glob import glob
from datetime import datetime, timezone, timedelta

sys.path.append('../../misc') # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable = '../../../Tables/obs4MIPs_SImon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'OSI-450-sh.json' ; # Update contents of this file to set your global_attributes
inputFileDir = '.../obs4MIPs-cmor-tables/inputs/MET-Norway/MET-Norway/OSI-450-nh/' # Folder with montly input files
inputFileName = 'OBS_OSI-450-nh_reanaly_v3_OImon_sic_197901-197912.nc' # Filename pattern of monthly input files created in ESMValTool 
inputVarName = 'sic'
outputVarName = 'siconc'
outputUnits = '%'

# Open and read input netcdf file, get coordinates and add bounds
#f = xr.open_mfdataset(glob(os.path.join(inputFileDir, inputFileName)), decode_times=False)
f = xr.open_mfdataset(sorted(glob(os.path.join(inputFileDir, inputFileName))), decode_times=False, combine='nested', concat_dim='time')
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values 
time = f.time.values  
tbds = f.time_bnds.values

# Insert missing time/data for missing monthly files
missing_dates, missing_dates_ts = [], []
new_time, new_tbds = [], []
for n,t in enumerate(time):
    dt = datetime.fromtimestamp(t)
    try:
        if ( (dt - prev).days > 35 ):
            # Generate timestamp for missing date
            dt_tmp = datetime(dt.year, dt.month, 1, 12, 0, 0) - timedelta(days=1)
            dt_miss = datetime(dt_tmp.year, dt_tmp.month, 16, 12, 0, 0)
            dt_miss_tbds = [datetime.timestamp(datetime(dt_miss.year, dt_miss.month, 1, 0, 0, 0)),
                datetime.timestamp(datetime(dt.year, dt.month, 1, 0, 0, 0))]
            missing_dates.append(dt_miss)
            missing_dates_ts.append(datetime.timestamp(dt_miss))
            new_time.append(datetime.timestamp(dt_miss))
            new_time.append(t)
            new_tbds.append(dt_miss_tbds)
            new_tbds.append(tbds[n])
        else:
            new_time.append(t)
            new_tbds.append(tbds[n])
        prev = dt
    except NameError as e:
        prev = dt
        new_time.append(t)
        new_tbds.append(tbds[n])
        continue

if ( len(missing_dates) > 0 ):
    missing_dates_da = xr.DataArray(missing_dates_ts, dims=['time'], coords=[missing_dates_ts])
    full_time = xr.concat([f.time, missing_dates_da], dim='time')
    full = f.reindex(time=full_time, fill_value=1.e20).sortby('time')
    d = full[inputVarName]

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history', f.history) 

# Create CMOR axes
cmorLat = cmor.axis('latitude', coord_vals=lat[:], cell_bounds=f.lat_bnds.values[0], units='degrees_north')
cmorLon = cmor.axis('longitude', coord_vals=lon[:], cell_bounds=f.lon_bnds.values[0], units='degrees_east')
cmorTime = cmor.axis('time', coord_vals=new_time[:], cell_bounds=new_tbds, units=f.time.units)
cmoraxes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid = cmor.variable(outputVarName, outputUnits, cmoraxes, missing_value=1.e20)
values = np.array(d, np.float32)[:]

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid, 'valid_min', 'f' ,0.0)
cmor.set_variable_attribute(varid, 'valid_max', 'f' ,100.0)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID>
#gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo('./'))
#full_git_path = f'https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo["commit_number"]}/demo'  
#cmor.set_cur_dataset_attribute('processing_code_location', full_git_path)
 
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid, 1, 1, 1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid, values, len(new_time)) 
cmor.close()
f.close()

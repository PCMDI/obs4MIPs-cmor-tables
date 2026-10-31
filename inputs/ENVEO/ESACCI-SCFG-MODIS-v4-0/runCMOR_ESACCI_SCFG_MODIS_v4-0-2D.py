

# --------------------------------------------
# ### INFO: 
# CMOR DOCUMENTATION: `https://cmor.llnl.gov/mydoc_cmor3_api/`
# --------------------------------------------

import cmor
import xcdat as xc
import numpy as np
import pandas as pd
import json, sys, os, glob
from pathlib import Path
from datetime import datetime, timedelta, UTC
import cftime
import time

base_dir = Path(__file__).parents[4] 
table_dir = base_dir / 'obs4MIPs-cmor-tables/'
obs4MIPsLib_path = f'{table_dir}/inputs/misc'
read_git = False
if os.path.exists(obs4MIPsLib_path):
    sys.path.append(obs4MIPsLib_path)
    import obs4MIPsLib
    read_git = True
    print(f'obs4MIPsLib imported.')

total_start = time.perf_counter()


wd = str(Path(__file__).parents[0])
os.chdir(wd)

# --------------------------------------------
# ### INPUT
# --------------------------------------------

# NOTE variable specific
inputVarName    = 'SCFG'

vardict = {'SCFV': 'sncfv','SCFG': 'sncfg'}
outputVarName   = vardict[inputVarName.upper()]

# user provided input
sensor          = 'MODIS'

inputJson = f'./ESACCI-{inputVarName.upper()}-MODIS-v4-0-input.json'
cmorTable = f'{table_dir}/Tables/obs4MIPs_Aday.json' 

# temporal specification
start_period    = '2000-02-24'
end_period      = '2023-12-31'


# Data Types
outputUnits     = '%'
dtype           = 'f'
missing_val     = 1e+20 # original: 255

# input files
# NOTE intern link outside obs4MIPs-cmor-tables
data_path   = str(base_dir / 'data/scf')
input_dir   = f'{data_path}/{inputVarName.lower()}/{sensor}/v4.0/{{year}}/{{month}}/'
input_files = f'{input_dir}{{date}}-ESACCI-L3C_SNOW-{inputVarName}-MODIS_TERRA-fv4.0.nc'

# --------------------------------------------
# LOG FILE
# --------------------------------------------
logdir = (Path(base_dir) / f'CMOR_log' / outputVarName).resolve()
logdir.mkdir(parents=True, exist_ok=True)
ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
logfile = str(logdir / f'log_debug_{ts}.txt')
print('INFO Log-File:', logfile)

def log(str, logfile=logfile):
    try:
        print(str)
        if logfile is not None:
            with open(logfile, 'a') as log:
                log.write(str + '\n')
    except:
        print(str)

logname_cm = str(logdir / f'log_cmor_{ts}')

# --------------------------------------------
# CONVERT DTYPE
# --------------------------------------------
# apply data type to values

np_dtype        = np.dtype(dtype)
actual_range    = tuple(np_dtype.type(v) for v in (0,100))
missing         = np_dtype.type(missing_val)

# --------------------------------------------
# ### RESOLVE PATHS
# --------------------------------------------
# create absolute paths

cmorTable   = str(Path(cmorTable).resolve())
inputJson   = str(Path(inputJson).resolve())

for check, check_path in [['data_path', data_path], ['cmorTable', cmorTable], ['inputJson', inputJson]]:
    if not Path(check_path).exists():
        sys.exit(f'{check} path does not exist: {check_path}')

# --------------------------------------------
# ### TIMESPAN
# --------------------------------------------
# time list for each day

start       = datetime.fromisoformat(start_period)
end         = datetime.fromisoformat(end_period)
all_dates   = [start + timedelta(days=i) for i in range((end - start).days + 1)]

yeardict = {}

for date in all_dates:
    year = date.year
    yeardict.setdefault(year, []).append(date)


# --------------------------------------------
# PREPARATION: DEFINE AXES TIME, LAT, LON
# --------------------------------------------
# Open first file to get lat/lon values
# read first file and extract summary & comment

for date in all_dates:
    file = Path(input_files.format(
        year=date.year,
        month=f'{date.month:02d}',
        date=date.strftime('%Y%m%d')
    )).resolve()

    if not file.is_file():
        continue

    log(f'[INFO] Reference dataset {file}', logfile)
    ds_i = xc.open_dataset(file)

    latitude_units   = ds_i['lat'].units
    latitude_values  = ds_i['lat'].values 
    latitude_bounds  = ds_i['lat_bnds'].values.copy()
    latitude_bounds  = np.round(latitude_bounds, 5)

    longitude_units  = ds_i['lon'].units
    longitude_values = ds_i['lon'].values
    longitude_bounds = ds_i['lon_bnds'].values.copy()
    longitude_bounds = np.round(longitude_bounds, 5)

    nlat             = latitude_values.size
    nlon             = longitude_values.size

    axes = [ 
        {
            'table_entry': 'time',
            'units': 'days since 1950-01-01 00:00:00', 
            },
        {
            'table_entry': 'latitude',
            'units': latitude_units,
            'coord_vals': latitude_values,
            'cell_bounds': latitude_bounds
            },
        {
            'table_entry': 'longitude',
            'units': longitude_units,
            'coord_vals': longitude_values,
            'cell_bounds': longitude_bounds
            },
        ]

    history = ds_i.history

    # get attributes
    try:
        attribute_dict = {}
        for item in ['summary', 'comment']:
            if item in ds_i.attrs:
                attribute_dict[item] = ds_i.attrs.get(item, None)
                log(f'Attribte {item} read from reference dataset: {attribute_dict[item]}', logfile)
    except:
        attribute_dict = None
        msg = f'Attributes "summary" and "comment" not extracted from {file}'
        log(msg, logfile)
        raise ValueError(msg)

    ds_i.close()

    break

# --------------------------------------------
# ### PREPARING CMOR netCDF for one year
# --------------------------------------------
# documentation: `https://cmor.llnl.gov/mydoc_cmor3_api/`
try:
    for year, dates in yeardict.items():

        log(f'Processing year {year}', logfile)
        logfile_cm = logname_cm + f'_{year}.txt'
        log(f'CMOR Log-File: {logfile_cm}', logfile)

        try:
            cmor.setup(
                inpath='./', 
                netcdf_file_action=cmor.CMOR_REPLACE_4,    
                exit_control=cmor.CMOR_NORMAL,
                logfile=logfile_cm
                )
            cmor.dataset_json(inputJson)
            cmor.load_table(cmorTable)
            cmor.set_cur_dataset_attribute('history', history) 

            axisIds = list() ; 
            for ax in axes:
                axisId = cmor.axis(**ax)
                axisIds.append(axisId)
            
            # SETUP CMOR
            # Setup units and create variable to write using cmor
            # see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
            
            varid = cmor.variable(
                table_entry = outputVarName,
                units = outputUnits,
                axis_ids = axisIds,
                data_type = dtype,
                missing_value = missing
                )
            
            cmor.set_deflate(
                var_id=varid,
                shuffle=1,
                deflate=1,
                deflate_level=1
                )

            # ### ATTRIBUTES
            # Add attributes to cmor from original dataset
            # log(attribute_dict, logfile)
            if attribute_dict is not None:
                for item, value in attribute_dict.items():
                    if value is not None:
                        cmor.set_cur_dataset_attribute(item, value)
                        log(f'[CMOR attributes {year}] Set dataset_attribute "{item}": {value}', logfile)
                    else:
                        log(f'[CMOR attributes {year}] Did not set dataset_attribute "{item}": {value}', logfile)

            # ### GIT
            # append URL for GIT
            if read_git:
                os.chdir(table_dir)
                try:
                    git_commit_number = obs4MIPsLib.get_git_revision_hash()
                    path_to_code = str(Path(__file__).parent).split("obs4MIPs-cmor-tables")[-1]
                    path_to_code = str(Path(f'{table_dir}/inputs/ENVEO/ESACCI-{inputVarName.upper()}-MODIS-v4-0/').resolve()).split("obs4MIPs-cmor-tables/")[-1]
                    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
                    log(f'[INFO {year}] Git path: {full_git_path}', logfile)
                    cmor.set_cur_dataset_attribute("processing_code_location", full_git_path)
                except Exception as error:
                    log(f'[INFO {year}] [WARNING] Git commit number not created. See error:', logfile)
                    log(f'[INFO {year}] {error}', logfile)
            os.chdir(wd)

            # ### DATA
            # Reference timestemp
            base_time   = cftime.DatetimeGregorian(1950, 1, 1, 0, 0, 0)

            # write dates to cmor netcdf
            for date in dates:
                scene_start = time.perf_counter()

                # define filepath
                file = Path(input_files.format(
                    year=date.year,
                    month=f'{date.month:02d}',
                    date=date.strftime('%Y%m%d')
                )).resolve()


                # read data
                if file.is_file():
                    ds = xc.open_dataset(file)
                    data = ds[inputVarName.lower()].values.astype(dtype)
                    mask = ((data < actual_range[0]) | (data > actual_range[1])) 
                    data[mask] = missing 
                    ds.close()
                    log(f'[CMOR {date}] Dataset read: {file}', logfile)
                
                # empty data filled with nan
                else:
                    data = np.full((nlat, nlon), missing, dtype=dtype)
                    log(f'[CMOR {date}] Dataset empty. FILLED with no data.', logfile)

                # Timestamp as days since 1950
                cf_date     = cftime.DatetimeGregorian(date.year, date.month, date.day, 0, 0, 0)
                time_start  = (cf_date - base_time).total_seconds() / 86400.0
                time_bnds   = np.array([[time_start, time_start + 1.0]], dtype="d")

                # Representative time coordinate = midpoint of bounds
                coord_val = np.mean(time_bnds, axis=1)

                cmor.write(
                    var_id=varid,
                    data=data,
                    time_vals=coord_val,
                    time_bnds=time_bnds
                )
                
                log(f'[CMOR {date}] Wrote data to obs4mips dataset', logfile)
                
                scene_duration = time.perf_counter() - scene_start
                log(f'[CMOR {date}] Duration: {scene_duration:.2f} sec', logfile)

        except Exception as error:
            log(f'[ERROR {year}] {error}', logfile)
            raise Exception(f'[FAIL {year}] see logfile: {logfile}')

        finally:
            cmor.close()
        
finally:
    total_end = time.perf_counter()
    total_duration = total_end - total_start
    log(f'[INFO {year}] Duration: {total_duration:.2f} sec', logfile)

log('[INFO] DONE.', logfile)



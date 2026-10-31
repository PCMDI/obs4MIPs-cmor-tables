#writes out ancillary data files for the SnowCCI SCFV obs4mips data

#import xcdat
import os, sys, glob
import xarray as xr
import numpy as np
import pandas as pd
import uuid
from datetime import datetime, UTC
from netCDF4 import Dataset
from pathlib import Path
import time

# --------------------------------------------
# ### INPUT INFORMATION
# --------------------------------------------

# temporal specification
start_period    = '2000-02-24'
end_period      = '2023-12-31'

# NOTE: Variable specific
inputVarName = 'SCFG'

vardict         = {'SCFV': 'sncfv','SCFG': 'sncfg'}
labeldict       = {'SCFV': 'Viewable','SCFG': 'on Ground'}
standard_name   = {'SCFV': 'snow_area_fraction_viewable_from_above','SCFG': 'surface_snow_area_fraction_on_ground'}
uncdict         = {'SCFV': 'viewable snow','SCFG': 'snow on ground'}

# variables
institution = 'ENVEO'
frequency   = 'day'
grid_label  = 'gn'
source_id   = f'ESACCI-{inputVarName}-MODIS-v4-0'
variable_id = vardict[inputVarName]

# netcdf
sensor      = 'MODIS'

# uncertainty
unc         = 'stderr'
unc_long    = 'standard_error'
dtype       = 'f4'
missing_val = 1e+20 

unc_id      = f'{variable_id}{unc}'

# new netcdf attributes
new_title       = f"ESA CCI {labeldict[inputVarName].lower()} snow product level L3C daily from MODIS: standard error"
new_long_name   = f"Standard Error for Snow Cover Fraction {labeldict[inputVarName]}"
new_comment     = f"Unbiased Root Mean Square Error for the obs4MIPs source_id {source_id}"
label_uscore    = labeldict[inputVarName].lower().replace(' ', '_')

# --------------------------------------------
# LOG FILE
# --------------------------------------------
total_start = time.perf_counter()
base_dir = Path(__file__).parents[4].resolve()
logdir   = (base_dir / f'CMOR_log' / variable_id)

logdir.mkdir(parents=True, exist_ok=True)
ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
logfile = str(logdir / f'log_unc_debug_{ts}.txt')
print('INFO Log-File:', logfile)

def log(str, logfile=logfile):
    try:
        print(str)
        if logfile is not None:
            with open(logfile, 'a') as log:
                log.write(str + '\n')
    except:
        print(str)

log(f'Write {unc_id} for {inputVarName}')

# --------------------------------------------
# ### PREPARE VARIABLES
# --------------------------------------------

start = datetime.fromisoformat(start_period)
end   = datetime.fromisoformat(end_period)

yeardict = {}

for year in range(start.year, end.year + 1):

    year_start = max(start, datetime(year, 1, 1))
    year_end   = min(end, datetime(year, 12, 31))

    yeardict[year] = (
        year_start.strftime("%Y%m%d"),
        year_end.strftime("%Y%m%d"),
    )

for year, (sd, ed) in yeardict.items():
    cpath = str(Path(__file__).parent.parent)

    # obs4mips file
    cdate       = datetime.now(UTC).strftime("%Y%m%d")
    o4m_file    = f'{cpath}/out/obs4MIPs/{institution}/{source_id}/{frequency}/{variable_id}/{grid_label}/v{cdate}/{variable_id}_{frequency}_{source_id}_{institution}_{grid_label}_{sd}-{ed}.nc'

    odir        = f'{str(Path(o4m_file).resolve().parents[0])}_{unc}'

    basename    = Path(o4m_file).name
    n_basename  = basename.replace(vardict[inputVarName], vardict[inputVarName]+unc)
    outfile     = os.path.join(odir, n_basename)

    # input files
    data_path   = str(base_dir / 'data' / 'scf')

    input_dir   = f'{data_path}/{inputVarName.lower()}/{sensor}/v4.0/{{year}}/{{month}}/'
    input_files = f'{input_dir}{{date}}-ESACCI-L3C_SNOW-{inputVarName}-MODIS_TERRA-fv4.0.nc'
    layer_input = f'{inputVarName.lower()}_unc'

    # --------------------------------------------
    # PROCESSING
    # --------------------------------------------

    # apply data type to values
    np_dtype        = np.dtype(dtype)
    missing         = np_dtype.type(missing_val)

    # --------------------------------------------
    # CHECK INPUT DATA
    # --------------------------------------------

    if not Path(o4m_file).resolve().exists():
        sys.exit(f'Path does not exist: {str(Path(o4m_file).resolve())}')

    # --------------------------------------------
    # CREATE OUTPUT DIRECTORY
    # --------------------------------------------
    if not Path(odir).is_dir():
        Path(odir).mkdir(parents=True, exist_ok=True)

    log(f'Output File: {outfile}')

    # --------------------------------------------
    # READ OBS4MIPS netCDF
    # --------------------------------------------


    # read in with xarray
    ds_o4m      = xr.open_dataset(o4m_file) #, chunks={"time": 1})
    ds_o4m_raw  = xr.open_dataset(o4m_file, decode_times=False) 

    lat     = ds_o4m.lat
    lon     = ds_o4m.lon
    time_ds = ds_o4m.time

    lat_raw     = ds_o4m_raw["lat"]
    lon_raw     = ds_o4m_raw["lon"]
    time_raw    = ds_o4m_raw["time"]

    nlat        = lat_raw.size 
    nlon        = lon_raw.size 

    old_comment = ds_o4m.attrs.get("comment", "")

    # --------------------------------------------
    # WRITE netCDF
    # --------------------------------------------

    # DIMENSIONS

    # nc = Dataset(outfile, "w", format="NETCDF4")
    nc = Dataset(outfile, "w", format="NETCDF4_CLASSIC")
    nc.createDimension("time", None)
    nc.createDimension("lat", nlat)
    nc.createDimension("lon", nlon)

    if "bnds" in ds_o4m_raw.dims:
        nc.createDimension("bnds", ds_o4m_raw.sizes["bnds"]) 

    # Define coordinate variables in original datatype in cmor order
    def copy_variable(src_ds, dst_nc, name):
        var = src_ds[name]

        for dim in var.dims:
            if dim not in dst_nc.dimensions:
                dst_nc.createDimension(dim, var.sizes[dim])

        out = dst_nc.createVariable(name, var.dtype, var.dims)
        out[:] = var.values

        for k, v in var.attrs.items():
            setattr(out, k, v)

        return out

    timev = copy_variable(ds_o4m_raw, nc, "time")

    if "time_bnds" in ds_o4m_raw.variables:
        copy_variable(ds_o4m_raw, nc, "time_bnds")

    latv = copy_variable(ds_o4m_raw, nc, "lat")
    if "lat_bnds" in ds_o4m_raw.variables:
        copy_variable(ds_o4m_raw, nc, "lat_bnds")

    lonv = copy_variable(ds_o4m_raw, nc, "lon")
    if "lon_bnds" in ds_o4m_raw.variables:
        copy_variable(ds_o4m_raw, nc, "lon_bnds")

    # spatial ref
    if "spatial_ref" in ds_o4m_raw.variables: 
        svar = ds_o4m_raw["spatial_ref"]  
        for dim in svar.dims:  
            if dim not in nc.dimensions:  
                nc.createDimension(dim, svar.sizes[dim])  
        spatial_ref = nc.createVariable("spatial_ref", svar.dtype, svar.dims)  
        spatial_ref[...] = svar.values  
        for k, v in svar.attrs.items():  
            setattr(spatial_ref, k, v)  

    # UNCERTAINTY VARIABLE

    #Define standard deviation variable
    sev = nc.createVariable(
        unc_id,
        np_dtype,
        ("time", "lat", "lon"),
        fill_value=missing,
        zlib=True,
        complevel=1,
        shuffle=True
    )

    long_name = f"Unbiased Root Mean Square Error for Snow Cover Fraction {labeldict[inputVarName]}"

    #Define attributes
    sev.standard_name   = (f"{standard_name[inputVarName]} standard_error")
    sev.long_name       = long_name
    sev.units           = "%"  #"percent"
    sev.missing_value   = missing

    # avoid dangling grid_mapping attribute
    if "spatial_ref" in ds_o4m_raw.variables:
        sev.grid_mapping = 'spatial_ref'

    # Original attributes in original order
    attrs = dict(ds_o4m.attrs)

    # Change existing attributes
    attrs['title'] = new_title
    attrs['variable_id'] = unc_id
    attrs['creation_date'] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    attrs['tracking_id'] = str(uuid.uuid4())
    attrs['summary'] = (
        f'The product uncertainty for observed land pixels is provided as '
        f'unbiased RMSE per pixel for information on {uncdict[inputVarName]}. '
        f'Clouds are masked.'
    )
    attrs['long_name'] = long_name


    attrs['comment'] = (
        f'{new_comment}; {old_comment}'
        if old_comment
        else new_comment
    )

    # Delete unwanted attributes
    for attr in ['aux_uncertainty_id', 'has_aux_unc']:
        attrs.pop(attr, None)

    # Write all attributes in preserved order
    nc.setncatts(attrs)

    # WRITE UNCERTAINTY

    log(f'Number of files to process : {len(time_ds.values)}')

    for it, date in enumerate(pd.to_datetime(time_ds.values).normalize()):
        date_start = time.perf_counter()
        scf2d = np.squeeze(ds_o4m[variable_id].isel(time=it).values)
        valid = np.isfinite(scf2d)
        valid &= (scf2d >= 0) & (scf2d <= 100)

        file = Path(input_files.format(
            year=date.year,
            month=f'{date.month:02d}',
            date=date.strftime('%Y%m%d')
        )).resolve()

        if file.is_file():
            log(f'[INFO {date}] Read layer {layer_input}: {file}')

            with xr.open_dataset(file) as ds_se:
                if layer_input not in ds_se.variables:
                    available_vars = list(ds_se.data_vars)
                    raise ValueError(
                        f"Variable '{layer_input}' not found in file: {file}. "
                        f"Available data variables: {available_vars}"
                    )
                se2d  = np.squeeze(ds_se[layer_input].values).astype(np_dtype)

                # check array shape
                if se2d.shape != (len(ds_se["lat"]), len(ds_se["lon"])):
                    raise ValueError(
                        f"Unexpected shape for {layer_input} in {file}: "
                        f"{se2d.shape}, expected {(len(ds_se['lat']), len(ds_se['lon']))}"
                    )
                
                # read source latitude to validate orientation
                lat_se = ds_se["lat"].values  
                target_lat = lat_raw.values  
                if np.allclose(lat_se, target_lat, rtol=0, atol=1e-6):  
                    pass  
                elif np.allclose(lat_se[::-1], target_lat, rtol=0, atol=1e-6):  
                    se2d = se2d[::-1, :]  # flip latitude if source is reversed
                else:  
                    raise ValueError(f"Latitude grid does not match obs4MIPs input: {file}")  


                lon_se = ds_se["lon"].values
                target_lon = lon_raw.values  
                # choose longitude convention from target grid
                if target_lon.min() >= 0:  
                    lon_se_cmp = np.mod(lon_se, 360)  
                else:  
                    lon_se_cmp = ((lon_se + 180) % 360) - 180  
                
                order = np.argsort(lon_se_cmp)
                se2d = se2d[:, order]
                lon_se_sorted = lon_se_cmp[order] 

                # check
                if not np.allclose(lon_se_sorted, target_lon, rtol=0, atol=1e-6):  
                    raise ValueError(f"Longitude grid does not match obs4MIPs input: {file}")

            duration = f'{time.perf_counter() - date_start:.2f}'
            log(f'[INFO {date}] Duration: {duration} sec')

        else:
            log(f'    WARNING: no uncertainty file found for {date:%Y-%m-%d}')
            se2d = np.full(
                (nlat, nlon), 
                missing, 
                dtype=np_dtype
                )

        # Remove flagedded values
        se2d[~valid] = missing
        se2d[se2d < 0] = missing

        sev[it, :, :] = se2d

    #Close output file
    nc.close()
    ds_o4m.close()
    ds_o4m_raw.close()

total_duration = f'{time.perf_counter() - total_start:.2f}'
log(f'[INFO] Duration: {total_duration} sec')
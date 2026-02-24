#writes out standard deviation data file for the snow cci SWE data

import xarray as xr
import numpy as np
import glob, os
from datetime import datetime
import cftime
import pandas as pd
import uuid
from netCDF4 import Dataset

#output directory
outdir='./obs4MIPs/FMI/CCI-SWE-v4-0/day/sweLut/gn/v20260108_sd/'

#read in swe obs4mips files
obs4mips_file = './obs4MIPs/FMI/CCI-SWE-v4-0/day/sweLut/gn/v20260108/sweLut_day_CCI-SWE-v4-0_FMI_gn_19790101-20231231.nc'

#read in with xarray
#ds_swe = xr.open_dataset(obs4mips_file)
ds_swe = xr.open_dataset(
    obs4mips_file,
    chunks={"time": 1}   
)

time = ds_swe.time
lat  = ds_swe.lat
lon  = ds_swe.lon
nlat = lat.size
nlon = lon.size
ntime = time.size

#read the individual data files
input_dir = '/mnt/c/Users/venalaip/OneDrive - Ilmatieteen laitos/Documents/MATLAB/CCI_SWE_datasets/NetCDF/snow_cci_v4/'
input_path = input_dir+'*.nc'

#get filelist
filelist = glob.glob(input_path)
print('Number of files to process:',len(filelist))

#Create a map of date to file name
sd_map = {}
for f in filelist:
    fname = os.path.basename(f)
    date_str = fname.split("-")[0] 
    sd_map[pd.to_datetime(date_str)] = f

#Create output NetCDF file
os.makedirs(outdir, exist_ok=True)

outfile = (
    outdir +
    "sdsweLut_day_CCI-SWE-v4-0_FMI_gn_19790101-20231231.nc"
)

nc = Dataset(outfile, "w", format="NETCDF4_CLASSIC")
nc.createDimension("time", None)
nc.createDimension("lat", nlat)
nc.createDimension("lon", nlon)


#Define coordinate variables
latv = nc.createVariable("lat", "f4", ("lat",))
lonv = nc.createVariable("lon", "f4", ("lon",))
timev = nc.createVariable("time", "f8", ("time",))


latv[:] = lat.values
lonv[:] = lon.values
latv.units = lat.units
lonv.units = lon.units
timev.units = time.encoding.get("units", "days since 1950-01-01")
timev.calendar = time.encoding.get("calendar", "gregorian")

#Define standard deviation variable
sdv = nc.createVariable(
    "sweLut_standard_deviation",
    "f4",
    ("time", "lat", "lon"),
    fill_value=1.0e20,
    zlib=True,
    complevel=1,
    shuffle=True
)

sdv.units = "m"
sdv.long_name = "Standard deviation of snow water equivalent"
sdv.standard_name = (
    "lwe_thickness_of_surface_snow_amount standard_deviation"
)

#Set global attributes
for k, v in ds_swe.attrs.items():
    setattr(nc, k, v)

nc.title = "Snow water equivalent: standard deviation"
nc.variable_id = "sdSweLut"
nc.comment = "Ancillary standard deviation for the SWE obs4MIPs product"
nc.creation_date = datetime.now().isoformat()
nc.tracking_id = str(uuid.uuid4())

# Base time for numeric conversion
base_time = cftime.DatetimeGregorian(1950, 1, 1, 0, 0, 0)
time_days = (pd.to_datetime(time.values) - pd.Timestamp("1950-01-01")).days
timev[:] = time_days

#Loop over time and read standard deviation data
print('Writing standard deviation data to file:',outfile)
for it, t in enumerate(pd.to_datetime(time.values)):
    #swe2d = ds_swe["sweLut"].isel(time=it).values
    swe2d = np.squeeze(ds_swe["sweLut"].isel(time=it).values)
    valid = np.isfinite(swe2d)

    if t in sd_map:
        ds_sd = xr.open_dataset(sd_map[t])
        sd2d = np.squeeze(ds_sd["swe_std"].values).astype("float32") / 1000.0 # mm → m

        # Reorder longitudes (-180..180 → 0..360)
        lon_sd = ds_sd["lon"].values
        lon_sd_0360 = np.mod(lon_sd, 360)
        order = np.argsort(lon_sd_0360)
        sd2d = sd2d[:, order]

        ds_sd.close()
    else:
        sd2d = np.full((nlat, nlon), np.nan, dtype="float32")

    # Remove flagedded values
    sd2d[~valid] = np.nan
    sd2d[sd2d < 0] = np.nan

    sdv[it, :, :] = sd2d

#Close output file
nc.close()
ds_swe.close()

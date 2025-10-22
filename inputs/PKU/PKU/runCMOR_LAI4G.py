# Author: Sen Cao (sencao@pku.edu.cn)
# Date: 2025-04-25 21:56:57
# LastEditors: Sen Cao (sencao@pku.edu.cn)
# LastEditTime: 2025-05-14 12:06:08
# FilePath: /obs4MIPs-cmor/LAI4g_for_obs4MIPs.py
# Description: This script converts GIMMS LAI4g version 1.2 available at
#             https://zenodo.org/records/8281930 to a format required by obs4MIPs using CMOR under linux.
#             Original half-month records in 1/12 degree have been converted to monthly averages in 0.1 degree
#             Scripts modified from https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/demo/runCMORdemo_CMAP-V1902.py

# This script is available under Creative Commons Attribution 4.0 International, 
# which allows re-distribution and re-use of a licensed work on the condition that 
# the creator is appropriately credited


import cmor
import xarray as xr
import xcdat
import numpy as np
import sys,os
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject
import pandas as pd
from datetime import datetime
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root_dir, "inputs","misc"))
import obs4MIPsLib

print('Start:', datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))

cmorTable = os.path.join(root_dir,'Tables','obs4MIPs_Lmon.json')
inputJson = 'Input_table_LAI4g.json'
outputVarName = 'lai'
outputUnits = 'm2 m-2'

# LAI4g GEOTIFF folders
LAI4g_folder = 'GIMMS_LAI4g_AVHRR_MODIS_consolidated'
sub_folders = ['GIMMS_LAI4g_AVHRR_MODIS_consolidated_1982_1990',
               'GIMMS_LAI4g_AVHRR_MODIS_consolidated_1991_2000',
               'GIMMS_LAI4g_AVHRR_MODIS_consolidated_2001_2010',
               'GIMMS_LAI4g_AVHRR_MODIS_consolidated_2011_2020']

# function-resample a GeoTIFF file and return the data
def geotiff_resample(tiff_file, target_reso = 0.1):
    # Read metadata to get the target CRS
    with rasterio.open(tiff_file) as src:
        src_crs = src.crs
        src_transform = src.transform
        src_width = src.width
        src_height = src.height

    # Calculate target width/height based on original bounds
    with rasterio.open(tiff_file) as src:
        left, bottom, right, top = src.bounds
        target_width = int((right - left) / target_reso)
        target_height = int((top - bottom) / target_reso)

    # Target transform (affine transformation matrix)
    target_transform = rasterio.Affine(target_reso, 0, left,0, -target_reso, top)

    # Resample
    with rasterio.open(tiff_file) as src:
        LAI = src.read(1).astype(np.single)
        LAI[LAI==65535] = np.nan

        # Create a destination array for reprojection
        LAI_re = np.zeros((target_height, target_width), dtype=np.single)

        # Reproject & resample to 0.1° (ignores NaN values)
        reproject(
            source=LAI,
            destination=LAI_re,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_transform,
            dst_crs=src_crs,
            resampling=Resampling.bilinear
        )

        return LAI_re

# function-convert a single GeoTIFF file to an xarray DataArray
def half_month_geotiff_to_monthly_xarray(tiff_file_1, tiff_file_2):
    reso = 0.1
    
    # resample the tiff files to 0.1 degree (10 km), one of defined values by obs4MIPs_CV.json
    LAI_re_1 = geotiff_resample(tiff_file_1, target_reso = reso)
    LAI_re_2 = geotiff_resample(tiff_file_2, target_reso = reso)

    # Create coordinates
    lat = np.arange(90-reso/2, -90, -reso)
    lon = np.arange(reso/2, 360, reso)

    # prcoess the two half-month records to monthly average
    LAI_mean = np.nanmean([LAI_re_1,LAI_re_2], axis=0)
    LAI_mean = LAI_mean * 0.001

    # process nan value
    LAI_mean = np.nan_to_num(LAI_mean,nan=9999)

    # roll the data by 180 degree
    LAI_mean_roll = np.roll(LAI_mean, shift=LAI_mean.shape[1] // 2, axis=1)

    # Create DataArray
    LAI_da = xr.DataArray(
        LAI_mean_roll,
        dims=("lat", "lon"),
        coords={"lat": lat, "lon": lon},
        attrs={
            "description": f"{os.path.basename(tiff_file_1)[17:23]}"
        },
    )
    # Create the Dataset
    dataset = xr.Dataset({"lai": LAI_da})

    return dataset

# read all LAI4g records in the data folder to a list
data_arrays = []
ref_time = datetime(1800, 1, 1, 0, 0, 0)
times = []
for year in range(1982, 2021):
    # find the sub folder based on year
    if year <= 1990:
        sub_folder = sub_folders[0]
    elif year <= 2000:
        sub_folder = sub_folders[1]
    elif year <= 2010:
        sub_folder = sub_folders[2]
    else:
        sub_folder = sub_folders[3]

    for month in range(1,13):
            print(year, month)
            # read geotiff file to list
            tiff_file_1 = 'GIMMS_LAI4g_V1.2_' + f"{year:04d}" + f"{month:02d}" + "01" + '.tif'
            tiff_file_1 = os.path.join(root_dir, LAI4g_folder, sub_folder, tiff_file_1)
            tiff_file_2 = 'GIMMS_LAI4g_V1.2_' + f"{year:04d}" + f"{month:02d}" + "02" + '.tif'
            tiff_file_2 = os.path.join(root_dir, LAI4g_folder, sub_folder, tiff_file_2)
            # store for time stamps
            time_str = os.path.basename(tiff_file_1)[17:23]
            year = np.int32(time_str[0:4])
            month = np.int32(time_str[4:])
            time = datetime(year, month, 16, 0, 0, 0)
            delta_time = time - ref_time
            times.append(np.round(np.single(delta_time.total_seconds()) / 3600 / 24))
            data_arrays.append(half_month_geotiff_to_monthly_xarray(tiff_file_1, tiff_file_2))

# Combine all DataArrays into a single xarray Dataset, and add time coordinate
times = np.array(times)
combined_dataset = xr.concat(data_arrays, dim="time")
combined_dataset = combined_dataset.assign_coords(time=("time", times, {"units": "days since 1800-01-01 00:00:0.0"}))

# get attributes of the dataset
lat = combined_dataset.lat.values
lon = combined_dataset.lon.values
time = combined_dataset.time.values
f = combined_dataset.bounds.add_bounds("T").bounds.add_bounds("Y").bounds.add_bounds("X")
tbds = f.time_bnds.values
latbds = f.lat_bnds.values
# lonbds = f.lon_bnds.values
# mannual calculation for accuracy, as required by cmor.axis
lonbds = np.single([np.array([l-0.05,l+0.05]) for l in lon])
lonbds[-1,1] = 360

# Initialize and run CMOR
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f'Created on {pd.Timestamp.now()}')

# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat, cell_bounds=latbds, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=lon, cell_bounds=lonbds, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=time, cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorLat, cmorLon]

# Setup units and create variable to write using cmor
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=9999)
values = np.array(combined_dataset['lai'],np.float32)[:]

# Append valid_min and valid_max to variable before writing using cmor
cmor.set_variable_attribute(varid,'valid_min','f',0.0)
cmor.set_variable_attribute(varid,'valid_max','f',7.0)

# Prepare variable for writing, then write and close file
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid, values,len(time)) 
cmor.close()
f.close()

print('Finish:', datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))



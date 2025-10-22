import os
import numpy as np
import pandas as pd
import xarray as xr
import cmor
import json
import logging
import warnings
import s3fs
import obs4MIPsLib 
warnings.filterwarnings("ignore", category=UserWarning, message=".*tight_layout.*")

# Config

BUCKET = "noaa-cdr-leaf-area-index-fapar-pds"
PREFIX = "data"
#OUTPUT_DIR = "./obs4mips_lai_files"
YEARS = range(1981, 2025)


# Setup

s3 = s3fs.S3FileSystem(anon=True)
#os.makedirs(OUTPUT_DIR, exist_ok=True)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("lai_processing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)



# Utilities

def list_daily_files(year):
    """
    List all NetCDF daily LAI files for a specific year from the public S3 bucket.

    Parameters:
        year (int): Year to list files for (e.g., 1981)

    Returns:
        List[str]: List of full S3 paths to NetCDF files
    """
    path = f"{BUCKET}/{PREFIX}/{year}"
    try:
        files = [f for f in s3.ls(path) if f.endswith(".nc")]
        logger.debug(f"Found {len(files)} files for {year}")
        return files
    except Exception as e:
        logger.error(f"Could not list files for {year}: {e}")
        return []


def load_and_filter_file(s3_path):
    """
    Load a single NetCDF file from S3 and apply QA filtering to retain only valid LAI values.

    Parameters:
        s3_path (str): Full S3 path to the NetCDF file

    Returns:
        xarray.DataArray or None: Filtered LAI array with variable renamed to 'lai', or None if error occurs
    """
    try:
        with s3.open(s3_path) as f:
            ds = xr.open_dataset(f)
            valid_mask = (ds["QA"] & 0x0003) == 0x0000
            lai_filtered = ds["LAI"].where(valid_mask)
            lai_filtered.name = "lai"
            logger.debug(f"Loaded and filtered {s3_path}")
            return lai_filtered
    except Exception as e:
        logger.warning(f"Failed to load/filter {s3_path}: {e}")
        return None


def convert_lon_180_to_360(ds):
    """
    Convert longitudes from [-180, 180] to [0, 360) and reorder latitude to be ascending.

    Parameters:
        ds (xarray.Dataset): Input dataset with 'LAI', 'latitude', and 'longitude'

    Returns:
        xarray.Dataset: Dataset with remapped 'lon' and reordered 'lat'
    """
    
    ds = ds.copy()
    ds = ds.rename({ "latitude": "lat", "longitude": "lon"})
    if "QA" in ds:
        ds = ds.drop_vars("QA")
        
    ds["lai"] = ds["lai"].astype("float32")
    ds["lon"] = ((ds["lon"] + 360) % 360).astype("float64")
    ds["lat"] = ds["lat"].astype("float64")

    
    # Clip latitudes to valid range
    ds["lat"] = ds["lat"].clip(min=-90.0, max=90.0)

    if not np.all(np.diff(ds["lat"].values) > 0):
        ds = ds.sortby("lat")

    # Sort lon (ascending)
    if not np.all(np.diff(ds["lon"].values) > 0):
        ds = ds.sortby("lon")
    
    return ds


def compute_lat_lon_bounds(lat, lon):
    lat = np.asarray(lat)
    lon = np.asarray(lon)

    # Latitude bounds
    lat_edges = np.zeros(lat.size + 1)
    lat_edges[1:-1] = (lat[:-1] + lat[1:]) / 2
    lat_edges[0] = lat[0] - (lat[1] - lat[0]) / 2
    lat_edges[-1] = lat[-1] + (lat[-1] - lat[-2]) / 2
    lat_edges = np.clip(lat_edges, -90, 90)
    lat_bnds = np.column_stack((lat_edges[:-1], lat_edges[1:]))

    # Longitude bounds
    lon_edges = np.zeros(lon.size + 1)
    lon_edges[1:-1] = (lon[:-1] + lon[1:]) / 2
    lon_edges[0] = lon[0] - (lon[1] - lon[0]) / 2
    lon_edges[-1] = lon[-1] + (lon[-1] - lon[-2]) / 2
    lon_edges = np.clip(lon_edges, 0, 360)
    lon_bnds = np.column_stack((lon_edges[:-1], lon_edges[1:]))

    return lat_bnds, lon_bnds


def compute_time_bounds(times, time_origin="1850-01-01"):
    base = pd.Timestamp(time_origin)
    bounds = []
    for t in pd.to_datetime(times):
        start = t.replace(day=1)
        end = (start + pd.offsets.MonthEnd(1))
        start_days = (start - base).days
        end_days = (end - base).days
        bounds.append([start_days, end_days])
    return np.array(bounds), f"days since {time_origin}"

def process_year(year, inputJson):
    logger.info(f"Starting processing for year {year}")
    file_paths = list_daily_files(year)

    if not file_paths:
        logger.warning(f"No NetCDF files found for year {year}")
        return

    lai_daily = []

    for path in file_paths:
        lai = load_and_filter_file(path)
        if lai is not None:
            lai_daily.append(lai)

    if not lai_daily:
        logger.warning(f"No valid LAI data after filtering for {year}")
        return

    # Combine and compute monthly average
    lai_combined = xr.concat(lai_daily, dim="time").sortby("time")
    monthly_avg = lai_combined.resample(time="1MS").mean()
    monthly_avg = monthly_avg.copy(deep=True)
    monthly_avg["time"] = monthly_avg["time"] + pd.Timedelta(days=14)

    # Prepare Dataset
    ds_monthly = xr.Dataset({"lai": monthly_avg})
    ds_monthly = convert_lon_180_to_360(ds_monthly)

    # Extract axes
    lat = ds_monthly.lat.values
    lon = ds_monthly.lon.values
    time = ds_monthly.time.values
    d = ds_monthly["lai"]

    # Compute bounds
    lat_bnds, lon_bnds = compute_lat_lon_bounds(lat, lon)
    time_bnds, time_units = compute_time_bounds(time)

    # Replace NaNs with fill value
    d_values = np.where(np.isnan(d.values), 1e20, d.values.astype(np.float32))

    # Step 1: Initialize CMOR
    cmor.setup(inpath="./", netcdf_file_action=cmor.CMOR_REPLACE_4)

    # Step 2: Load dataset metadata
    cmor.dataset_json(inputJson)

    # Step 3: Load coordinate table
    cmor.load_table("../Tables/obs4MIPs_coordinate.json")

    # Step 4: Load main variable table
    cmorTable = "../Tables/obs4MIPs_Lmon.json"
    cmorTableId = cmor.load_table(cmorTable)


    # CMOR setup

    cmor.set_cur_dataset_attribute("history", d.attrs.get("history", "Created via CMOR"))

    # Define CMOR axes
    cmorLat = cmor.axis("latitude", coord_vals=lat, cell_bounds=lat_bnds, units="degrees_north")
    cmorLon = cmor.axis("longitude", coord_vals=lon, cell_bounds=lon_bnds, units="degrees_east")
    cmorTime = cmor.axis("time", coord_vals=(time - np.datetime64("1850-01-01")).astype("timedelta64[D]").astype(int),
                         cell_bounds=time_bnds, units=time_units)
    cmorAxes = [cmorTime, cmorLat, cmorLon]

    # Create CMOR variable
    varid = cmor.variable("lai", "1", cmorAxes, missing_value=1e20)
    cmor.set_variable_attribute(varid, 'valid_min', 'f', 0.0)
    cmor.set_variable_attribute(varid, 'valid_max', 'f', 10.0)  # adjust if needed

    # Provenance
    #gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
    #gitpath = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"
    #cmor.set_cur_dataset_attribute("processing_code_location", gitpath)
    cmor.set_cur_dataset_attribute("processing_code_location", "https://gitlab.cicsnc.org/cdr-dashboard/cdr_dashboard")


    # Compression + Write
    cmor.set_deflate(varid, 1, 1, 1)
    cmor.write(varid, d_values, len(time))
    cmor.close()
    logger.info(f"Finished writing CMOR-compliant NetCDF for {year}")


if __name__ == "__main__":
    for year in YEARS:
        try:
            if year <= 2013:
                input_json = "input_avhrr.json"
            else:
                input_json = "input_viirs.json"
            process_year(year, input_json)
        except Exception as e:
            logger.error(f"Failed to process year {year}: {e}")


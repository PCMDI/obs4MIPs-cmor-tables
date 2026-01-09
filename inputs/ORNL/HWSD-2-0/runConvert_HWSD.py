import datetime
import os
import sqlite3
import subprocess
import warnings
from pathlib import Path

import cftime as cf
import numpy as np
import pandas as pd
import rioxarray as rxr
import xarray as xr
from dask.distributed import Client, LocalCluster
from osgeo import gdal

# Determine the parent directory (ILAMB-DATA)
from ilamb3_data import (
    create_output_filename,
    gen_trackingid,
    gen_utc_timestamp,
    get_cmip6_variable_info,
    set_coord_bounds,
    set_lat_attrs,
    set_lon_attrs,
    set_ods_global_attrs,
    set_time_attrs,
    set_var_attrs,
    standardize_dim_order,
)

#####################################################
# set parameters
#####################################################

# main parameters
VAR = "cSoil"
# VAR = "cSoilAbove1m"
LAYERS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7"]  # cSoil
# LAYERS = ["D1", "D2", "D3", "D4", "D5"]  # cSoilAbove1m
POOLS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # soil types
SDATE = datetime.datetime(1960, 1, 1)
EDATE = datetime.datetime(2022, 1, 1)

# dask parameters -- adjust these to fit your computer's capabilities
# chatgpt can optimize n_workers, n_threads, and mem_limit if you provide your computer specs!
CHUNKSIZE = 3000
N_WORKERS = 4
N_THREADS = 2
MEM_LIMIT = "16GB"

# paths to files
REMOTE_RAST = (
    "https://s3.eu-west-1.amazonaws.com/data.gaezdev.aws.fao.org/HWSD/HWSD2_RASTER.zip"
)
LOCAL_RAST = "_raw/HWSD2_RASTER/HWSD2.bil"
REMOTE_DATA = "https://www.isric.org/sites/default/files/HWSD2.sqlite"
LOCAL_DATA = "_raw/HWSD2.sqlite"
GITHUB_PATH = "https://github.com/rubisco-sfa/ILAMB-Data/blob/master/HWSD2/convert.py"

# suppress specific warnings
warnings.filterwarnings("ignore", message="invalid value encountered in cast")
gdal.DontUseExceptions()

#####################################################
# functions in the order that they are used in main()
#####################################################


# 1. download raster and sql database to connect to raster
def download_data(remote_rast, remote_data):
    raw_dir = "_raw"
    os.makedirs(raw_dir, exist_ok=True)

    # --- raster ZIP -> _raw/HWSD2_RASTER/ ---
    rast_dir_name = os.path.splitext(os.path.basename(remote_rast))[0]  # "HWSD2_RASTER"
    rast_dir = os.path.join(raw_dir, rast_dir_name)  # "_raw/HWSD2_RASTER"
    os.makedirs(rast_dir, exist_ok=True)

    # already have a .bil in the target dir?
    have_bil = any(fname.endswith(".bil") for fname in os.listdir(rast_dir))
    if not have_bil:
        zip_path = os.path.join(
            raw_dir, os.path.basename(remote_rast)
        )  # "_raw/HWSD2_RASTER.zip"
        subprocess.run(["curl", "-L", remote_rast, "-o", zip_path], check=True)
        subprocess.run(["unzip", "-o", zip_path, "-d", rast_dir], check=True)
    else:
        print(f"Raster already present in {rast_dir}")

    # --- sqlite -> _raw/HWSD2.sqlite ---
    sql_database = os.path.join(
        raw_dir, os.path.basename(remote_data)
    )  # "_raw/HWSD2.sqlite"
    if not os.path.isfile(sql_database):
        subprocess.run(["curl", "-L", remote_data, "-o", sql_database], check=True)
    else:
        print(f"Database already present: {sql_database}")


# 2. initialize the dask multiprocessing client; the link can be used to track worker progress
def initialize_client(n_workers, n_threads, mem_limit):
    cluster = LocalCluster(
        n_workers=n_workers, threads_per_worker=n_threads, memory_limit=mem_limit
    )
    client = Client(cluster)
    print(f"Dask dashboard link: {client.dashboard_link}")
    return client


# 3. load the raster we use to connect with HWSDv2 data
def load_raster(path, chunksize):
    rast = rxr.open_rasterio(
        path,
        band_as_variable=True,
        mask_and_scale=True,
        chunks={"x": chunksize, "y": chunksize},
    )
    rast = (
        rast.astype("int16").drop_vars("spatial_ref").rename_vars(band_1="HWSD2_SMU_ID")
    )
    return rast


# 4. load the table with data from the sqlite database
def load_layer_table(db_path, table_name):
    conn = sqlite3.connect(db_path)
    query = f"SELECT * FROM {table_name}"
    layer_df = pd.read_sql_query(query, conn)
    conn.close()
    return layer_df


# 5(a). function to calculate carbon stock
def calculate_stock(
    df, top_depth, bottom_depth, bulk_density_g_cm3, cf, organic_carbon
):
    thickness_cm = df[bottom_depth] - df[top_depth]
    df["stock"] = (
        (df[bulk_density_g_cm3] * 1000)  # g to kg
        * (1 - df[cf] / 100)
        * (thickness_cm * 0.01)  # cm to meter
        * (df[organic_carbon] / 100)
    )
    return df["stock"]


# 5(b). function to calculate weighted mean
def weighted_mean(values, weights):
    return (values * weights).sum() / weights.sum()


# 5. process each soil layer by selecting the layer & pools of interest,
# removing erroneous negative values, calculating C stock, and getting
# the weighted mean of the pools
def process_layers(layer_df, layers, pools, var):
    dfs = []
    for layer in layers:
        sel = layer_df[
            [
                "HWSD2_SMU_ID",
                "LAYER",
                "SEQUENCE",
                "ORG_CARBON",
                "BULK",
                "BOTDEP",
                "TOPDEP",
                "COARSE",
                "SHARE",
            ]
        ]
        df = sel[sel["LAYER"] == layer].drop(columns=["LAYER"])
        df = df[df["SEQUENCE"].isin(pools)]
        for attr in ["ORG_CARBON", "BULK", "SHARE"]:
            df[attr] = df[attr].where(df[attr] > 0, np.nan)
        df[var] = calculate_stock(
            df, "TOPDEP", "BOTDEP", "BULK", "COARSE", "ORG_CARBON"
        )
        grouped = (
            df.groupby("HWSD2_SMU_ID")
            .apply(
                lambda x: pd.Series({var: weighted_mean(x["stock"], x["SHARE"])}),
                include_groups=False,
            )
            .reset_index()
        )
        dfs.append(grouped)
    return dfs


# 6. combine all the layers by summing, and set the data types
def combine_and_summarize(dfs, var):
    total_df = pd.concat(dfs)
    total_df = total_df.groupby("HWSD2_SMU_ID")[var].agg("sum").reset_index(drop=False)
    total_df["HWSD2_SMU_ID"] = total_df["HWSD2_SMU_ID"].astype("int16")
    total_df[var] = total_df[var].astype("float32")
    return total_df


# 7(a). function to map the soil unit ID to the cSoil variable
def map_uid_to_var(uid, uid_to_var):
    return uid_to_var.get(uid, float("nan"))


# 7. create a variable in the rast dataset containing cSoil data
def apply_mapping(rast, total_df, var):
    uid_to_var = total_df.set_index("HWSD2_SMU_ID")[var].to_dict()
    mapped_orgc = xr.apply_ufunc(
        map_uid_to_var,
        rast["HWSD2_SMU_ID"],
        input_core_dims=[[]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=["float32"],
        kwargs={"uid_to_var": uid_to_var},
    )
    rast = rast.assign({var: mapped_orgc})
    return rast


# 8. save the rast dataset as a tif
def save_raster(rast, var, layers, pools):
    output_path = f"hwsd2_{var}_{layers[0]}-{layers[-1]}_seq{pools[0]}-{pools[-1]}.tif"
    rast[[var]].rio.to_raster(output_path)
    return output_path


# 9. resample the 250m resolution to 0.5deg resolution
def resample_raster(input_path, output_path, xres, yres, interp, nan):
    gdal.SetConfigOption("GDAL_CACHEMAX", "500")
    ds = gdal.Warp(
        output_path,
        input_path,
        xRes=xres,
        yRes=yres,
        resampleAlg=interp,
        outputType=gdal.GDT_Float32,
        dstNodata=nan,
        outputBounds=(-180.0, -90.0, 180.0, 90.0),
    )
    del ds


# 10. create a netcdf of the 0.5deg resolution raster
def create_netcdf(
    input_path, var, local_data, remote_data, sdate, edate, pools, layers
):
    # open the .tif file
    ds = rxr.open_rasterio(input_path, band_as_variable=True, mask_and_scale=True)
    ds = ds.rename({"x": "lon", "y": "lat", "band_1": var})

    # create time dimension
    ds = ds.drop_vars(["spatial_ref"], errors="ignore")
    ds = set_time_attrs(
        ds,
        bounds_frequency="fx",
        ref_date=cf.DatetimeGregorian(sdate.year, sdate.month, sdate.day),
        create_new_time=True,
        sdate=cf.DatetimeGregorian(sdate.year, sdate.month, sdate.day),
        edate=cf.DatetimeGregorian(edate.year, edate.month, edate.day),
    )
    ds = set_lat_attrs(ds)
    ds = set_lon_attrs(ds)
    ds = set_coord_bounds(ds, "lat")
    ds = set_coord_bounds(ds, "lon")
    ds = standardize_dim_order(ds)

    # ensure csoil has time dimension
    ds[var] = ds[var].expand_dims(time=ds.sizes["time"]).assign_coords(time=ds["time"])
    ds["time"].encoding["_FillValue"] = None

    # Set timestamps and tracking id
    download_stamp = gen_utc_timestamp(Path(local_data).stat().st_mtime)
    creation_stamp = gen_utc_timestamp()
    today_stamp = datetime.datetime.now().strftime("%Y%m%d")
    tracking_id = gen_trackingid()

    # get variable attribute info via ESGF CMIP variable information
    info = get_cmip6_variable_info(var)

    # set variable attributes
    ds = set_var_attrs(
        ds,
        var=var,
        cmip6_units=info["variable_units"],
        cmip6_standard_name=info["cf_standard_name"],
        cmip6_long_name=info["variable_long_name"],
        target_dtype=np.float32,
    )

    # create history variable
    history = f"""
{download_stamp}: downloaded source from {remote_data}
{creation_stamp}: filtered data to soil dominance sequence(s) {pools}; where 1 is the dominant soil type
{creation_stamp}: masked invalid negative organic_carbon_pct_wt and bulk_density_g_cm3 with np.nan
{creation_stamp}: calculated cSoilLevels in kg m-2 for each level {layers}: (bulk_density_g_cm3 * 1000) * (1 - coarse_fragment_pct_vol / 100) * (thickness_cm * 0.01) * (organic_carbon_pct_wt / 100)
{creation_stamp}: calculated {var} by getting the weighted mean of all pools in a level and summing {layers} cSoilLevels where levles are 0-20cm (D1), 20-40cm (D2), 40-60cm (D3), 60-80cm (D4), 80-100cm (D5), 100-150cm (D6), 150-200 cm (D7)
{creation_stamp}: resampled to 0.5 degree resolution using mean
{creation_stamp}: created CF-compliant metadata
"""

    # set the attributes
    ds = set_ods_global_attrs(
        ds,
        activity_id="obs4MIPs",
        aux_variable_id="N/A",
        comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
        contact="Matieu Henry (matieu.henry@fao.org)",
        conventions="CF-1.12 ODS-2.5",
        creation_date=creation_stamp,
        dataset_contributor="Morgan Steckler",
        data_specs_version="2.5",
        doi="N/A",
        frequency="fx",
        grid="0.5x0.5 degree latitude x longitude",
        grid_label="gn",
        has_auxdata="False",
        history=history,
        institution="International Institute for Applied Systems Analysis, Laxenburg, Austria; Food and Agriculture Organization of the United Nations, Rome, Italy",
        institution_id="IIASA-FAO",
        license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
        nominal_resolution="0.5x0.5 degree",
        processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/HWSD2/convert.py",
        product="derived",
        realm="land",
        references="Nachtergaele, F. (Ed.),van Velthuizen, H.(Ed.), Verelst, L.(Ed.), Wiberg, D.(Ed.), Henry, M.(Ed.), Chiozza, F.(Ed.), Yigini, Y.(Ed.), Aksoy, E., Batjes, N., Boateng, E., Fischer, G., Jones, A., Montanarella, L., Shi, X., & Tramberend, S. (2023). Harmonized World Soil Database Version 2.0 (Technical Report). FAO & IIASA.",
        region="global_land",
        source="Harmonized international soil profiles from WISE30sec 2015 with 7 soil layers and expanded soil attributes",
        source_id="HWSD-2-0",
        source_data_retrieval_date=download_stamp,
        source_data_url=f"{REMOTE_RAST}; {REMOTE_DATA}",
        source_label="HWSD",
        source_type="gridded_insitu",
        source_version_number="2.0",
        title="Harmonized World Soil Database version 2.0",
        tracking_id=tracking_id,
        variable_id=var,
        variant_label="REF",
        variant_info="CMORized product prepared by ILAMB and CMIP IPO",
        version=f"v{today_stamp}",
    )

    # export as netcdf
    out_path = create_output_filename(ds.attrs)
    ds.to_netcdf(out_path, format="NETCDF4")


# use all nine steps above to convert the data into a netcdf
def main():
    download_data(REMOTE_RAST, REMOTE_DATA)
    client = initialize_client(N_WORKERS, N_THREADS, MEM_LIMIT)
    rast = load_raster(LOCAL_RAST, CHUNKSIZE)
    layer_df = load_layer_table(LOCAL_DATA, "HWSD2_LAYERS")
    dfs = process_layers(layer_df, LAYERS, POOLS, VAR)
    total_df = combine_and_summarize(dfs, VAR)
    rast = apply_mapping(rast, total_df, VAR)
    output_path = save_raster(rast, VAR, LAYERS, POOLS)

    resample_raster(
        output_path,
        f"hwsd2_{VAR}_{LAYERS[0]}-{LAYERS[-1]}_seq{POOLS[0]}-{POOLS[-1]}_resamp.tif",
        0.5,
        0.5,
        "average",
        np.float32(1.0e20),
    )

    create_netcdf(
        f"hwsd2_{VAR}_{LAYERS[0]}-{LAYERS[-1]}_seq{POOLS[0]}-{POOLS[-1]}_resamp.tif",
        VAR,
        LOCAL_DATA,
        REMOTE_DATA,
        SDATE,
        EDATE,
        POOLS,
        LAYERS,
    )

    client.close()


if __name__ == "__main__":
    main()

from datetime import datetime
from pathlib import Path

import cftime as cf
import numpy as np
import pandas as pd
import xarray as xr

from ilamb3_data import (
    create_output_filename,
    download_from_html,
    gen_trackingid,
    gen_utc_timestamp,
    set_coord_bounds,
    set_depth_attrs,
    set_lat_attrs,
    set_lon_attrs,
    set_ods_global_attrs,
    set_time_attrs,
    set_var_attrs,
    standardize_dim_order,
)

# Download source
remote_source = "https://www.ncei.noaa.gov/data/oceans/woa/DATA_ANALYSIS/3M_HEAT_CONTENT/NETCDF/heat_content/heat_content_anomaly_0-2000_yearly.nc"  # Redirected from: https://www.ncei.noaa.gov/access/global-ocean-heat-content/heat_global.html
local_source = Path("_raw")
local_source.mkdir(parents=True, exist_ok=True)
source = local_source / Path(remote_source).name
if not source.is_file():
    download_from_html(remote_source, str(source))

# Set timestamps and tracking id
download_stamp = gen_utc_timestamp(source.stat().st_mtime)
creation_stamp = gen_utc_timestamp()
today_stamp = datetime.now().strftime("%Y%m%d")
tracking_id = gen_trackingid()

# Load the dataset for adjustments
ds = xr.open_dataset(source, decode_times=False, engine="netcdf4")

# Convert "months since" to "days since" for cftime decoding
time_units = ds["time"].attrs.get("units") or ds["time"].encoding.get("units")
calendar = "standard"  # found using CLI `cdo -s sinfo <file>`
origin_str = time_units.split("since", 1)[-1].strip()
origin_ts = pd.Timestamp(origin_str)

# Build new reference date string for cftime
ref_cf = cf.DatetimeGregorian(
    origin_ts.year,
    origin_ts.month,
    origin_ts.day,
    origin_ts.hour,
    origin_ts.minute,
    origin_ts.second,
    origin_ts.microsecond,
)

# Convert each value m (in months) to exact days since origin:
time_days = [
    int((origin_ts + pd.DateOffset(months=int(m)) - origin_ts).days)
    for m in ds["time"].values
]
ds = ds.assign_coords(time=("time", time_days))
ds["time"].attrs["units"] = f"days since {origin_str}"
ds["time"].attrs["calendar"] = calendar

# propery decode times
time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
ds = xr.decode_cf(ds, decode_times=time_coder)

##########################################################################################
# ohc
##########################################################################################

# Set global ohc and ohc_error
ds["ohc"] = ds["yearl_h22_WO"].rename("ohc")
ds["ohc"] = (ds["ohc"] * 10).astype(np.float64)
ds["ohc_se"] = ds["yearl_h22_se_WO"].rename("ohc_se")
ds["ohc_se"] = (ds["ohc_se"] * 10).astype(np.float64)

# Set ohc variable attrs
ds = set_var_attrs(
    ds,
    var="ohc",
    cmip6_units="ZJ",
    cmip6_standard_name="ocean_heat_content_anomaly",
    cmip6_long_name="global annual ocean (0-2000m depth) heat content anomaly (WOA09 1955-2006 baseline)",
    ancillary_variables="ohc_se",
    cell_methods=None,
    target_dtype=np.float64,
    convert=False,
)

# Set ancillary variables attrs
ds["ohc_se"].attrs = {
    "standard_name": "ocean_heat_content_anomaly standard_error",
    "units": "ZJ",
}
ds["ohc_se"].encoding = {"_FillValue": None}

##########################################################################################
# ohc_Jm2
##########################################################################################

# Compute cell area
radius = ds.crs.semi_major_axis
lat_bnds = np.deg2rad(ds.lat_bnds.values)  # (lat,2)
lon_bnds = np.deg2rad(ds.lon_bnds.values)  # (lon,2)
delta_phi = np.sin(lat_bnds[:, 1]) - np.sin(lat_bnds[:, 0])
delta_lon = lon_bnds[:, 1] - lon_bnds[:, 0]
area_2d = (radius**2) * delta_phi[:, None] * delta_lon[None, :]  # (lat,lon)
cell_area = xr.DataArray(
    area_2d,
    dims=("lat", "lon"),
    coords={"lat": ds.lat, "lon": ds.lon},
    name="cell_area",
)

# Convert to 4D (add back time and depth)
hc_J = ds["h18_hc"].astype("float32") * 1e18
area_4d = cell_area.broadcast_like(hc_J.isel(time=0, depth=0))
area_4d = area_4d.expand_dims({"time": hc_J.time, "depth": hc_J.depth}, axis=(0, 1))

# Compute J m-2
ohcJm2 = (hc_J / area_4d).astype("float32")
ds["ohcJm2"] = ohcJm2

# Set ohc_Jm2 variable attrs
ds = set_var_attrs(
    ds,
    var="ohcJm2",
    cmip6_units="J m-2",
    cmip6_standard_name="integral_wrt_depth_of_sea_water_potential_temperature_expressed_as_heat_content",
    cmip6_long_name="depth-integrated ocean heat content anomaly (WOA09 1955-2006 baseline) computed as the integral over depth of sea water (0-2000m) potential temperature",
    ancillary_variables=None,
    cell_methods="area: mean depth: mean time: mean",  # this came from the original dataset, so I'll keep it
    target_dtype=np.float32,
    convert=False,
)

# Clean up attrs
ds = set_time_attrs(ds, bounds_frequency="Y")
ds = set_lat_attrs(ds)
ds = set_lon_attrs(ds)
ds = set_depth_attrs(
    ds,
    bounds=np.array([[0, 2000]]),
    units="meters",
    positive="down",
    long_name="depth of sea water",
)
ds = set_coord_bounds(ds, "lat")
ds = set_coord_bounds(ds, "lon")

# global temporal mean of ohcJm2
anomaly_per_cell = ohcJm2 * cell_area  # per-cell anomaly
global_ohc_J = anomaly_per_cell.sum(dim=("lat", "lon"))  # global ocean anomaly
global_ohc_ZJ = global_ohc_J * 1e-21  # J to ZJ
ohc_climatology_ZJ = global_ohc_ZJ.mean(
    dim=("time", "depth")
)  # mean of time/depth (there's only 1 depth)

# temporal mean of ohc
mean_ohc = ds["ohc"].mean()
print(f"Global OHC (from ohcJm2): {ohc_climatology_ZJ:.3e} ZJ")
print(f"Global OHC (from ohc)   : {mean_ohc:.3e} ZJ")

# Create one ds per variable
base_vars = [
    "time",
    "time_bnds",
    "lat",
    "lat_bnds",
    "lon",
    "lon_bnds",
    "depth",
    "depth_bnds",
]
for var in ["ohcJm2", "ohc"]:
    # define output datasets
    if var == "ohcJm2":
        out_ds = ds[base_vars + [var]]
        out_ds = standardize_dim_order(out_ds)
        out_ds["time"].encoding = {"_FillValue": None}
    else:
        out_ds = ds[base_vars + [var, "ohc_se"]]
        out_ds = out_ds.drop_dims(["lat", "lon"])
        orig_attrs, orig_encoding = (
            out_ds["depth"].attrs.copy(),
            out_ds["depth"].encoding.copy(),
        )
        # this resets the depth attrs/encoding
        out_ds[[var, "ohc_se"]] = out_ds[[var, "ohc_se"]].expand_dims(
            dim={"depth": ds["depth"]}
        )
        # so I have to set them again
        out_ds["depth"].attrs, out_ds["depth"].encoding = orig_attrs, orig_encoding
        out_ds = standardize_dim_order(out_ds)
        out_ds["time"].encoding = {"_FillValue": None}

    # Define varibable-dependant attributes
    ohc_title = "WOA23 global yearly mean ocean heat content (0-2000m) anomaly (WOA09 1955-2006 anomaly baseline) from in-situ profile data"
    ohc_jm2_title = "WOA23 depth-integrated ocean heat content anomaly (WOA09 1955-2006 baseline) computed as the integral over depth of sea water (0-2000m) potential temperature"
    dynamic_attrs = {
        "title": f"{ohc_title if var == 'ohc' else ohc_jm2_title}",
        "grid": f"{'1x1 degree latitude x longitude' if var == 'ohcJm2' else 'global mean data'}",
        "grid_label": f"{'gm' if var == 'ohc' else 'gn'}",
        "nominal_resolution": f"{'1x1 degree' if var == 'ohcJm2' else 'site'}",
        "aux_variable_id": f"{'ohc_se' if var == 'ohc' else 'N/A'}",
        "has_auxdata": f"{'True' if var == 'ohc' else 'False'}",
    }

    # Set global attributes
    out_ds = set_ods_global_attrs(
        out_ds,
        activity_id="obs4MIPs",
        aux_variable_id=dynamic_attrs["aux_variable_id"],
        comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
        contact="NOAA National Centers for Environmental Information (ncei.info@noaa.gov)",
        conventions="CF-1.12 ODS-2.5",
        creation_date=creation_stamp,
        dataset_contributor="Morgan Steckler",
        data_specs_version="2.5",
        doi="N/A",
        external_variables="N/A",
        frequency="yr",
        grid=dynamic_attrs["grid"],
        grid_label=dynamic_attrs["grid_label"],
        has_auxdata=dynamic_attrs["has_auxdata"],
        history=f"""
    {download_stamp}: downloaded {remote_source};
    {creation_stamp}: converted to obs4MIPs format""",
        institution="National Oceanic and Atmospheric Administration, National Centers for Environmental Information, Ocean Climate Laboratory, Asheville, NC, USA",
        institution_id="NOAA-NCEI-OCL",
        license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
        nominal_resolution=dynamic_attrs["nominal_resolution"],
        processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/NOAA/convert.py",
        product="observations",
        realm="ocean",
        references="S. Levitus, J. I. Antonov, T. P. Boyer, O. K. Baranova, H. E. Garcia, R. A. Locarnini, A. V. Mishonov, J. R. Reagan, D. Seidov, E. S. Yarosh, M. M. Zweng, World ocean heat content and thermosteric sea level change (0-2000 m), Geophysical Research Letters. 1955-2010. 10.1029/2012GL051106",
        region="global_ocean",
        source="WOA23 yearly mean ocean heat content anomaly from in-situ profile data",
        source_id="WOA-23",
        source_data_retrieval_date=download_stamp,
        source_data_url=remote_source,
        source_label="WOA",
        source_type="gridded_insitu",
        source_version_number="1.0",
        title=dynamic_attrs["title"],
        tracking_id=tracking_id,
        variable_id=var,
        variant_label="REF",
        variant_info="CMORized product prepared by ILAMB and CMIP IPO",
        version=f"v{today_stamp}",
    )

    # Prep for export
    out_path = create_output_filename(out_ds.attrs)
    out_ds.to_netcdf(out_path, format="NETCDF4")

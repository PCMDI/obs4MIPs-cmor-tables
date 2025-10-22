import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr

from ilamb3_data import (
    create_output_filename,
    gen_trackingid,
    gen_utc_timestamp,
    get_cmip6_variable_info,
    set_depth_attrs,
    set_lat_attrs,
    set_ods_global_attrs,
    set_time_attrs,
    set_var_attrs,
    standardize_dim_order,
)

# Follow link to download source; it cannot be downloaded automatically
# Select "MOC transports in NetCDF format" for download
remote_source = "https://rapid.ac.uk/data/data-download"
local_source = Path("_raw")
local_source.mkdir(parents=True, exist_ok=True)
source = local_source / "moc_transports.nc"
if not source.is_file():
    print(
        f"NetCDF has not been downloaded. Navigate here ({remote_source}) to request download of 'MOC transports in NetCDF format'"
    )
    sys.exit(1)

# Set timestamps and tracking id
download_stamp = gen_utc_timestamp(source.stat().st_mtime)
creation_stamp = gen_utc_timestamp()
today_stamp = datetime.now().strftime("%Y%m%d")
tracking_id = gen_trackingid()

# Load the dataset for adjustments
time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
ds = xr.open_dataset(source, decode_times=time_coder)

# Create latitude dimension
lat_da = xr.DataArray(
    [26.5], dims=["lat"], name="lat", attrs={"units": "degrees_north"}
)

# Create depth dimension
depth_da = xr.DataArray(
    [0],
    dims=["depth"],
    name="depth",
)

# Assigning the coordinates to the dataset
ds = ds.assign_coords({"lat": lat_da, "depth": depth_da})
print(len(ds.time))

# Get monthly means instead of 12-hourly
ds = ds.resample(time="MS").mean(keep_attrs=True)

# Select data var
ds = ds.drop_vars([v for v in ds.data_vars if v != "moc_mar_hc10"]).rename_vars(
    {"moc_mar_hc10": "msftmz"}
)

# Assign coordinates to data var
ds["msftmz"] = ds["msftmz"].expand_dims({"depth": ds["depth"], "lat": ds["lat"]})

# Set var attrs
var_info = get_cmip6_variable_info("msftmz")
ds = set_var_attrs(
    ds,
    var="msftmz",
    cmip6_units=var_info["variable_units"],
    cmip6_standard_name=var_info["cf_standard_name"],
    cmip6_long_name=var_info["variable_long_name"],
    target_dtype=np.float32,
    convert=False,
)

# Clean up attrs
ds = set_time_attrs(ds, bounds_frequency="M")
ds = set_lat_attrs(ds)
ds = set_depth_attrs(
    ds,
    bounds=np.array([[0, 2000]]),
    units="meters",
    positive="down",
    long_name="depth of sea water",
)

ds = standardize_dim_order(ds)

# Set global attributes and export
out_ds = set_ods_global_attrs(
    ds,
    activity_id="obs4MIPs",
    comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
    contact="Ben Moat (ben.moat@noc.ac.uk)",
    conventions="CF-1.12 ODS-2.5",
    creation_date=creation_stamp,
    dataset_contributor="Morgan Steckler",
    data_specs_version="2.5",
    doi="10.5285/33826d6e-801c-b0a7-e063-7086abc0b9db",
    external_variables="N/A",
    frequency="mon",
    grid="global mean data",
    grid_label="gm",
    has_auxdata="False",
    history=f"""
{download_stamp}: downloaded {remote_source};
{today_stamp}: aggregated 12-hour timeseries to monthly;
{creation_stamp}: converted to obs4MIPs format""",
    institution="National Oceanography Centre, UK",
    institution_id="NOC",
    license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
    nominal_resolution="site",
    processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/RAPID/convert.py",
    product="derived",
    realm="ocean",
    references="Moat, B.I., Smeed, D.A., Rayner, D., Johns, W.E., Smith, R., Volkov, D., Elipot, S., Petit, T., Kajtar, J., Baringer, M.O., Collins, J. (2025). Atlantic meridional overturning circulation observed by the RAPID-MOCHA-WBTS (RAPID-Meridional Overturning Circulation and Heatflux Array-Western Boundary Time Series) array at 26N from 2004 to 2023 (v2023.1a), British Oceanographic Data Centre - Natural Environment Research Council, UK. https://doi.org/10.5285/33826d6e-801c-b0a7-e063-7086abc0b9db",
    region="atlantic_ocean",
    source="Atlantic meridional overturning circulation observed by the RAPID-Meridional Overturning Circulation and Heatflux Array-Western Boundary",
    source_id="RAPID-2023-1a",
    source_data_retrieval_date=download_stamp,
    source_data_url="https://rapid.ac.uk/data/data-download",
    source_label="RAPID",
    source_type="insitu",
    source_version_number="2023.1a",
    title="RAPID AMOC observations (v2023.1a)",
    tracking_id=tracking_id,
    variable_id="msftmz",
    variant_label="REF",
    variant_info="CMORized product prepared by ILAMB and CMIP IPO",
    version=f"v{today_stamp}",
)

# Prep for export
out_path = create_output_filename(out_ds.attrs)
out_ds.to_netcdf(out_path, format="NETCDF4")

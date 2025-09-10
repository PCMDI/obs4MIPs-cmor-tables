from datetime import datetime
from pathlib import Path

import numpy as np
import xarray as xr

from ilamb3_data import (
    create_output_filename,
    download_from_html,
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

# Download the data
remote_sources = [
    f"https://thredds.nci.org.au/thredds/fileServer/ks32/ARCCSS_Data/LORA/v1-0/LORA_v1.0_{year}.nc"
    for year in range(1980, 2013)
]
local_source = Path("_raw")
local_sources = []
for remote_source in remote_sources:
    local_source.mkdir(parents=True, exist_ok=True)
    source = local_source / Path(remote_source).name
    if not source.is_file():
        download_from_html(remote_source, str(source))
    local_sources.append(source)

# Set timestamps and tracking id
download_stamp = gen_utc_timestamp(local_sources[0].stat().st_mtime)
creation_stamp = gen_utc_timestamp()
today_stamp = datetime.now().strftime("%Y%m%d")
tracking_id = gen_trackingid()

# Load the dataset for adjustments
time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
ds = xr.open_mfdataset(local_sources, engine="netcdf4", decode_times=time_coder)

# Get attribute info for mrro
mrro_info = get_cmip6_variable_info("mrro")

# Set correct attribute information for the vars
ds = set_var_attrs(
    ds,
    var="mrro",
    cmip6_units=mrro_info["variable_units"],
    cmip6_standard_name=mrro_info["cf_standard_name"],
    cmip6_long_name=mrro_info["variable_long_name"],
    ancillary_variables="mrro_stddev",
    target_dtype=np.float32,
    convert=True,
)

# Assign ancillary variables
ds = ds.assign(mrro_stdev=(("time", "lat", "lon"), ds.mrro_sd.values))
ds = ds.drop_vars(["mrro_sd"])
ds.mrro_stdev.attrs = {
    "long_name": f"{ds.mrro.attrs['standard_name']} standard_deviation",
    "cell_methods": "area: standard_deviation",  # copied from source data
}
ds.mrro_stdev.encoding = {
    "_FillValue": None,  # CMOR default
    "dtype": "float32",
}

# Clean up attrs
ds = set_time_attrs(ds, bounds_frequency="M")
ds = set_lat_attrs(ds)
ds = set_lon_attrs(ds)
ds = set_coord_bounds(ds, "lat")
ds = set_coord_bounds(ds, "lon")
ds = standardize_dim_order(ds)

# Set global attributes and export
out_ds = set_ods_global_attrs(
    ds,
    activity_id="obs4MIPs",
    aux_variable_id="mrro_stdev",
    comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
    contact="Sanaa Hobeichi (s.hobeichi@student.unsw.edu.au)",
    conventions="CF-1.12 ODS-2.5",
    creation_date=creation_stamp,
    dataset_contributor="Morgan Steckler",
    data_specs_version="2.5",
    doi="10.25914/5b612e993d8ea",
    external_variables="N/A",
    frequency="mon",
    grid="0.5x0.5 degree latitude x longitude",
    grid_label="gn",
    has_auxdata="True",
    history=f"""
{download_stamp}: downloaded {remote_source};
{creation_stamp}: converted to obs4MIPs format""",
    institution="ARC Centre of Excellence for Climate System Science, NSW, Australia",
    institution_id="ARCCSS",
    license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",  # OG license: Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International Public License
    nominal_resolution="50 km",
    processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/LORA/convert.py",
    product="observations",
    realm="land",
    references="Hobeichi, Sanaa, 2018: Linear Optimal Runoff Aggregate v1.0. NCI National Research Data Collection, doi:10.25914/5b612e993d8ea",
    region="global_land",
    source="LORA 1.0 (2018): Linear Optimal Runoff Aggregate",
    source_id="LORA-1-0",
    source_data_retrieval_date=download_stamp,
    source_data_url="https://thredds.nci.org.au/thredds/catalog/ks32/ARCCSS_Data/LORA/v1-0/catalog.html",
    source_label="LORA",
    source_type="gridded_insitu",
    source_version_number="1.0",
    title="Linear Optimal Runoff Aggregate (version v1.0)",
    tracking_id=tracking_id,
    variable_id="mrro",
    variant_label="REF",
    variant_info="CMORized product prepared by ILAMB and CMIP IPO",
    version=f"v{today_stamp}",
)

# Define chunk sizes based on a ~1–3 MB target per chunk
# (float32 → 4 bytes/element; 6×180×360 ≃ 388 800 elements → ~1.5 MB)
chunks = dict(time=6, lat=180, lon=360)
ds_chunked = out_ds.chunk(chunks)
encoding = {}
for var, da in ds_chunked.data_vars.items():
    encoding_copy = da.encoding.copy()
    # only data variables need chunksizes
    if var in ("mrro", "mrro_stdev"):
        encoding_copy["chunksizes"] = tuple(
            chunks.get(dim, da.sizes[dim]) for dim in da.dims
        )
    encoding[var] = encoding_copy

# Prep for export
out_path = create_output_filename(ds_chunked.attrs)
ds_chunked.to_netcdf(out_path, encoding=encoding, format="NETCDF4")

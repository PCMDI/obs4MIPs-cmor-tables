from datetime import datetime
from pathlib import Path

import cftime as cf
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
remote_source = "https://avdc.gsfc.nasa.gov/pub/data/project/WECANN/WECANN_v1.0.nc"
local_source = Path("_raw")
local_source.mkdir(parents=True, exist_ok=True)
local_source = local_source / Path(remote_source).name
if not local_source.is_file():
    download_from_html(remote_source, str(local_source))

# Set timestamps and tracking id
download_stamp = gen_utc_timestamp(local_source.stat().st_mtime)
creation_stamp = gen_utc_timestamp()
today_stamp = datetime.now().strftime("%Y%m%d")
tracking_id = gen_trackingid()

# Load the dataset for adjustments
orig_ds = xr.open_dataset(local_source)

# Fix the time dimension and add as coordinates
coords = {}
coords["time"] = [
    cf.DatetimeGregorian(int("".join(t[:4])), int("".join(t[-2:])), 15)
    for t in orig_ds["Time"].astype(str).values.T
]

# Latitude and Longitude are 2D but have constant values in opposite dimension
coords["lat"] = orig_ds["Latitude"][0, :].values
coords["lon"] = orig_ds["Longitude"][:, 0].values

# Load the dataarrays, rename to CMOR variables, change dimension order
renaming_dict = {"GPP": "gpp", "H": "hfss", "LE": "hfls"}
data = {
    renaming_dict[v]: orig_ds[v].transpose("t", "lat", "lon").rename(t="time")
    for v in renaming_dict
}

# Make new dataset
ds = xr.Dataset(data_vars=data, coords=coords)

# Get attribute info for gpps, hfss, hfls
vars = list(renaming_dict.values())
var_info = []
for var in vars:
    info = get_cmip6_variable_info(var)
    var_info.append(info)

# Set correct attribute information for the vars
ds.gpp.attrs["Units"] = "g m-2 day-1"
for var, info in zip(vars, var_info):
    ds = set_var_attrs(
        ds,
        var=var,
        cmip6_units=info["variable_units"],
        cmip6_standard_name=info["cf_standard_name"],
        cmip6_long_name=info["variable_long_name"],
        target_dtype=np.float32,
        convert=True,
    )

# Standardize the dimensions
ds = set_time_attrs(ds, bounds_frequency="M")
ds = set_lat_attrs(ds)
ds = set_lon_attrs(ds)
ds = set_coord_bounds(ds, "lat")
ds = set_coord_bounds(ds, "lon")

# Order + var selection
ds = standardize_dim_order(ds)

# Set global attributes and export
for var in vars:
    # Create one ds per variable
    to_drop = [
        v
        for v in ds.data_vars
        if (var not in v) and ("time" not in v) and (not v.endswith("_bnds"))
    ]
    out_ds = ds.drop_vars(to_drop)

    # Set global attributes
    out_df = set_ods_global_attrs(
        out_ds,
        activity_id="obs4MIPs",
        comment="Not yet obs4MIPs compliant: 'version' attribute is temporary",
        contact="Hamed Alemohammad (halemohammad@clarku.edu)",
        conventions="CF-1.12 ODS-2.5",
        creation_date=creation_stamp,
        dataset_contributor="Morgan Steckler",
        data_specs_version="ODS2.5",
        doi="N/A",
        external_variables="N/A",
        frequency="mon",
        grid="1x1 degree latitude x longitude",
        grid_label="gn",
        has_auxdata="False",
        history=f"""
{download_stamp}: downloaded {remote_source};
{creation_stamp}: converted to obs4MIP format""",
        institution="Columbia University, NY, USA",
        institution_id="ColumbiaU",
        license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
        nominal_resolution="100 km",
        processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/WECANN/convert.py",
        product="derived",
        realm="land",
        references="Alemohammad, S. H., Fang, B., Konings, A. G., Aires, F., Green, J. K., Kolassa, J., Miralles, D., Prigent, C., and Gentine, P.: Water, Energy, and Carbon with Artificial Neural Networks (WECANN): a statistically based estimate of global surface turbulent fluxes and gross primary productivity using solar-induced fluorescence, Biogeosciences, 14, 4101–4124, https://doi.org/10.5194/bg-14-4101-2017, 2017.",
        region="global_land",
        source="WECANN 1.0 (2018): Water, Energy, and Carbon with Artificial Neural Networks",
        source_id="WECANN-1-0",
        source_data_retrieval_date=download_stamp,
        source_data_url=remote_source,
        source_label="WECANN",
        source_type="satellite_retrieval",
        source_version_number="1.0",
        title="Water, Energy, and Carbon with Artificial Neural Networks (WECANN)",
        tracking_id=tracking_id,
        variable_id=var,
        variant_label="REF",
        variant_info="CMORized product prepared by ILAMB and CMIP IPO",
        version=f"v{today_stamp}",
    )

    out_path = create_output_filename(out_ds.attrs)
    out_ds.to_netcdf(out_path)

    print(f"Exported to {out_path}")

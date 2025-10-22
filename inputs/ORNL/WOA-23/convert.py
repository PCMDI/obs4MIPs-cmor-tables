from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

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

# DATA NOTES:
# Climatologies:
# --------------
# 00 = 1-year
# 01-12 = each month
# 13-16 = each season

# Within-file naming
# ------------------
# statistical mean = average of quality controlled raw observational stats; simple averaging; gridcells subject to missing data/uneven sampling
# objectively analyzed climatology = take statistical means and fill gaps + interpolate unevenly sampled gridcells

# salinity, temperature
# ---------------------
# Decadal averages: 5564 (1955-1964), 6574 (1965-1974), 7584 (1975-1984), 8594 (1985-1994), 95A4 (1995-2004), A5B4 (2005-2014), B5C2 (2015-2022)
# 30-year averages: decav71A0 (1971-2000), decav81B0 (1981-2010), decav91C0 (1991-2020)
# Average of 7 decades (1955-2022): decav

# phosphate, nitrate, oxygen, silicate
# ------------------------------------
# Average of available data (1965-2022): all

AVG_PERIODS = ["decav"]
NAME_CONVERSIONS = {
    "oxygen": {"o": "o2"},
    "phosphate": {"p": "po4"},
    "nitrate": {"n": "no3"},
    "silicate": {"i": "si"},
    "temperature": {"t": "thetao"},
    "salinity": {"s": "so"},
}

# Build remote_source_dict = {full_name: {period: [urls]}}
remote_source_dict = {}

for full_name, abbv_dict in NAME_CONVERSIONS.items():
    code, cmip_var = next(iter(abbv_dict.items()))
    periods = AVG_PERIODS if full_name in ("temperature", "salinity") else ["all"]

    for period in periods:
        urls = [
            f"https://www.ncei.noaa.gov/data/oceans/woa/WOA23/DATA/{full_name}/netcdf/{period}/1.00/"
            f"woa23_{period}_{code}{month:02d}_01.nc"
            for month in range(1, 13)
        ]
        remote_source_dict.setdefault(full_name, {})[period] = urls

# Download + build local_source_dict = {full_name: {period: [local_paths]}}
local_source_dict = {}
for full_name, periods in remote_source_dict.items():
    for period, urls in periods.items():
        local_paths = []
        for url in urls:
            # derive a stable local path: _raw/<full_name>/<period>/<filename>
            fname = Path(urlparse(url).path).name
            dest = Path("_raw") / full_name / period / fname
            dest.parent.mkdir(parents=True, exist_ok=True)

            if not dest.is_file():
                download_from_html(url, str(dest))

            local_paths.append(str(dest))
        local_source_dict.setdefault(full_name, {})[period] = local_paths

# Set timestamps and tracking id
local_source_ex = local_source_dict["temperature"]["decav"][0]
download_stamp = gen_utc_timestamp(Path(local_source_ex).stat().st_mtime)
creation_stamp = gen_utc_timestamp()
today_stamp = datetime.now().strftime("%Y%m%d")
tracking_id = gen_trackingid()

# --------- MAIN LOOP ----------
for name, period_dict in local_source_dict.items():
    for period, files in period_dict.items():
        var, std_var = next(iter(NAME_CONVERSIONS[name].items()))
        print(f"\nWorking on var '{var}' ({std_var})...")

        # Open without decoding time (it is encoded as "months since ...")
        ds = xr.open_mfdataset(files, decode_times=False, coords="all")

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
        for tvar in ["time", "climatology_bounds"]:
            ds[tvar].attrs["units"] = f"days since {origin_str}"
            ds[tvar].attrs["calendar"] = calendar

        # Ensure time values are cftime objects
        time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
        ds = xr.decode_cf(ds, decode_times=time_coder)
        lbound = ds["climatology_bounds"].values.min()

        # keep Objectively analyzed climatology (_an) & Standard error of the mean of each variable (_se)
        ds = (
            ds.drop_vars(
                [
                    f"{var}_mn",  # Statistical mean
                    f"{var}_dd",  # Number of observations
                    f"{var}_sd",  # Standard deviation about the statistical mean of each variable
                    f"{var}_oa",  # Statistical mean minus the climatological mean
                    f"{var}_ma",  # Seasonal or monthly climatology minus the annual climatology
                    f"{var}_gp",  # Number of one-degree squares within the smallest radius of influence
                    f"{var}_sdo",  # Objectively analyzed standard deviation
                    f"{var}_sea",  # Standard error of the analysis
                    "crs",
                    "climatology_bounds",  # CF climatology bounds is re-built below
                    "climatology_bnds",
                ],
                errors="ignore",
            )
            .rename_vars({f"{var}_an": std_var, f"{var}_se": f"{std_var}_se"})
            .rename_dims({"nbounds": "bnds"})
        )

        # Variable attrs (example units; adjust per variable if needed)
        ds[std_var].attrs["units"] = "umol kg-1"
        ds = set_var_attrs(
            ds,
            var=std_var,
            cmip6_units=ds[std_var].attrs["units"],
            cmip6_standard_name=ds[std_var].attrs.get("standard_name"),
            cmip6_long_name=ds[std_var].attrs.get("long_name"),
            ancillary_variables=f"{std_var}_se",
            cell_methods="area: mean depth: mean time: mean within years time: mean over years",
            target_dtype=np.float32,
            convert=False,
        )
        ds[std_var].attrs.pop("grid_mapping", None)

        # Ancillary attrs
        ds[f"{std_var}_se"].attrs = {
            "standard_name": f"{ds[std_var].attrs.get('standard_name')} standard_error",
            "units": ds[std_var].attrs["units"],
        }
        ds[f"{std_var}_se"].encoding = {"_FillValue": None}

        # Standardize time/coord attrs & build monthly **climatology** bounds via your helper
        ds = set_time_attrs(
            ds,
            bounds_frequency="M",
            ref_date=ref_cf,  # reference cftime from dataset units
            climatology=True,  # create climatology_bnds and time
            create_new_time=False,  # use existing time values, don't re-create
            clim_sdate=cf.DatetimeGregorian(lbound.year, lbound.month, lbound.day),
            clim_edate=cf.DatetimeGregorian(2022, 1, 1),
        )

        # Lat/Lon/Depth attrs & bounds
        ds = set_lat_attrs(ds)
        ds = set_lon_attrs(ds)
        assert (ds.depth_bnds == ds.depth_bnds.isel(time=0)).all()
        ds = set_depth_attrs(
            ds,
            bounds=ds.depth_bnds.isel(time=0).to_numpy(),
            units="meters",
            positive="down",
            long_name="depth of sea water",
        )
        ds = set_coord_bounds(ds, "lat")
        ds = set_coord_bounds(ds, "lon")

        # Order + var selection
        ds = standardize_dim_order(ds)

        # Populate attributes
        title = ds.attrs["title"]
        reference = ds.attrs["references"]
        ds = set_ods_global_attrs(
            ds,
            activity_id="obs4MIPs",
            aux_variable_id=f"{std_var}_se",
            comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
            contact="NOAA National Centers for Environmental Information (ncei.info@noaa.gov)",
            conventions="CF-1.12 ODS-2.5",
            creation_date=creation_stamp,
            dataset_contributor="Morgan Steckler",
            data_specs_version="2.5",
            doi="10.25921/va26-hv25",
            external_variables="N/A",
            frequency="monC",
            grid="1x1 degree latitude x longitude",
            grid_label="gn",
            has_auxdata="True",
            history=f"""
    {download_stamp}: downloaded file;
    {creation_stamp}: converted to obs4MIPs format""",
            institution="National Oceanic and Atmospheric Administration, National Centers for Environmental Information, Ocean Climate Laboratory, Asheville, NC, USA",
            institution_id="NOAA-NCEI-OCL",
            license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
            nominal_resolution="1x1 degree",
            processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/WOA/convert.py",
            product="observations",
            realm="ocean",
            references=reference,
            region="global_ocean",
            source="WOA 2023 (2024): World Ocean Atlas",
            source_id="WOA-23",
            source_data_retrieval_date=download_stamp,
            source_data_url="https://www.ncei.noaa.gov/data/oceans/woa/WOA23/DATA/",
            source_label="WOA",
            source_type="gridded_insitu",
            source_version_number="1.0",
            title=title,
            tracking_id=tracking_id,
            variable_id=std_var,
            variant_label="REF",
            variant_info="CMORized product prepared by ILAMB and CMIP IPO",
            version=f"v{today_stamp}",
        )

        # Prep for export
        out_path = create_output_filename(ds.attrs)
        ds.to_netcdf(out_path, format="NETCDF4")

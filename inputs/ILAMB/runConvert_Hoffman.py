# Last update: 11 July 2025
# Author: Morgan Steckler (stecklermr@ornl.gov)

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
    set_ods_global_attrs,
    set_time_attrs,
    set_var_attrs,
)

VARS = ["nbp", "fgco2"]
UNC = "95pci"


# Download the data
remote_source = "https://www.ilamb.org/ILAMB-Data/DATA/nbp/HOFFMAN/nbp_1850-2010.nc"
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
time_coder = xr.coders.CFDatetimeCoder(use_cftime=True)
ds = xr.open_dataset(local_source, decode_times=time_coder)
ds = set_time_attrs(ds, bounds_frequency="Y", ref_date=cf.DatetimeNoLeap(1850, 1, 1))

for var in VARS:
    # Get attribute info for fgco2 and nbp
    var_info = get_cmip6_variable_info(var)

    # Set correct attribute information for the vars
    ds = set_var_attrs(
        ds,
        var=var,
        cmip6_units=var_info["variable_units"],
        cmip6_standard_name=var_info["cf_standard_name"],
        cmip6_long_name=var_info["variable_long_name"],
        ancillary_variables=f"{var}_{UNC}",
        target_dtype=np.float32,
        convert=False,
    )

    # Assign ancillary variables
    ds = ds.rename({f"{var}_bnds": f"{var}_{UNC}"})
    ds[f"{var}_{UNC}"].attrs["long_name"] = (
        f"{ds[var].attrs['standard_name']} 95_pct_confidence_interval"
    )
    ds[f"{var}_{UNC}"].encoding = {
        "_FillValue": np.float32(1.0e20),
        "dtype": np.float32,
    }

# Clean up attrs
for var in ds.variables:
    ds[var].encoding.pop("missing_value", None)
ds["nbp"].attrs.pop("bounds", None)
ds["fgco2"].attrs.pop("bounds", None)

# Set global attributes and export
for var in VARS:
    # Create one ds per variable
    out_ds = ds.drop_vars([v for v in ds if (var not in v and "time" not in v)])
    out_ds["time"].encoding = {"_FillValue": None}

    # Define varibable-dependant attributes
    dynamic_attrs = {
        "realm": "land" if var == "nbp" else "ocean",
        "region": f"global_{'land' if var == 'nbp' else 'ocean'}",
        "title": f"{'Land' if var == 'nbp' else 'Ocean'} anthropogenic carbon flux estimates",
        "variable_id": var,
    }

    # Set global attributes
    out_ds = set_ods_global_attrs(
        out_ds,
        activity_id="obs4MIPs",
        aux_variable_id=f"{var}_{UNC}",
        comment="Not yet obs4MIPs compliant: 'version' attribute is temporary; source_id not in obs4MIPs yet",
        contact="Forrest Hoffman (forrest@climatemodeling.org)",
        conventions="CF-1.12 ODS-2.5",
        creation_date=creation_stamp,
        dataset_contributor="Morgan Steckler",
        data_specs_version="2.5",
        doi="N/A",
        frequency="yr",
        grid="global mean data",
        grid_label="gm",
        has_auxdata="True",
        history=f"""
{download_stamp}: downloaded {remote_source};
{creation_stamp}: converted to obs4MIPs format""",
        institution="University of California at Irvine, Irvine, CA, USA; Oak Ridge National Laboratory, Oak Ridge, TN, USA",
        institution_id="UCI-ORNL",
        license="Data in this file produced by ILAMB is licensed under a Creative Commons Attribution- 4.0 International (CC BY 4.0) License (https://creativecommons.org/licenses/).",
        nominal_resolution="site",
        processing_code_location="https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/Hoffman/convert.py",
        product="derived",
        realm=dynamic_attrs["realm"],
        references="Hoffman, Forrest M., James T. Randerson, Vivek K. Arora, Qing Bao, Patricia Cadule, Duoying Ji, Chris D. Jones, Michio Kawamiya, Samar Khatiwala, Keith Lindsay, Atsushi Obata, Elena Shevliakova, Katharina D. Six, Jerry F. Tjiputra, Evgeny M. Volodin, and Tongwen Wu, (2014) Causes and Implications of Persistent Atmospheric Carbon Dioxide Biases in Earth System Models. J. Geophys. Res. Biogeosci., 119(2):141-162. https://doi.org/10.1002/2013JG002381.",
        region=dynamic_attrs["region"],
        source="Annual land carbon storage change = (total anthropogenic CO2 emissions) - (atmospheric carbon storage change) - (ocean carbon storage change)",
        source_id="Hoffman-1-0",
        source_data_retrieval_date=download_stamp,
        source_data_url=remote_source,
        source_label="Hoffman",
        source_type="stastical-estimate",
        source_version_number="1.0",
        title=dynamic_attrs["title"],
        tracking_id=tracking_id,
        variable_id=var,
        variant_label="REF",
        variant_info="CMORized product prepared by ILAMB and CMIP IPO",
        version=f"v{today_stamp}",
    )

    out_path = create_output_filename(out_ds.attrs)
    encoding = {name: out_ds[name].encoding.copy() for name in out_ds.variables}
    out_ds.to_netcdf(out_path, encoding=encoding, format="NETCDF4")

    print(f"Exported to {out_path}")

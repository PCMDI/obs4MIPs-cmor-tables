import os
from pathlib import Path

import cftime as cf
import numpy as np
import xarray as xr
from ilamb3.dataset import coarsen_dataset

from ilamb3_data import gen_utc_timestamp, set_lat_attrs, set_lon_attrs

PURGE = True
remote_source = "https://catalogue.ceda.ac.uk/uuid/f4654030223445b0bac63a23aaa60620/"


def download_average_and_coarsen(
    year: int, month: int, output_path: Path | str = "_raw", remove_source: bool = False
) -> None:
    # Only redownload and run if the intermediate file does not exist
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    out_file = output_path / f"snc-{year:04d}-{month:02d}.nc"
    if out_file.is_file():
        return

    os.system(
        f"wget -e robots=off --mirror --no-parent -r https://dap.ceda.ac.uk/neodc/esacci/snow/data/scfg/CryoClim/v1.0/{year:04d}/{month:02d}/"
    )
    root = Path(
        f"dap.ceda.ac.uk/neodc/esacci/snow/data/scfg/CryoClim/v1.0/{year:04d}/{month:02d}/"
    )
    ds = xr.open_mfdataset(sorted(root.glob("*.nc"))).mean(dim="time")
    ds = ds.drop_vars(["spatial_ref", "lat_bnds", "lon_bnds"])
    ds = xr.where(ds["scfg"] < 150, ds, np.nan)
    ds = coarsen_dataset(ds, res=0.5)
    ds = ds.expand_dims(dim={"time": [cf.DatetimeNoLeap(year, month, 15)]}, axis=0)
    ds["time_bnds"] = (
        ("time", "nv"),
        [
            [
                cf.DatetimeNoLeap(year, month, 1),
                cf.DatetimeNoLeap(
                    year + (1 if month == 12 else 0),
                    1 if month == 12 else (month + 1),
                    1,
                ),
            ]
        ],
    )
    ds["time"].attrs = {
        "axis": "T",
        "standard_name": "time",
        "long_name": "time",
        "bounds": "time_bnds",
    }
    ds["time"].encoding = {"units": "days since 1983-01-01", "calendar": "noleap"}
    ds = ds.drop_vars(["cell_measures"])
    ds.to_netcdf(str(out_file))
    if remove_source:
        for filename in root.iterdir():
            filename.unlink()


# Initial pass to create monthly mean files
for year in range(1982, 2020):
    for month in range(1, 13):
        if year == 2019 and month > 6:
            continue
        download_average_and_coarsen(year, month, remove_source=PURGE)

out = xr.open_mfdataset("_raw/snc*.nc")
out = out.rename_vars({"scfg": "snc", "scfg_unc": "snc_unc"})

# Fix up the dimensions
out = set_lat_attrs(out)
out = set_lon_attrs(out)
out = out.sortby(["time", "lat", "lon"])
out = out.cf.add_bounds(["lat", "lon"])
out["time"].attrs["bounds"] = "time_bnds"
out["time_bnds"].attrs["long_name"] = "time_bounds"
time_range = f"{out['time'].min().dt.year:d}{out['time'].min().dt.month:02d}"
time_range += f"-{out['time'].max().dt.year:d}{out['time'].max().dt.month:02d}"

download_stamp = gen_utc_timestamp(
    next(iter(Path("_raw/").glob("*.nc"))).stat().st_mtime
)
generate_stamp = gen_utc_timestamp()

# Populate attributes
attrs = {
    "activity_id": "obs4MIPs",
    "contact": "Thomas Nagler (thomas.nagler@enveo.at)",
    "Conventions": "CF-1.12 ODS-2.5",
    "creation_data": generate_stamp,
    "dataset_contributor": "Nathan Collier",
    "data_specs_version": "2.5",
    "doi": "10.5285/f4654030223445b0bac63a23aaa60620",
    "frequency": "mon",
    "grid": "0.5x0.5 degree",
    "grid_label": "gn",
    "history": """
%s: downloaded raw data from %s;
%s: converted to obs4MIP format"""
    % (
        download_stamp,
        remote_source,
        generate_stamp,
    ),
    "institution": "European Space Agency Climate Change Initiative",
    "institution_id": "ESACCI",
    "license": "CC BY-NC-SA 4.0",
    "nominal_resolution": "0.5x0.5 degree",
    "processing_code_location": "https://github.com/rubisco-sfa/ilamb3-data/blob/main/data/Snow-cci/convert.py",
    "product": "observations",
    "realm": "land",
    "references": "Solberg, R.; Rudjord, Ø.; Salberg, A.-B.; Killie, M.A.; Eastwood, S.; Sørensen, A.; Marin, C.; Premier, V.; Schwaizer, G.; Nagler, T. (2023): ESA Snow Climate Change Initiative (Snow_cci): Fractional Snow Cover in CryoClim, v1.0. NERC EDS Centre for Environmental Data Analysis, 08 August 2023. doi:10.5285/f4654030223445b0bac63a23aaa60620.",
    "region": "global_land",
    "source": "The product is based on a multi-sensor time-series fusion algorithm combining observations by optical and passive microwave radiometer (PMR) data, combining an historical record of AVHRR sensor data with PMR data from the SMMR, SSM/I and SSMIS sensors.",
    "source_id": "Snow-cci",
    "source_data_retrieval_date": download_stamp,
    "source_data_url": remote_source,
    "source_type": "satellite_retrieval",
    "source_version_number": "1",
    "title": "Fractional Snow Cover in CryoClim",
    "variant_label": "BE",
}

# Write out files
out.attrs = attrs | {"variable_id": "snc"}
out.to_netcdf(
    "{variable_id}_{frequency}_{source_id}_{variant_label}_{grid_label}_{time_mark}.nc".format(
        **out.attrs, time_mark=time_range
    ),
    encoding={"snc": {"zlib": True}, "snc_unc": {"zlib": True}},
)

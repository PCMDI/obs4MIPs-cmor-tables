#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CMORize JASMES Snow Cover (snc) to obs4MIPs for a given date range (specified in code).

Input file pattern:
  ../org_data/YYYY/MM/{type}YYYYMMDD_YYYYMMDD_GLBOD01D_SNWFG_EQ05KM_1?9.hdf.gz
  where {type} in {GHR, M5C, SVC}

Notes:
- No pyhdf, no xarray, no xcdat
- Read HDF4 via GDAL
- snc = surface_snow_area_fraction (0/1, missing=1e20)
- Writes one NetCDF per day (CMOR table obs4MIPs_Aday)
- Adds provenance into global attribute: input_sensor_provenance
"""

import cmor
import numpy as np
import sys, os, re, gzip, shutil, tempfile, glob
from datetime import datetime, timedelta
from osgeo import gdal

# obs4MIPs provenance helper (for git hash)
sys.path.append("../../../inputs/misc")
import obs4MIPsLib

# =========================
# User settings
# =========================
CMOR_TABLE = "../../../Tables/obs4MIPs_Aday.json"
INPUT_JSON = "./obs4MIPs_JASMES_SNOWCOVER.json"

tgt_org_data_path = "/Users/wakuhisa/Desktop/EORC_tmp/20251224_obs4mip_snc/obs4MIPs-cmor-tables/CMOR_JASMES_snc/org_data/"

INPUT_SDS_NAME = "cs_flg_tpf"
OUTPUT_VAR_NAME = "snc"
OUTPUT_UNITS = "1"

# Missing value (CMOR/CMIP convention; NaN is not allowed)
MISSING = np.float32(1e20)

# =========================
# Execution period (EDIT HERE)
# =========================
YYYYMMDD_START = "19781201"
YYYYMMDD_END   = "19781201"

YYYYMMDD_START = "20010101"
YYYYMMDD_END   = "20010101"

YYYYMMDD_START = "20190101"
YYYYMMDD_END   = "20190101"

# Which types to process (EDIT HERE)
# allowed: "GHR", "M5C", "SVC"
TYPES = ["GHR", "M5C", "SVC"]


# =========================
# Utilities
# =========================
def yyyymmdd_to_date(s: str):
    return datetime.strptime(s, "%Y%m%d").date()


def daterange(d0, d1):
    d = d0
    while d <= d1:
        yield d
        d += timedelta(days=1)


def build_input_glob(d, typ):
    """Return glob pattern for given date and type."""
    yyyy = d.strftime("%Y")
    mm = d.strftime("%m")
    ymd = d.strftime("%Y%m%d")
    # Example: ../org_data/1978/12/GHR19781201_19781201_GLBOD01D_SNWFG_EQ05KM_1n9.hdf.gz
    return tgt_org_data_path + f"{yyyy}/{mm}/{typ}{ymd}_{ymd}_GLBOD01D_SNWFG_EQ05KM_1?9.hdf.gz"
    #GHR19781201_19781201_GLBOD01D_SNWFG_EQ05KM_1n9.hdf.gz
    #M5C20010101_20010101_GLBOD01D_SNWFG_EQ05KM_1m9.hdf.gz
    #SVC20190101_20190101_GLBOD01D_SNWFG_EQ05KM_1s9.hdf.gz

def parse_date_from_filename(fp):
    m = re.search(r"(19|20)\d{6}", os.path.basename(fp))
    if not m:
        raise ValueError(f"Date not found in filename: {fp}")
    return datetime.strptime(m.group(0), "%Y%m%d").date()


def collect_files(start_date, end_date, types):
    """
    Collect existing files within [start_date, end_date] for given types.
    Returns list of file paths sorted by date then type.
    """
    found = []
    for d in daterange(start_date, end_date):
        for typ in types:
            pat = build_input_glob(d, typ)
            hits = sorted(glob.glob(pat))
            for h in hits:
                found.append(h)

    found.sort(key=lambda p: (parse_date_from_filename(p), os.path.basename(p)))
    return found


def gunzip_to_temp(fp):
    if not fp.endswith(".gz"):
        return fp, lambda: None

    tmpdir = tempfile.mkdtemp(prefix="jasmes_")
    outfp = os.path.join(tmpdir, os.path.basename(fp[:-3]))

    with gzip.open(fp, "rb") as f_in, open(outfp, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

    def cleanup():
        shutil.rmtree(tmpdir, ignore_errors=True)

    return outfp, cleanup


def read_sds_hdf4_via_gdal(fp, sds_name):
    ds = gdal.Open(fp)
    if ds is None:
        raise RuntimeError(
            f"GDAL could not open {fp}\n"
            f"Hint: You may need HDF4 driver: conda install -c conda-forge libgdal-hdf4"
        )

    subs = ds.GetSubDatasets()
    target = None
    for name, desc in subs:
        if sds_name in name or sds_name in desc:
            target = name
            break

    if target is None:
        raise RuntimeError(f"SDS {sds_name} not found in {fp}")

    sds = gdal.Open(target)
    arr = sds.ReadAsArray()
    return arr.astype(np.uint8, copy=False)


def flag_to_snc(flg):
    """
    Convert cs_flg_tpf to snc (fraction: 0/1, missing=1e20).
    Only LAND snow/no-snow are mapped; others remain missing.

    Land snow:
      160-169, 170-172, 180-181, 190-193 -> 1
    Land no-snow:
      140-147, 150-151 -> 0
    Everything else -> missing (1e20)
    """
    snc = np.full(flg.shape, MISSING, dtype=np.float32)

    # snow on land
    snc[(flg >= 160) & (flg <= 169)] = 1.0
    snc[(flg >= 170) & (flg <= 172)] = 1.0
    snc[(flg >= 180) & (flg <= 181)] = 1.0
    snc[(flg >= 190) & (flg <= 193)] = 1.0

    # snow-free land
    snc[(flg >= 140) & (flg <= 147)] = 0.0
    snc[(flg >= 150) & (flg <= 151)] = 0.0

    return snc

"""
def make_lon_lat_with_bounds(nlat, nlon):
    # longitude edges and bounds
    dlon = 360.0 / nlon
    lon_edges = -180.0 + dlon * np.arange(nlon + 1, dtype=np.float64)   # -180 ... 180
    lon = 0.5 * (lon_edges[:-1] + lon_edges[1:])                       # centers
    lon_bnds = np.stack([lon_edges[:-1], lon_edges[1:]], axis=1)        # (nlon,2)

    # latitude centers include poles; bounds from midpoints
    lat = np.linspace(90.0, -90.0, nlat, dtype=np.float64)              # centers
    lat_edges = np.empty(nlat + 1, dtype=np.float64)
    lat_edges[1:-1] = 0.5 * (lat[:-1] + lat[1:])                        # midpoints
    lat_edges[0] = 90.0
    lat_edges[-1] = -90.0
    lat_bnds = np.stack([lat_edges[:-1], lat_edges[1:]], axis=1)         # (nlat,2)
    lat_bnds = np.sort(lat_bnds, axis=1)

    return lat, lon, lat_bnds, lon_bnds
"""

def make_lon_lat_with_bounds(nlat, nlon):
    """
    Exact coordinate construction (no floating-point runoff).
    Expected grid: nlat=3601 (90 to -90 every 0.05 deg), nlon=7200 (0.05 deg)
    lon in [-180, 180), lat in [90, -90]
    """
    # Use centi-degrees (0.01 deg) as integer base
    # 0.05 deg = 5 centi-deg
    step_cd = 5  # centi-deg

    # ---- lon ----
    # edges: -180 ... 180 step 0.05
    lon_edges_cd = np.arange(-18000, 18000 + step_cd, step_cd, dtype=np.int64)  # len = nlon+1
    if lon_edges_cd.size != nlon + 1:
        raise RuntimeError(f"Unexpected lon size: {lon_edges_cd.size} (expected {nlon+1})")

    lon_cd = (lon_edges_cd[:-1] + lon_edges_cd[1:]) // 2  # exact centers in centi-deg
    lon = lon_cd.astype(np.float64) / 100.0
    lon_bnds = np.stack([lon_edges_cd[:-1], lon_edges_cd[1:]], axis=1).astype(np.float64) / 100.0

    # ---- lat ----
    # centers include poles: 90, 89.95, ..., -90
    lat_cd = np.arange(9000, -9000 - step_cd, -step_cd, dtype=np.int64)  # len = nlat
    if lat_cd.size != nlat:
        raise RuntimeError(f"Unexpected lat size: {lat_cd.size} (expected {nlat})")

    # edges: first=90, last=-90, interior midpoints
    lat_edges_cd = np.empty(nlat + 1, dtype=np.int64)
    lat_edges_cd[0] = 9000
    lat_edges_cd[-1] = -9000
    lat_edges_cd[1:-1] = (lat_cd[:-1] + lat_cd[1:]) // 2  # exact midpoints

    lat = lat_cd.astype(np.float64) / 100.0
    lat_bnds = np.stack([lat_edges_cd[:-1], lat_edges_cd[1:]], axis=1).astype(np.float64) / 100.0
    lat_bnds = np.sort(lat_bnds, axis=1)  # ensure increasing bounds

    return lat, lon, lat_bnds, lon_bnds

def detect_sensor_provenance(filename):
    if "GHR" in filename:
        return "GHR: Input snow cover fraction derived from AVHRR onboard NOAA series satellites (1978–2000)."
    elif "M5C" in filename:
        return "M5C: Input snow cover fraction derived from MODIS onboard Terra and Aqua satellites (2001–2018)."
    elif "SVC" in filename:
        return "SVC: Input snow cover fraction derived from VIIRS onboard Suomi NPP and JPSS-1 satellites, and SGLI onboard GCOM-C (2019–2025)"
    else:
        print("Input sensor provenance could not be determined from filename.")
        quit()


# =========================
# CMORize one file
# =========================
def cmorize_one_file(fp, cmorLat, cmorLon):
    # read & convert
    hdf_fp, cleanup = gunzip_to_temp(fp)
    try:
        flg = read_sds_hdf4_via_gdal(hdf_fp, INPUT_SDS_NAME)
    finally:
        cleanup()

    snc = flag_to_snc(flg)

    # shift 180 deg to match lon centers/bounds convention (-180..180)
    nlat, nlon = snc.shape
    shift = nlon // 2
    snc = np.roll(snc, shift=shift, axis=1)

    # time axis: daily, bounds [0,1], CMOR will use center=0.5
    date = parse_date_from_filename(fp)
    time_units = f"days since {date.strftime('%Y-%m-%d')} 00:00:00"
    time_val = np.array([0.0], dtype=np.float64)
    time_bnds = np.array([[0.0, 1.0]], dtype=np.float64)

    cmorTime = cmor.axis("time", coord_vals=time_val, cell_bounds=time_bnds, units=time_units)
    cmoraxes = [cmorTime, cmorLat, cmorLon]

    varid = cmor.variable(OUTPUT_VAR_NAME, OUTPUT_UNITS, cmoraxes, missing_value=MISSING)

    # valid range (CMOR converts 1 -> % for snc in obs4MIPs tables)
    cmor.set_variable_attribute(varid, "valid_min", "f", 0.0)
    cmor.set_variable_attribute(varid, "valid_max", "f", 100.0)

    cmor.set_deflate(varid, 1, 1, 1)

    # add provenance (not overwritten by CMOR)
    prov = detect_sensor_provenance(os.path.basename(fp))
    cmor.set_cur_dataset_attribute("input_sensor_provenance", prov)

    # write (one time step)
    cmor.write(varid, snc[np.newaxis, :, :], 1)
    cmor.close(varid)

    print(f"[OK] {date}  {os.path.basename(fp)}")


# =========================
# Main
# =========================
def main():
    # collect files based on in-code period
    start_date = yyyymmdd_to_date(YYYYMMDD_START)
    end_date = yyyymmdd_to_date(YYYYMMDD_END)

    files = collect_files(start_date, end_date, TYPES)
    if not files:
        print("No files found for the given range/types.")
        sys.exit(1)

    print(f"Found {len(files)} files:")
    for f in files[:10]:
        print("  ", f)
    if len(files) > 10:
        print("  ...")
    print(files)

    # CMOR init
    cmor.setup(inpath="./", netcdf_file_action=cmor.CMOR_REPLACE_4)
    cmor.dataset_json(INPUT_JSON)
    cmor.load_table(CMOR_TABLE)



    # provenance: processing code location
    git_commit_number = obs4MIPsLib.get_git_revision_hash()
    path_to_code = os.getcwd().split("obs4MIPs-cmor-tables")[-1]
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
    cmor.set_cur_dataset_attribute("processing_code_location", full_git_path)

    # Define lat/lon axes once from a sample file
    sample = files[0]
    hdf_fp, cleanup = gunzip_to_temp(sample)
    try:
        flg0 = read_sds_hdf4_via_gdal(hdf_fp, INPUT_SDS_NAME)
    finally:
        cleanup()

    nlat, nlon = flg0.shape
    if (nlat, nlon) != (3601, 7200):
        raise RuntimeError(f"Unexpected grid shape: {(nlat, nlon)} (expected 3601x7200)")

    lat, lon, lat_bnds, lon_bnds = make_lon_lat_with_bounds(nlat, nlon)

    cmorLat = cmor.axis("latitude", coord_vals=lat, cell_bounds=lat_bnds, units="degrees_north")
    cmorLon = cmor.axis("longitude", coord_vals=lon, cell_bounds=lon_bnds, units="degrees_east")

    # Process each file (one output per day)
    n_ok = 0
    for fp in files:
        try:
            cmorize_one_file(fp, cmorLat, cmorLon)
            n_ok += 1
        except Exception as e:
            print(f"[FAIL] {fp}\n  {type(e).__name__}: {e}")

    cmor.close()
    print(f"Done. Success: {n_ok}/{len(files)}")


if __name__ == "__main__":
    main()

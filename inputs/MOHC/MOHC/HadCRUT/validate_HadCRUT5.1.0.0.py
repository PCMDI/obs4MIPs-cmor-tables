"""
Output validation for runCMOR_HadCRUT5.1.0.0.py
Checks the CMORized NetCDF against obs4MIPs requirements.
The dataset contributor is responsible for verifying all aspects of the output.
Usage: python validate_HadCRUT5.1.0.0.py
"""
import glob
import json
import os
import sys
import numpy as np
import xarray as xr

# ── Settings ───────────────────────────────────────────────────────────────────
cvTable       = '../../../../Tables/obs4MIPs_CV.json'
cmorTable     = '../../../../Tables/obs4MIPs_Amon.json'
outpath       = './'                        # Must match outpath in HadCRUT5.1.0.0.json
expectedVar   = 'tastosanomanom'            # out_name from CMOR table entry for tastosanom-MOHC
expectedUnits = '1'                         # As currently defined in CMOR table (TODO: should be K)
expectedDtype = 'float32'
expectedFill  = 1.e20

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

def check(label, condition, detail=""):
    print(f"  [{PASS if condition else FAIL}] {label}")
    if not condition and detail:
        print(f"         {detail}")
    return condition

def info(label, value):
    print(f"  [{INFO}] {label}: {value}")

# ── Find output file ───────────────────────────────────────────────────────────
print("\n1. Locating CMORized output file")
matches = glob.glob(os.path.join(outpath, "**", "*.nc"), recursive=True)
check("At least one NetCDF output file found", len(matches) > 0,
      f"No .nc files found under '{os.path.abspath(outpath)}'")
if not matches:
    sys.exit(1)

if len(matches) > 1:
    print(f"         Multiple files found - using most recent:")
    matches.sort(key=os.path.getmtime)
    for m in matches:
        print(f"           {m}")
ncfile = matches[-1]
info("Output file", ncfile)

# ── Open file ──────────────────────────────────────────────────────────────────
print("\n2. Opening file")
try:
    ds = xr.open_dataset(ncfile, decode_times=False)
    check("File opens without error", True)
except Exception as e:
    check("File opens without error", False, str(e))
    sys.exit(1)

# ── Global attributes ──────────────────────────────────────────────────────────
print("\n3. Checking global attributes")
# Required attributes from obs4MIPs CV required_global_attributes
required_attrs = [
    'Conventions', 'activity_id', 'contact', 'creation_date',
    'data_specs_version', 'frequency', 'grid', 'grid_label',
    'has_aux_unc', 'institution', 'institution_id', 'license',
    'nominal_resolution', 'processing_code_location', 'product',
    'realm', 'references', 'region', 'source', 'source_data_url',
    'source_id', 'source_type', 'source_version_number', 'table_id',
    'tracking_id', 'variable_id',
]
for attr in required_attrs:
    check(f"  global attr '{attr}' present", attr in ds.attrs,
          f"Missing from output file")

# Spot-check key values
info("institution_id", ds.attrs.get('institution_id', '(missing)'))
info("source_id",      ds.attrs.get('source_id', '(missing)'))
info("variable_id",    ds.attrs.get('variable_id', '(missing)'))
info("frequency",      ds.attrs.get('frequency', '(missing)'))
info("tracking_id",    ds.attrs.get('tracking_id', '(missing)'))
info("creation_date",  ds.attrs.get('creation_date', '(missing)'))

# ── Variable checks ────────────────────────────────────────────────────────────
print("\n4. Checking data variable")
check(f"Variable '{expectedVar}' present", expectedVar in ds.data_vars,
      f"Variables found: {list(ds.data_vars)}")

if expectedVar in ds.data_vars:
    v = ds[expectedVar]

    check(f"Data type is {expectedDtype}",
          str(v.dtype) == expectedDtype,
          f"Got: {v.dtype}")

    check(f"Units attribute = '{expectedUnits}'",
          v.attrs.get('units') == expectedUnits,
          f"Got: '{v.attrs.get('units', '(missing)')}'  -- NOTE: should be 'K', pending metadata fix in master")

    # xarray moves _FillValue to v.encoding (consumed during decode), not v.attrs
    fill = v.encoding.get('_FillValue',
           v.attrs.get('_FillValue',
           v.attrs.get('missing_value', None)))
    check("_FillValue / missing_value present",
          fill is not None,
          "Neither _FillValue nor missing_value found in attrs or encoding")
    if fill is not None:
        check(f"Missing value = {expectedFill}",
              np.isclose(float(fill), expectedFill),
              f"Got: {fill}")

    check("long_name present",     'long_name'     in v.attrs, "Missing long_name")
    check("standard_name present", 'standard_name' in v.attrs, "Missing standard_name")

    data = v.values
    finite = data[np.isfinite(data) & (data < expectedFill * 0.9)]
    info("Shape (time, lat, lon)", v.shape)
    info("Non-missing values",     f"{len(finite):,}  of  {data.size:,}  ({100*len(finite)/data.size:.1f}%)")
    if len(finite):
        info("Data range",         f"{finite.min():.4f} to {finite.max():.4f}  {v.attrs.get('units','')}")

    check("No Inf values in data", not np.any(np.isinf(data)),
          "Infinite values found in data array")
    check("Some non-missing data present", len(finite) > 0,
          "All values are missing - something went wrong")

# ── Coordinate checks ──────────────────────────────────────────────────────────
print("\n5. Checking coordinates")

# Latitude - CMOR always outputs the short CF name 'lat' and bounds as 'lat_bnds'
check("'lat' coordinate present", 'lat' in ds.coords,
      f"Expected 'lat'. Coords available: {list(ds.coords)}")
if 'lat' in ds.coords:
    lat = ds['lat'].values
    info("lat", f"{len(lat)} values,  {lat.min():.2f} to {lat.max():.2f} degrees_north")
    check(f"  'lat' range within [-90, 90]  (got {lat.min():.2f} to {lat.max():.2f})",
          lat.min() >= -90 and lat.max() <= 90)
    check(f"  'lat' is monotonically increasing",
          bool(np.all(np.diff(lat) > 0)),
          f"Min step: {np.diff(lat).min():.3f}")

    check(f"  'lat_bnds' present", 'lat_bnds' in ds,
          "Expected 'lat_bnds' — not found in dataset")
    if 'lat_bnds' in ds:
        lb = ds['lat_bnds'].values
        check(f"  'lat_bnds' shape is ({len(lat)}, 2)  (got {lb.shape})",
              lb.shape == (len(lat), 2))
        check(f"  'lat_bnds' contiguous: upper[t] == lower[t+1]",
              bool(np.allclose(lb[1:, 0], lb[:-1, 1])),
              f"Max gap: {np.max(np.abs(lb[1:,0] - lb[:-1,1])):.6f}")
        check(f"  'lat_bnds' span [-90, 90]  (got {lb.min():.3f} to {lb.max():.3f})",
              np.isclose(lb.min(), -90, atol=0.01) and np.isclose(lb.max(), 90, atol=0.01))

# Longitude - CMOR always outputs the short CF name 'lon' and bounds as 'lon_bnds'
check("'lon' coordinate present", 'lon' in ds.coords,
      f"Expected 'lon'. Coords available: {list(ds.coords)}")
if 'lon' in ds.coords:
    lon = ds['lon'].values
    info("lon", f"{len(lon)} values,  {lon.min():.2f} to {lon.max():.2f} degrees_east")
    check(f"  'lon' range within [-180, 360]  (got {lon.min():.2f} to {lon.max():.2f})",
          lon.min() >= -180 and lon.max() <= 360)
    check(f"  'lon' is monotonically increasing",
          bool(np.all(np.diff(lon) > 0)),
          f"Min step: {np.diff(lon).min():.3f}")

    check(f"  'lon_bnds' present", 'lon_bnds' in ds,
          "Expected 'lon_bnds' — not found in dataset")
    if 'lon_bnds' in ds:
        lonb = ds['lon_bnds'].values
        check(f"  'lon_bnds' shape is ({len(lon)}, 2)  (got {lonb.shape})",
              lonb.shape == (len(lon), 2))
        check(f"  'lon_bnds' contiguous: upper[t] == lower[t+1]",
              bool(np.allclose(lonb[1:, 0], lonb[:-1, 1])),
              f"Max gap: {np.max(np.abs(lonb[1:,0] - lonb[:-1,1])):.6f}")

# Time
check("'time' coordinate present", 'time' in ds.coords)
if 'time' in ds.coords:
    t = ds.time.values
    check("Time is monotonically increasing",
          bool(np.all(np.diff(t) > 0)),
          f"Non-monotonic steps found: {np.where(np.diff(t) <= 0)}")
    info("Time", f"{len(t)} steps,  units: {ds.time.attrs.get('units','(missing)')}")
    info("Time span", f"{t[0]:.1f} to {t[-1]:.1f}")

    if 'time_bnds' in ds:
        tb = ds.time_bnds.values
        check("Time bounds present and shape (n,2)", tb.shape == (len(t), 2))
        check("Time bounds are continuous (upper bound[t] == lower bound[t+1])",
              bool(np.allclose(tb[1:, 0], tb[:-1, 1])),
              f"Max discontinuity: {np.max(np.abs(tb[1:,0] - tb[:-1,1])):.6f} -- may cause issues in analysis")
        check("Each time value falls within its bounds",
              bool(np.all((t >= tb[:, 0]) & (t <= tb[:, 1]))),
              "Some time centre values fall outside their bounds")
        gaps = tb[1:, 0] - tb[:-1, 1]
        if not np.allclose(gaps, 0):
            gap_idx = np.where(~np.isclose(gaps, 0))[0]
            print(f"         Gap locations (time index): {gap_idx[:5]}{'...' if len(gap_idx)>5 else ''}")
    else:
        check("Time bounds present", False, "'time_bnds' not found in dataset")

# ── Data continuity ────────────────────────────────────────────────────────────
print("\n6. Checking for data discontinuities")
if expectedVar in ds.data_vars:
    v = ds[expectedVar]
    data = v.values
    missing_mask = ~np.isfinite(data) | (data >= expectedFill * 0.9)

    # Check for completely empty time slices
    empty_slices = np.where(missing_mask.reshape(data.shape[0], -1).all(axis=1))[0]
    check("No completely empty time slices",
          len(empty_slices) == 0,
          f"{len(empty_slices)} time steps are entirely missing: indices {empty_slices[:5]}")

    # Check for suspicious step changes between consecutive time steps - crude discontinuity detector
    slice_means = np.nanmean(np.where(missing_mask, np.nan, data).reshape(data.shape[0], -1), axis=1)
    valid_means = slice_means[np.isfinite(slice_means)]
    if len(valid_means) > 2:
        diffs = np.abs(np.diff(valid_means))
        # Use a generous threshold (10x std): sparse early-record and wartime coverage
        # gaps in HadCRUT5 cause legitimate apparent jumps in the spatial mean when
        # large regions drop in/out. These are data characteristics, not errors.
        threshold = 10 * np.std(diffs)
        jumps = np.where(diffs > threshold)[0]
        check("No suspicious jumps in global mean (threshold: 10x std of all steps)",
              len(jumps) == 0,
              f"{len(jumps)} large step(s) at time indices {jumps[:5]} -- likely sparse coverage, inspect visually")

# ── Summary ────────────────────────────────────────────────────────────────────
ds.close()
print("\nDone. Review any FAILs and confirm INFO values look physically reasonable.\n")

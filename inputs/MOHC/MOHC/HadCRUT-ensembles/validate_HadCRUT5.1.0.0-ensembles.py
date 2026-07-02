"""
Output validation for runCMOR_HadCRUT5.1.0.0-ensembles.py
Checks all 200 CMORized ensemble-member NetCDF files against obs4MIPs
requirements. Unlike validate_HadCRUT5.1.0.0.py (which validates a single
ensemble-mean file verbosely), this script must validate 200 files, so per-file
checks are done quietly and only failures/warnings are printed in detail; a
one-line PASS/FAIL summary is printed per file plus an overall summary at the end.
The dataset contributor is responsible for verifying all aspects of the output.
Usage: python validate_HadCRUT5.1.0.0-ensembles.py
"""
import glob
import json
import os
import re
import sys
import numpy as np
import xarray as xr

# ── Settings ───────────────────────────────────────────────────────────────────
cvTable         = '../../../../Tables/obs4MIPs_CV.json'
cmorTable       = '../../../../Tables/obs4MIPs_Amon.json'
outpath         = './'                        # Must match outpath in HadCRUT5.1.0.0-ensembles.json
expectedVar     = 'tastosanomanom'            # out_name from CMOR table entry for tastosanom-MOHC
expectedUnits   = '1'                         # As currently defined in CMOR table (TODO: should be K)
expectedDtype   = 'float32'
expectedFill    = 1.e20
expectedCount   = 200
variantPatternRe = re.compile(r'-r(\d{3})$')  # e.g. "MOHC-r001"

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

required_attrs = [
    'Conventions', 'activity_id', 'contact', 'creation_date',
    'data_specs_version', 'frequency', 'grid', 'grid_label',
    'has_aux_unc', 'institution', 'institution_id', 'license',
    'nominal_resolution', 'processing_code_location', 'product',
    'realm', 'references', 'region', 'source', 'source_data_url',
    'source_id', 'source_type', 'source_version_number', 'table_id',
    'tracking_id', 'variable_id', 'variant_label',
]

def info(label, value):
    print(f"  [{INFO}] {label}: {value}")

def validate_one_file(ncfile):
    """Returns a list of (label, detail) issues found in this file. Empty list = fully clean."""
    issues = []

    def check(label, condition, detail=""):
        if not condition:
            issues.append((label, detail))
        return condition

    try:
        ds = xr.open_dataset(ncfile, decode_times=False)
    except Exception as e:
        return [("File opens without error", str(e))]

    for attr in required_attrs:
        check(f"global attr '{attr}' present", attr in ds.attrs, "Missing from output file")

    variant_label = ds.attrs.get('variant_label', None)

    check(f"Variable '{expectedVar}' present", expectedVar in ds.data_vars,
          f"Variables found: {list(ds.data_vars)}")

    if expectedVar in ds.data_vars:
        v = ds[expectedVar]
        check(f"Data type is {expectedDtype}", str(v.dtype) == expectedDtype, f"Got: {v.dtype}")
        check(f"Units attribute = '{expectedUnits}'", v.attrs.get('units') == expectedUnits,
              f"Got: '{v.attrs.get('units', '(missing)')}'")

        fill = v.encoding.get('_FillValue', v.attrs.get('_FillValue', v.attrs.get('missing_value', None)))
        check("_FillValue / missing_value present", fill is not None)
        if fill is not None:
            check(f"Missing value = {expectedFill}", np.isclose(float(fill), expectedFill), f"Got: {fill}")

        check("long_name present", 'long_name' in v.attrs)
        check("standard_name present", 'standard_name' in v.attrs)

        data = v.values
        finite = data[np.isfinite(data) & (data < expectedFill * 0.9)]
        check("Some non-missing data present", len(finite) > 0, "All values are missing")
        check("No Inf values in data", not np.any(np.isinf(data)))

    check("'lat' coordinate present", 'lat' in ds.coords)
    if 'lat' in ds.coords:
        lat = ds['lat'].values
        check("'lat' range within [-90, 90]", lat.min() >= -90 and lat.max() <= 90,
              f"Got {lat.min():.2f} to {lat.max():.2f}")
        check("'lat' is monotonically increasing", bool(np.all(np.diff(lat) > 0)))
        check("'lat_bnds' present", 'lat_bnds' in ds)
        if 'lat_bnds' in ds:
            lb = ds['lat_bnds'].values
            check("'lat_bnds' shape correct", lb.shape == (len(lat), 2), f"Got {lb.shape}")
            check("'lat_bnds' span [-90, 90]",
                  np.isclose(lb.min(), -90, atol=0.01) and np.isclose(lb.max(), 90, atol=0.01))

    check("'lon' coordinate present", 'lon' in ds.coords)
    if 'lon' in ds.coords:
        lon = ds['lon'].values
        check("'lon' range within [0, 360]",
              lon.min() >= -1e-6 and lon.max() <= 360 + 1e-6,
              f"Got {lon.min():.2f} to {lon.max():.2f} -- CMOR should convert -180->180 source to 0->360")
        check("'lon' is monotonically increasing", bool(np.all(np.diff(lon) > 0)))
        check("'lon_bnds' present", 'lon_bnds' in ds)
        if 'lon_bnds' in ds:
            lonb = ds['lon_bnds'].values
            check("'lon_bnds' shape correct", lonb.shape == (len(lon), 2), f"Got {lonb.shape}")
            check("'lon_bnds' span [0, 360]",
                  np.isclose(lonb.min(), 0, atol=0.01) and np.isclose(lonb.max(), 360, atol=0.01))

    check("'time' coordinate present", 'time' in ds.coords)
    if 'time' in ds.coords:
        t = ds.time.values
        check("Time is monotonically increasing", bool(np.all(np.diff(t) > 0)))
        if 'time_bnds' in ds:
            tb = ds.time_bnds.values
            check("Time bounds shape correct", tb.shape == (len(t), 2))
            check("Time bounds contiguous", bool(np.allclose(tb[1:, 0], tb[:-1, 1])))
        else:
            check("Time bounds present", False, "'time_bnds' not found in dataset")

    ds.close()
    return variant_label, issues


# ── 1. Locate all output files ──────────────────────────────────────────────
print("\n1. Locating CMORized ensemble output files")
matches = sorted(glob.glob(os.path.join(outpath, "**", "*.nc"), recursive=True))
print(f"  [{INFO if len(matches) else FAIL}] Found {len(matches)} NetCDF file(s) under {os.path.abspath(outpath)}")
if len(matches) != expectedCount:
    print(f"  [{FAIL}] Expected exactly {expectedCount} files, found {len(matches)}")
if not matches:
    sys.exit(1)

# ── 2. Validate every file ──────────────────────────────────────────────────
print(f"\n2. Validating all {len(matches)} files (quiet per-file; failures printed in detail)")
all_variant_labels = []
files_with_issues = {}

for ncfile in matches:
    variant_label, issues = validate_one_file(ncfile)
    all_variant_labels.append(variant_label)
    status = PASS if not issues else FAIL
    print(f"  [{status}] {os.path.basename(ncfile)}  (variant_label={variant_label})"
          f"{'' if not issues else f'  -- {len(issues)} issue(s)'}")
    if issues:
        files_with_issues[ncfile] = issues
        for label, detail in issues:
            print(f"           - {label}" + (f": {detail}" if detail else ""))

# ── 3. Check ensemble membership (200 unique realisations, r001..r200) ──────
print("\n3. Checking ensemble membership (200 unique realisation labels)")
found_indices = set()
for vl in all_variant_labels:
    m = variantPatternRe.search(vl or "")
    if m:
        found_indices.add(int(m.group(1)))
    else:
        print(f"  [{FAIL}] variant_label '{vl}' does not match expected '...-rNNN' pattern")

expected_indices = set(range(1, expectedCount + 1))
missing = sorted(expected_indices - found_indices)
duplicates = len(all_variant_labels) - len(set(v for v in all_variant_labels if v))
extra = sorted(found_indices - expected_indices)

print(f"  [{PASS if len(found_indices) == expectedCount else FAIL}] "
      f"Found {len(found_indices)} unique realisation indices (expected {expectedCount})")
if missing:
    print(f"  [{FAIL}] Missing realisation(s): {missing}")
if extra:
    print(f"  [{FAIL}] Unexpected realisation index(es) outside 1-200: {extra}")
if len(set(all_variant_labels)) != len(all_variant_labels):
    print(f"  [{FAIL}] Duplicate variant_label(s) detected across output files")

# ── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
print(f"  Files found          : {len(matches)} (expected {expectedCount})")
print(f"  Files with 0 issues  : {len(matches) - len(files_with_issues)}")
print(f"  Files with issues    : {len(files_with_issues)}")
if files_with_issues:
    print("\n  Files needing attention:")
    for f in files_with_issues:
        print(f"    - {f}")
print("\nDone. Review any FAILs above and confirm INFO values look physically reasonable.\n")

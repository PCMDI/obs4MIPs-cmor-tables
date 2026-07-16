"""
Pre-flight checks for runCMOR_HadCRUT5.1.0.0-ensembles.py
Lighter-weight than test_HadCRUT5.1.0.0.py (the ensemble-mean pre-flight
script): rather than downloading and deep-checking all 200 members (which
would mean pulling ~6.5 GB / 20 zips on every pre-flight run), this script:
  1. Checks imports and local config/table files.
  2. HEAD-checks all 20 zip URLs are reachable (cheap - no download).
  3. Downloads ONE representative sample member (realisation 1) and runs
     the same depth of structural/plausibility checks the mean pre-flight
     script performs, since all 200 members share the same grid/format.
Usage: python test_HadCRUT5.1.0.0-ensembles.py
"""
import json
import os
import re
import sys
import tempfile
import urllib.request
import zipfile

import numpy as np
import xarray as xr

sys.path.append("../../../misc")  # Path to obs4MIPsLib used to trap provenance

# ── Dataset-specific settings (keep in sync with runCMOR_HadCRUT5.1.0.0-ensembles.py) ──
cmorTable      = '../../../../Tables/obs4MIPs_Amon.json'
cvTable        = '../../../../Tables/obs4MIPs_CV.json'
inputJson      = 'HadCRUT5.1.0.0-ensembles.json'
inputVarName   = 'tas'
outputVarName  = 'tastosanom-MOHC'
zipUrlTemplate = ('https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/'
                   'HadCRUT.5.1.0.0.analysis.anomalies.{lo}_to_{hi}_netcdf.zip')
zipRanges      = [(lo, lo + 9) for lo in range(1, 200, 10)]
SAMPLE_MEMBER  = 1   # Which realisation number to fully download & inspect

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
WARN = "\033[93mWARN\033[0m"
INFO = "\033[96mINFO\033[0m"

_issues = []

def check(label, condition, detail=""):
    tag = PASS if condition else FAIL
    print(f"  [{tag}] {label}")
    if not condition:
        if detail:
            print(f"         {detail}")
        _issues.append((label, detail))
    return condition

def info(label, value):
    print(f"  [{INFO}] {label}: {value}")

def warn(label, detail=""):
    print(f"  [{WARN}] {label}")
    if detail:
        print(f"         {detail}")
    _issues.append((label, detail))

# ── 1. Imports ───────────────────────────────────────────────────────────────
print("\n1. Checking imports")
for pkg, hint in [
    ("xarray",      ""),
    ("xcdat",       "pip install xcdat"),
    ("cmor",        "conda install -c conda-forge cmor"),
    ("obs4MIPsLib", "is ../../../misc on your path?"),
]:
    try:
        __import__(pkg)
        check(f"{pkg} importable", True)
    except ImportError as e:
        check(f"{pkg} importable", False, f"{e}{' -- ' + hint if hint else ''}")

# ── 2. Local files ─────────────────────────────────────────────────────────────
print("\n2. Checking local files")
check("inputJson exists", os.path.isfile(inputJson), f"Not found: {inputJson}")
check("cmorTable exists", os.path.isfile(cmorTable), f"Not found: {cmorTable}")
check("cvTable exists",   os.path.isfile(cvTable),   f"Not found: {cvTable}")

# ── 3. JSON config content ──────────────────────────────────────────────────
print("\n3. Checking inputJson content")
cfg = {}
if os.path.isfile(inputJson):
    with open(inputJson) as fh:
        cfg = json.load(fh)
    for k in ['institution_id', 'source_id', 'variant_label', 'grid_label',
              'license', 'references', 'contact']:
        check(f"key '{k}' present", k in cfg, f"Missing from {inputJson}")
    info("variant_label (base, before per-member '-rNNN' suffix)", cfg.get('variant_label', '(missing)'))
    info("has_aux_unc", cfg.get('has_aux_unc', '(missing)'))
    retrieval_date = cfg.get('source_data_retrieval_date', '')
    if not retrieval_date.strip():
        warn("source_data_retrieval_date is blank",
             "Set this to the actual download date for provenance (e.g. '2026-07-02')")

# ── 4. CV lookup ─────────────────────────────────────────────────────────────
print("\n4. Checking CV tables")
if os.path.isfile(cvTable) and cfg:
    with open(cvTable) as fh:
        cv = json.load(fh)
    inst = cfg.get('institution_id', '')
    src  = cfg.get('source_id', '')
    check(f"institution_id '{inst}' in CV", inst in cv.get('CV', {}).get('institution_id', {}))
    check(f"source_id '{src}' in CV",       src in cv.get('CV', {}).get('source_id', {}))

# ── 5. CMOR table variable lookup ───────────────────────────────────────────
print("\n5. Checking CMOR table variable entry")
if os.path.isfile(cmorTable):
    with open(cmorTable) as fh:
        tbl = json.load(fh)
    present = outputVarName in tbl.get('variable_entry', {})
    check(f"outputVarName '{outputVarName}' in Amon table", present)
    if present:
        tbl_var = tbl['variable_entry'][outputVarName]
        info("out_name", tbl_var.get('out_name', '(not set)'))
        if tbl_var.get('units') == '1':
            warn("Table units='1' is scientifically incorrect for a temperature anomaly",
                 "Expected 'K'; same known table issue as the ensemble-mean dataset - raise with PCMDI")

# ── 6. Zip URL reachability (HEAD only, no download) ────────────────────────
print("\n6. Checking all 20 zip URLs are reachable (HEAD request, no download)")
for lo, hi in zipRanges:
    url = zipUrlTemplate.format(lo=lo, hi=hi)
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=30) as resp:
            size_mb = int(resp.headers.get('Content-Length', 0)) / 1e6
            check(f"{lo:3d}_to_{hi:3d}.zip reachable ({size_mb:.0f} MB)", resp.status == 200,
                  f"HTTP status {resp.status}")
    except Exception as e:
        check(f"{lo:3d}_to_{hi:3d}.zip reachable", False, str(e))

# ── 7. Full inspection of one representative sample member ─────────────────
print(f"\n7. Downloading and inspecting sample member r{SAMPLE_MEMBER:03d} in depth")
_lo = ((SAMPLE_MEMBER - 1) // 10) * 10 + 1
_hi = _lo + 9
_zip_url = zipUrlTemplate.format(lo=_lo, hi=_hi)
_member_name = f"HadCRUT.5.1.0.0.analysis.anomalies.{SAMPLE_MEMBER}.nc"
print(f"         Zip containing sample member: {_zip_url}")

_tmpdir = tempfile.TemporaryDirectory()
try:
    _zip_path = os.path.join(_tmpdir.name, os.path.basename(_zip_url))
    urllib.request.urlretrieve(_zip_url, _zip_path)
    check("Download sample zip", True)

    with zipfile.ZipFile(_zip_path) as zf:
        zf.extract(_member_name, _tmpdir.name)
    _member_path = os.path.join(_tmpdir.name, _member_name)

    f = xr.open_dataset(_member_path, decode_times=False)
    check("Sample member file opens", True)
    check(f"Variable '{inputVarName}' present", inputVarName in f.data_vars,
          f"Available variables: {list(f.data_vars)}")

    if inputVarName in f.data_vars:
        d = f[inputVarName]

        info("shape", str(d.shape))
        info("dtype (source)", str(d.dtype))
        info("units attribute (source)", d.attrs.get('units', '(not set)'))
        check("Source units already 'K' (unlike the ensemble-mean's mislabeled source variable)",
              d.attrs.get('units', '').strip() == 'K',
              f"Got: {d.attrs.get('units')}")

        # ── Missing data: source declares a -1e30 _FillValue, but xarray auto-decodes it to NaN on open ──
        fill = d.encoding.get('_FillValue', d.attrs.get('_FillValue', None))
        info("_FillValue in source encoding", str(fill))
        vals = d.values
        nan_count = int(np.sum(np.isnan(vals)))
        check("_FillValue declared in source (auto-decoded to NaN by xarray)",
              fill is not None,
              "No _FillValue found in attrs/encoding — masking logic in runCMOR script assumes NaN-decoded missing values")
        check("Missing values present as NaN after decoding (masking logic in runCMOR script uses np.isnan)",
              nan_count > 0,
              f"Found {nan_count} NaNs — expected some missing cells given HadCRUT5's historical coverage gaps")
        info("cells that are NaN (missing)", f"{nan_count:,} of {vals.size:,} ({100*nan_count/vals.size:.1f}%)")

        finite = vals[np.isfinite(vals)]

        # Float32 precision impact
        f32 = finite.astype(np.float32)
        max_abs_diff = float(np.abs(finite.astype(np.float64) - f32.astype(np.float64)).max()) if len(finite) else 0.0
        check("Float32 precision loss acceptable (max error < 0.001 K)",
              max_abs_diff < 1e-3,
              f"Max error = {max_abs_diff:.4e}")

        # Plausibility
        _abs_max = float(np.abs(finite).max())
        check(f"Max |anomaly| ({_abs_max:.2f} K) < 25 K — plausible for a surface temperature anomaly",
              _abs_max < 25,
              f"Max = {_abs_max:.2f} K")

        # Latitude / longitude
        lat_vals = f.latitude.values
        lon_vals = f.longitude.values
        info("latitude range", f"{lat_vals.min():.2f} to {lat_vals.max():.2f}")
        info("longitude range (source convention)", f"{lon_vals.min():.2f} to {lon_vals.max():.2f}")
        check("Latitude is ascending (S→N) — no CMOR flip required",
              bool(lat_vals[0] < lat_vals[-1]))
        if lon_vals.min() < 0:
            info("Longitude convention", "-180→180 — CMOR will convert to 0→360 in the output (see HadCRUT/ notes)")

        # Bounds already present in source (unlike the ensemble mean, which needed xcdat to generate them)
        check("latitude_bnds present in source", 'latitude_bnds' in f)
        check("longitude_bnds present in source", 'longitude_bnds' in f)
        check("time_bnds present in source", 'time_bnds' in f)

        # realization scalar coordinate
        if 'realization' in f.variables:
            info("realization variable value", int(f['realization'].values))
            check(f"realization variable matches filename index ({SAMPLE_MEMBER})",
                  int(f['realization'].values) == SAMPLE_MEMBER,
                  f"File claims to be member {SAMPLE_MEMBER} but realization variable = {int(f['realization'].values)}")

    f.close()

except Exception as e:
    check("Sample member accessible", False, str(e))

finally:
    print(f"\n         Removing temporary directory: {_tmpdir.name}")
    _tmpdir.cleanup()

# ── 8. Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 72)
print("SUMMARY")
print("=" * 72)
print("""
Key differences from the ensemble-mean pipeline (test_HadCRUT5.1.0.0.py) to
be aware of before running runCMOR_HadCRUT5.1.0.0-ensembles.py:

  1. Variable name is 'tas' (not 'tas_mean'), and its source units are
     already 'K' — correct, unlike the ensemble mean's mislabeled source.
  2. Missing data is declared via a -1e30 _FillValue attribute, which
     xarray/xcdat auto-decode to NaN on open (confirmed empirically) — same
     as the ensemble-mean file, so the runCMOR script's masking logic uses
     np.isnan(), consistent with the mean script.
  3. lat/lon/time bounds are already present in each source file, so no
     synthetic bounds should normally be generated.
  4. Same known table units bug ('1' instead of 'K') applies here too.
  5. This script only inspects ONE sample member (r%03d) in depth. All 200
     members share the same grid/format from the same data provider, but
     if you have reason to suspect inconsistency between members, increase
     SAMPLE_MEMBER coverage or run validate_HadCRUT5.1.0.0-ensembles.py
     after the full conversion, which checks every output file.
""" % SAMPLE_MEMBER)

if _issues:
    print(f"  {len(_issues)} issue(s) flagged during checks (see FAILs/WARNs above).\n")
else:
    print("  All automated checks passed.\n")

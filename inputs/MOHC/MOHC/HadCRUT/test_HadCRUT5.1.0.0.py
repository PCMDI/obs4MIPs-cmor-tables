"""
Pre-flight checks for runCMOR_HadCRUT5.1.0.0.py
Validates imports, local config files, CV/table entries, and the source data
before running the full CMORization. Safe to re-run at any time.
Usage: python test_HadCRUT5.1.0.0.py
"""
import json
import sys
import os
import numpy as np
import urllib.request
import tempfile
import xarray as xr

sys.path.append("../../../misc")

# ── Dataset-specific settings (update these for a different dataset) ───────────
cmorTable     = '../../../../Tables/obs4MIPs_Amon.json'
cvTable       = '../../../../Tables/obs4MIPs_CV.json'
inputJson     = 'HadCRUT5.1.0.0.json'
inputVarName  = 'tas_mean'
outputVarName = 'tastosanom-MOHC'
sourceURL     = 'https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/HadCRUT.5.1.0.0.analysis.anomalies.ensemble_mean.nc'

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

def check(label, condition, detail=""):
    print(f"  [{PASS if condition else FAIL}] {label}")
    if not condition and detail:
        print(f"         {detail}")
    return condition

# ── 1. Imports ─────────────────────────────────────────────────────────────────
print("\n1. Checking imports")
for pkg, hint in [
    ("xarray",      ""),
    ("xcdat",       ""),
    ("cmor",        ""),
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

# ── 3. JSON content ────────────────────────────────────────────────────────────
print("\n3. Checking inputJson content")
cfg = {}
if os.path.isfile(inputJson):
    with open(inputJson) as fh:
        cfg = json.load(fh)
    for k in ['institution_id', 'source_id', 'variant_label', 'grid_label',
              'license', 'references', 'contact']:
        check(f"  key '{k}' present", k in cfg, f"Missing from {inputJson}")
    # Dataset-specific value checks - update these for a different dataset
    check(f"institution_id = MOHC-CRU-NCAS", cfg.get('institution_id') == 'MOHC-CRU-NCAS',
          f"Got: {cfg.get('institution_id')}")
    check(f"source_id = HadCRUT5-0-2-0", cfg.get('source_id') == 'HadCRUT5-0-2-0',
          f"Got: {cfg.get('source_id')}")

# ── 4. CV lookup ───────────────────────────────────────────────────────────────
print("\n4. Checking CV tables")
if os.path.isfile(cvTable) and cfg:
    with open(cvTable) as fh:
        cv = json.load(fh)
    inst = cfg.get('institution_id', '')
    src  = cfg.get('source_id', '')
    check(f"institution_id '{inst}' in CV",
          inst in cv.get('CV', {}).get('institution_id', {}),
          "Add it to obs4MIPs_CV.json or check the value")
    check(f"source_id '{src}' in CV",
          src in cv.get('CV', {}).get('source_id', {}),
          "Add it to obs4MIPs_CV.json or check the value")

# ── 5. CMOR table variable lookup ──────────────────────────────────────────────
print("\n5. Checking CMOR table")
if os.path.isfile(cmorTable):
    with open(cmorTable) as fh:
        tbl = json.load(fh)
    check(f"outputVarName '{outputVarName}' in Amon table",
          outputVarName in tbl.get('variable_entry', {}),
          f"'{outputVarName}' not found in {cmorTable}")

# ── 6. Source data file ────────────────────────────────────────────────────────
print("\n6. Checking source data file")
print(f"         Downloading from: {sourceURL}")
_tmpdir = tempfile.TemporaryDirectory()
_inputFilePath = os.path.join(_tmpdir.name, os.path.basename(sourceURL))

try:
    urllib.request.urlretrieve(sourceURL, _inputFilePath)
    check("Download from source URL", True)

    f = xr.open_dataset(_inputFilePath, decode_times=False)
    check("Input file opens", True)
    check(f"Variable '{inputVarName}' present",
          inputVarName in f.data_vars,
          f"Available variables: {list(f.data_vars)}")

    lat_name = next((c for c in f.coords if c in ('lat', 'latitude')), None)
    lon_name = next((c for c in f.coords if c in ('lon', 'longitude')), None)
    check("Latitude coordinate found",  lat_name is not None, f"Coords: {list(f.coords)}")
    check("Longitude coordinate found", lon_name is not None, f"Coords: {list(f.coords)}")

    if inputVarName in f.data_vars:
        d = f[inputVarName]
        finite = d.values[np.isfinite(d.values)]
        print(f"\n         Variable summary:")
        print(f"           shape      : {d.shape}")
        print(f"           dtype      : {d.dtype}")
        print(f"           units attr : {d.attrs.get('units', '(not set)')}")
        print(f"           time units : {f.time.attrs.get('units', '(not set)')}")
        print(f"           lat coord  : '{lat_name}',  lon coord: '{lon_name}'")
        if len(finite):
            print(f"           data range : {finite.min():.3f} to {finite.max():.3f}")
    f.close()

except Exception as e:
    check("Source data accessible", False, str(e))

finally:
    print(f"\n         Removing temporary directory: {_tmpdir.name}")
    _tmpdir.cleanup()

# ── Summary ────────────────────────────────────────────────────────────────────
print("\nDone. Fix any FAILs above before running the main script.\n")


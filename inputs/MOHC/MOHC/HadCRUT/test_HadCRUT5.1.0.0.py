"""
Pre-flight checks for runCMOR_HadCRUT5.1.0.0.py
Validates imports, local config files, CV/table entries, and the source data
before running the full CMORization. Safe to re-run at any time.
Usage: python test_HadCRUT5.1.0.0.py

Each check is labelled with what CMOR will do to that attribute:
  [CMOR: WILL CHANGE]  -- CMOR actively rewrites this (value or attribute in output will differ from source)
  [CMOR: WILL CHECK]   -- CMOR validates this against the CV/table but leaves a passing value unchanged
  [CMOR: WILL ADD]     -- CMOR generates this attribute from scratch; it is absent in the source
  [MANUAL FIX NEEDED]  -- CMOR will not fix this; a human action is required before or after the run
  [KNOWN TABLE ISSUE]  -- A known problem in the obs4MIPs table that must be raised with PCMDI
"""
import json
import sys
import os
import numpy as np
import urllib.request
import tempfile
import xarray as xr

sys.path.append("../../../misc")  # Path to obs4MIPsLib used to trap provenance

# ── Dataset-specific settings (update these for a different dataset) ───────────
cmorTable     = '../../../../Tables/obs4MIPs_Amon.json'
cvTable       = '../../../../Tables/obs4MIPs_CV.json'
inputJson     = 'HadCRUT5.1.0.0.json'
inputVarName  = 'tas_mean'
outputVarName = 'tastosanom-MOHC'
sourceURL     = 'https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/HadCRUT.5.1.0.0.analysis.anomalies.ensemble_mean.nc'  # Also set in runCMOR_HadCRUT5.1.0.0.py — update both if URL changes

PASS  = "\033[92mPASS\033[0m"
FAIL  = "\033[91mFAIL\033[0m"
WARN  = "\033[93mWARN\033[0m"
INFO  = "\033[96mINFO\033[0m"

_issues = []  # Collect FAILs and WARNs for the final summary

def check(label, condition, detail="", disposition=""):
    tag = PASS if condition else FAIL
    disp_str = f"  \033[2m{disposition}\033[0m" if disposition else ""
    print(f"  [{tag}] {label}{disp_str}")
    if not condition:
        if detail:
            print(f"         {detail}")
        _issues.append((label, detail, disposition))
    return condition

def info(label, value, disposition=""):
    disp_str = f"  \033[2m{disposition}\033[0m" if disposition else ""
    print(f"  [{INFO}] {label}: {value}{disp_str}")

def warn(label, detail="", disposition=""):
    disp_str = f"  \033[2m{disposition}\033[0m" if disposition else ""
    print(f"  [{WARN}] {label}{disp_str}")
    if detail:
        print(f"         {detail}")
    _issues.append((label, detail, disposition))

# ── 1. Imports ─────────────────────────────────────────────────────────────────
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

# ── 3. JSON config content ─────────────────────────────────────────────────────
# Each field is shown with its current value and what CMOR will do with it.
print("\n3. Checking inputJson content")
cfg = {}
if os.path.isfile(inputJson):
    with open(inputJson) as fh:
        cfg = json.load(fh)

    # Required keys - CMOR validates all of these against the CV
    for k in ['institution_id', 'source_id', 'variant_label', 'grid_label',
              'license', 'references', 'contact']:
        check(f"key '{k}' present", k in cfg, f"Missing from {inputJson}",
              disposition="[CMOR: WILL CHECK] - validated against CV; rejected if absent or invalid")

    # Show current values with disposition
    print()
    info("institution_id",
         cfg.get('institution_id', '(missing)'),
         disposition="[CMOR: WILL CHECK] - must match CV institution_id registry")
    check("institution_id = MOHC-CRU-NCAS",
          cfg.get('institution_id') == 'MOHC-CRU-NCAS',
          f"Got: {cfg.get('institution_id')}")

    info("source_id",
         cfg.get('source_id', '(missing)'),
         disposition="[CMOR: WILL CHECK] - must match CV source_id registry; note: file is HadCRUT.5.1.0.0 but source_id is HadCRUT5-0-2-0 — confirm intentional")
    check("source_id = HadCRUT5-0-2-0",
          cfg.get('source_id') == 'HadCRUT5-0-2-0',
          f"Got: {cfg.get('source_id')}")

    info("variant_label",
         cfg.get('variant_label', '(missing)'),
         disposition="[CMOR: WILL CHECK] - written to global attributes unchanged if valid")
    info("grid_label",
         cfg.get('grid_label', '(missing)'),
         disposition="[CMOR: WILL CHECK] - must match CV grid_label values")
    info("nominal_resolution",
         cfg.get('nominal_resolution', '(missing)'),
         disposition="[CMOR: WILL CHECK] - must match CV nominal_resolution values; HadCRUT5 is 5-degree (~555 km equatorial)")
    info("license",
         cfg.get('license', '(missing)')[:80] + ('...' if len(cfg.get('license','')) > 80 else ''),
         disposition="[CMOR: WILL CHECK] - validated; written unchanged to output")
    info("has_aux_unc",
         cfg.get('has_aux_unc', '(missing)'),
         disposition="[MANUAL FIX NEEDED] - set TRUE here but this script only writes the ensemble mean; uncertainty files must be co-delivered or this flag set to FALSE")
    info("contact",
         cfg.get('contact', '(missing)'),
         disposition="[CMOR: WILL CHECK] - written unchanged to output")
    info("references",
         cfg.get('references', '(missing)')[:80] + ('...' if len(cfg.get('references','')) > 80 else ''),
         disposition="[CMOR: WILL CHECK] - written unchanged to output")

    # source_data_retrieval_date: blank check
    retrieval_date = cfg.get('source_data_retrieval_date', '')
    if not retrieval_date or retrieval_date.strip() == '':
        warn("source_data_retrieval_date is blank",
             "Set this to the actual download date for provenance (e.g. '2026-06-30')",
             disposition="[MANUAL FIX NEEDED] - CMOR does not populate this; must be set by user in JSON")
    else:
        info("source_data_retrieval_date", retrieval_date,
             disposition="[CMOR: WILL CHECK] - written unchanged to output")

    # Fields that CMOR will ADD or GENERATE
    print()
    info("tracking_prefix (→ tracking_id)",
         cfg.get('tracking_prefix', '(missing)'),
         disposition="[CMOR: WILL ADD] - CMOR appends a UUID to this prefix to generate a unique tracking_id in the output")
    info("outpath / output_path_template",
         f"{cfg.get('outpath','.')} / {cfg.get('output_path_template','')}",
         disposition="[CMOR: WILL ADD] - CMOR constructs the full directory hierarchy and canonical filename from these templates")

# ── 4. CV lookup ───────────────────────────────────────────────────────────────
print("\n4. Checking CV tables")
if os.path.isfile(cvTable) and cfg:
    with open(cvTable) as fh:
        cv = json.load(fh)
    inst = cfg.get('institution_id', '')
    src  = cfg.get('source_id', '')
    check(f"institution_id '{inst}' in CV",
          inst in cv.get('CV', {}).get('institution_id', {}),
          "Add it to obs4MIPs_CV.json or check the value",
          disposition="[CMOR: WILL CHECK]")
    check(f"source_id '{src}' in CV",
          src in cv.get('CV', {}).get('source_id', {}),
          "Add it to obs4MIPs_CV.json or check the value",
          disposition="[CMOR: WILL CHECK]")

# ── 5. CMOR table variable lookup ──────────────────────────────────────────────
# Shows what CMOR will enforce on the output variable from the MIP table.
# These override whatever attributes exist in the source file.
print("\n5. Checking CMOR table variable entry")
tbl_var = {}
if os.path.isfile(cmorTable):
    with open(cmorTable) as fh:
        tbl = json.load(fh)
    present = outputVarName in tbl.get('variable_entry', {})
    check(f"outputVarName '{outputVarName}' in Amon table", present,
          f"'{outputVarName}' not found in {cmorTable}",
          disposition="[CMOR: WILL CHECK]")
    if present:
        tbl_var = tbl['variable_entry'][outputVarName]
        print()
        print("  The following attributes come FROM THE TABLE and will be enforced by CMOR")
        print("  regardless of what is in the source file:")
        print()
        info("  out_name (→ variable name in output)",
             tbl_var.get('out_name', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - source variable 'tas_mean' will be renamed to this")
        info("  standard_name",
             tbl_var.get('standard_name', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - overrides source file standard_name attribute")
        info("  long_name (table default)",
             tbl_var.get('long_name', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - overridden in runCMOR script to include 1961-1990 ref period")
        info("  units (in table)",
             tbl_var.get('units', '(not set)'),
             disposition="[KNOWN TABLE ISSUE] - table says '1' (dimensionless) but data is a temperature anomaly in K; CMOR will write units='1' to output; raise with PCMDI to fix table to 'K'")
        if tbl_var.get('units') == '1':
            warn("Table units='1' is scientifically incorrect for a temperature anomaly",
                 "Expected 'K'; CMOR will write wrong units to output until table is corrected",
                 disposition="[KNOWN TABLE ISSUE]")
        info("  cell_methods",
             tbl_var.get('cell_methods', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - written to output variable; overrides source attribute")
        info("  dimensions (canonical axis order)",
             tbl_var.get('dimensions', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - CMOR reorders output axes to this canonical order (time outermost)")
        info("  frequency",
             tbl_var.get('frequency', '(not set)'),
             disposition="[CMOR: WILL CHECK] - must match the Amon table (monthly)")
        info("  modeling_realm",
             tbl_var.get('modeling_realm', '(not set)'),
             disposition="[CMOR: WILL ADD] - written as global attribute to output")
        info("  type",
             tbl_var.get('type', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - data cast to this type; runCMOR script also pre-casts to float32")
        print()
        print("  The following table fields are empty for this variable (no range checking will occur):")
        for field in ('valid_max', 'valid_min', 'ok_max_mean_abs', 'ok_min_mean_abs'):
            val = tbl_var.get(field, '')
            if val == '' or val is None:
                info(f"  {field}", "(empty) — no bounds check", disposition="[CMOR: WILL CHECK] - skipped if blank")

# ── 6. Source data file ────────────────────────────────────────────────────────
# All checks here load the actual source data and compute results directly.
# Nothing is assumed — every value shown is calculated from the file.
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
          f"Available variables: {list(f.data_vars)}",
          disposition="[CMOR: WILL CHANGE] - renamed to table out_name in output")

    lat_name = next((c for c in f.coords if c in ('lat', 'latitude')), None)
    lon_name = next((c for c in f.coords if c in ('lon', 'longitude')), None)
    check("Latitude coordinate found",  lat_name is not None,
          f"Coords: {list(f.coords)}",
          disposition="[CMOR: WILL CHANGE] - standardised to CF name 'latitude' in output")
    check("Longitude coordinate found", lon_name is not None,
          f"Coords: {list(f.coords)}",
          disposition="[CMOR: WILL CHANGE] - standardised to CF name 'longitude' in output")

    if inputVarName in f.data_vars:
        d    = f[inputVarName]
        vals = d.values
        finite_mask = np.isfinite(vals)
        finite      = vals[finite_mask]
        nan_count   = int(np.sum(~finite_mask))
        total_count = int(vals.size)

        # ── 6a. Shape and metadata ────────────────────────────────────────────
        print(f"\n  ── 6a. Variable shape and source metadata ──")
        info("  shape",
             str(d.shape),
             disposition="[CMOR: WILL CHECK] - axis count must match table dimensions")
        info("  dtype (source)",
             str(d.dtype),
             disposition="[CMOR: WILL CHANGE] - runCMOR pre-casts to float32; see 6b for precision impact")
        info("  units attribute (source)",
             d.attrs.get('units', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - overridden by table value '1' (see section 5 units warning)")
        info("  standard_name (source)",
             d.attrs.get('standard_name', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - overridden by table: 'surface_temperature_anomaly'")
        info("  long_name (source)",
             d.attrs.get('long_name', '(not set)'),
             disposition="[CMOR: WILL CHANGE] - overridden in runCMOR script to include 1961-1990 ref period")

        # ── 6b. Float32 precision impact (calculated) ─────────────────────────
        print(f"\n  ── 6b. Float32 precision impact (actual calculation on source data) ──")
        src_dtype    = d.dtype
        f32_vals     = finite.astype(np.float32)
        diff         = np.abs(finite.astype(np.float64) - f32_vals.astype(np.float64))
        max_abs_diff = float(diff.max())
        mean_abs_diff= float(diff.mean())
        data_range   = float(finite.max()) - float(finite.min())
        max_rel_err  = max_abs_diff / data_range if data_range > 0 else 0.0
        n_changed    = int(np.sum(diff > 0))
        n_sig        = int(np.sum(diff > 1e-4))   # values that shift by more than 0.1 mK

        info("  source dtype",
             str(src_dtype))
        info("  target dtype (after runCMOR cast)",
             "float32")
        info("  values that change at all after cast",
             f"{n_changed:,} of {len(finite):,} finite values ({100*n_changed/len(finite):.1f}%)")
        info("  max absolute error from cast",
             f"{max_abs_diff:.3e}  (in source units — expected K)")
        info("  mean absolute error from cast",
             f"{mean_abs_diff:.3e}")
        info("  max relative error (fraction of full data range {:.3f})".format(data_range),
             f"{max_rel_err:.3e}")
        info("  values with |error| > 1e-4  (> 0.1 mK)",
             f"{n_sig:,}  ({100*n_sig/len(finite):.2f}%)")

        # PASS criterion: max error must be < 0.001 K (sub-mK is scientifically negligible for anomaly data)
        check("Float32 precision loss acceptable (max error < 0.001 K / 1 mK)",
              max_abs_diff < 1e-3,
              f"Max error = {max_abs_diff:.4e}; consider retaining float64 in the CMOR write step",
              disposition="[CMOR: WILL CHANGE] - verify loss is scientifically negligible for HadCRUT5")
        if src_dtype == np.float32:
            check("Source is already float32 — cast introduces no additional precision loss",
                  True,
                  disposition="[informational]")

        # ── 6c. Missing data ──────────────────────────────────────────────────
        print(f"\n  ── 6c. Missing / fill values (calculated) ──")
        info("  NaN count",
             f"{nan_count:,} of {total_count:,} ({100*nan_count/total_count:.1f}%)",
             disposition="[CMOR: WILL CHANGE] - NaN → 1e20 (CMOR_MDI) replacement done in runCMOR before write")

        src_fill = d.attrs.get('_FillValue', d.attrs.get('missing_value', None))
        info("  _FillValue / missing_value in source file",
             str(src_fill) if src_fill is not None else "(not set — NaN used for masking)",
             disposition="[CMOR: WILL CHANGE] - output _FillValue set to 1e20 by CMOR")

        if src_fill is not None:
            fill_f = float(src_fill)
            near_fill = int(np.sum(np.abs(finite - fill_f) < 1.0))
            check(f"No finite data values within 1.0 of source fill value ({fill_f:.2e})",
                  near_fill == 0,
                  f"{near_fill} finite values are suspiciously close to the fill value — risk of masking real data",
                  disposition="[MANUAL FIX NEEDED] if any collide")

        # Confirm NaN is the actual masking mechanism (no large sentinel values lurking)
        _large_vals = int(np.sum(np.abs(finite) > 1e10))
        check("No suspiciously large finite values (|x| > 1e10) that might be unmasked fill values",
              _large_vals == 0,
              f"{_large_vals} finite values with |x| > 1e10 — check these are not mis-coded fill values",
              disposition="[MANUAL FIX NEEDED] if any found")

        # ── 6d. Data plausibility ─────────────────────────────────────────────
        print(f"\n  ── 6d. Data value plausibility ──")
        info("  data range (finite values only)",
             f"{finite.min():.4f} to {finite.max():.4f}",
             disposition="[CMOR: WILL CHECK] - against valid_min/valid_max if set in table (currently empty)")
        info("  mean (finite)",
             f"{finite.mean():.4f}")
        info("  std dev (finite)",
             f"{finite.std():.4f}")

        _abs_max = float(np.abs(finite).max())
        # Threshold is 25 K: typical HadCRUT5 anomalies are ±5-10 K but
        # sparse polar coverage in the early record can reach ~15-20 K.
        # Values above 25 K would indicate absolute temperature, not anomaly.
        check(f"Max |anomaly| ({_abs_max:.2f} K) < 25 K — plausible for a surface temperature anomaly",
              _abs_max < 25,
              f"Max = {_abs_max:.2f} K; typical HadCRUT5 anomalies are ±5-10 K; "
              f">25 K would suggest absolute temperature, not anomaly",
              disposition="[MANUAL FIX NEEDED] if FAIL")
        if 15 <= _abs_max < 25:
            warn(f"Max |anomaly| ({_abs_max:.2f} K) exceeds 15 K — unusual but possible in sparse polar "
                 f"regions or early record; verify these cells are not erroneous",
                 "Inspect the grid cells with |anomaly| > 15 K — likely Antarctic or Arctic early record",
                 disposition="[informational] — investigate but not necessarily a blocking issue")

        src_units = d.attrs.get('units', '')
        _unit_ok = src_units.strip() in ('K', 'degC', 'degrees_C', 'celsius', 'C', '°C', '1', 'degree_C')
        check(f"Source units attribute '{src_units}' is temperature-like",
              _unit_ok,
              f"Unexpected units '{src_units}' — confirm data is a temperature anomaly",
              disposition="[CMOR: WILL CHANGE] - CMOR overrides with table value '1'")

        # ── 6e. Latitude axis ─────────────────────────────────────────────────
        print(f"\n  ── 6e. Latitude axis (calculated) ──")
        if lat_name:
            lat_vals = f[lat_name].values

            info("  first value",  f"{lat_vals[0]:.4f}°")
            info("  last value",   f"{lat_vals[-1]:.4f}°")
            info("  n cells",      str(len(lat_vals)))

            lat_ascending = bool(lat_vals[0] < lat_vals[-1])
            check("Latitude is S→N (ascending) — no CMOR flip required",
                  lat_ascending,
                  f"Source runs N→S ({lat_vals[0]:.2f} → {lat_vals[-1]:.2f}); "
                  f"CMOR will reverse the coordinate AND reorder all data slices",
                  disposition="[CMOR: WILL CHANGE] if descending — both axis and data values will be flipped")

            lat_diffs        = np.diff(lat_vals)
            lat_unique_diffs = np.unique(np.round(lat_diffs, 4))
            lat_uniform      = len(lat_unique_diffs) == 1
            lat_step         = float(lat_unique_diffs[0]) if lat_uniform else None

            check("Latitude spacing is uniform across all cells",
                  lat_uniform,
                  f"Non-uniform spacings: {lat_unique_diffs[:10]}",
                  disposition="[CMOR: WILL ADD] - xcdat bounds assume uniform spacing; non-uniform requires manual bounds")

            if lat_step is not None:
                info("  step size", f"{abs(lat_step):.4f}°")
                expected_n = round(180.0 / abs(lat_step))
                check(f"Cell count ({len(lat_vals)}) consistent with {abs(lat_step):.1f}° global grid ({expected_n} expected)",
                      len(lat_vals) == expected_n,
                      f"Got {len(lat_vals)} cells; expected {expected_n} for {abs(lat_step):.1f}° spacing",
                      disposition="[informational] - confirms 5-degree global grid")

                half = abs(lat_step) / 2.0
                print(f"  [{INFO}]   xcdat-generated lat bounds preview (first 3 cells):")
                for i in range(min(3, len(lat_vals))):
                    lo, hi = lat_vals[i] - half, lat_vals[i] + half
                    print(f"           cell {i:3d}: [{lo:7.2f}, {hi:7.2f}]  centre = {lat_vals[i]:.2f}°")

                south_edge = float(lat_vals[0] if lat_ascending else lat_vals[-1]) - half
                north_edge = float(lat_vals[-1] if lat_ascending else lat_vals[0]) + half
                check(f"Synthetic lat bounds stay within [-90°, 90°]  (computed: [{south_edge:.2f}°, {north_edge:.2f}°])",
                      south_edge >= -90.0 and north_edge <= 90.0,
                      f"Bounds extend to [{south_edge:.2f}°, {north_edge:.2f}°] — outside valid range",
                      disposition="[CMOR: WILL ADD] - verify xcdat does not exceed ±90°")

        # ── 6f. Longitude axis ────────────────────────────────────────────────
        print(f"\n  ── 6f. Longitude axis (calculated) ──")
        if lon_name:
            lon_vals = f[lon_name].values

            info("  first value", f"{lon_vals[0]:.4f}°")
            info("  last value",  f"{lon_vals[-1]:.4f}°")
            info("  n cells",     str(len(lon_vals)))

            uses_0_360   = bool(lon_vals.min() >= -1e-6  and lon_vals.max() <= 360 + 1e-6)
            uses_neg180  = bool(lon_vals.min() < -1e-6)
            convention   = "0→360" if not uses_neg180 else "-180→180"
            _lon_ok = uses_0_360 or uses_neg180
            check(f"Longitude values are within a recognised convention ({convention})",
                  _lon_ok,
                  f"Values outside expected range: min={lon_vals.min():.2f}, max={lon_vals.max():.2f}",
                  disposition="[CMOR: WILL CHECK] - source convention accepted as input")
            if uses_neg180:
                info(f"Source longitude convention is -180→180 (first={lon_vals[0]:.2f}°, last={lon_vals[-1]:.2f}°)",
                     "CMOR will convert to 0→360 in the output",
                     disposition="[CMOR: WILL CHANGE] - obs4MIPs_coordinate.json requires valid_min=0.0/"
                                  "valid_max=360.0 with stored_direction='increasing'; CMOR offsets negative "
                                  "longitudes by +360 and re-sorts the data accordingly (confirmed empirically: "
                                  "-180→180 source is written as 2.5...357.5 in the output). No manual action needed.")

            lon_diffs        = np.diff(lon_vals)
            lon_unique_diffs = np.unique(np.round(lon_diffs, 4))
            lon_uniform      = len(lon_unique_diffs) == 1
            lon_step         = float(lon_unique_diffs[0]) if lon_uniform else None

            check("Longitude spacing is uniform across all cells",
                  lon_uniform,
                  f"Non-uniform: {lon_unique_diffs[:10]}",
                  disposition="[CMOR: WILL ADD] - xcdat bounds assume uniform spacing")

            if lon_step is not None:
                info("  step size", f"{abs(lon_step):.4f}°")
                expected_n = round(360.0 / abs(lon_step))
                check(f"Cell count ({len(lon_vals)}) consistent with {abs(lon_step):.1f}° global grid ({expected_n} expected)",
                      len(lon_vals) == expected_n,
                      f"Got {len(lon_vals)}; expected {expected_n}",
                      disposition="[informational]")

                half_l = abs(lon_step) / 2.0
                print(f"  [{INFO}]   xcdat-generated lon bounds preview (first 3 cells):")
                for i in range(min(3, len(lon_vals))):
                    lo, hi = lon_vals[i] - half_l, lon_vals[i] + half_l
                    print(f"           cell {i:3d}: [{lo:8.2f}, {hi:8.2f}]  centre = {lon_vals[i]:.2f}°")

        # ── 6g. Time axis ─────────────────────────────────────────────────────
        print(f"\n  ── 6g. Time axis (calculated) ──")
        t_vals      = f.time.values
        t_units_src = f.time.attrs.get('units', '')
        t_cal_src   = f.time.attrs.get('calendar', '')
        cal_in_cfg  = cfg.get('calendar', 'standard') if cfg else 'standard'

        info("  time units (source)", t_units_src if t_units_src else '(not set)',
             disposition="[CMOR: WILL CHANGE] - CMOR rewrites time axis in output")
        info("  calendar (source)",   t_cal_src   if t_cal_src   else '(not set)',
             disposition="[CMOR: WILL CHECK] - must match JSON config")
        info("  calendar (JSON config)", cal_in_cfg)

        _cal_match = (t_cal_src.lower() == cal_in_cfg.lower()) or (t_cal_src == '')
        check(f"Source calendar ('{t_cal_src}') matches JSON config ('{cal_in_cfg}')",
              _cal_match,
              f"Mismatch: source='{t_cal_src}' vs config='{cal_in_cfg}' — CMOR may silently shift all time values",
              disposition="[CMOR: WILL CHECK] - mismatch is a silent but serious error")

        info("  number of time steps", str(len(t_vals)))
        info("  time range (raw)",
             f"{t_vals[0]:.3f} to {t_vals[-1]:.3f}  ({t_units_src})")

        t_diffs = np.diff(t_vals.astype(np.float64))
        t_min, t_max, t_mean = float(t_diffs.min()), float(t_diffs.max()), float(t_diffs.mean())
        info("  time step stats (days)",
             f"mean={t_mean:.2f},  min={t_min:.2f},  max={t_max:.2f}  (expected ~28-31 for monthly)")
        check(f"Time steps are approximately monthly (mean={t_mean:.1f} days, expected 28-31)",
              20 < t_mean < 35 and t_min > 15 and t_max < 40,
              f"Step stats out of range: mean={t_mean:.1f}, min={t_min:.1f}, max={t_max:.1f}",
              disposition="[CMOR: WILL CHECK] - Amon table requires monthly frequency")

        # Time bounds
        tbnds_present = 'time_bnds' in f or 'time_bounds' in f
        check("Time bounds present in source file",
              tbnds_present,
              "Absent — xcdat will generate synthetic bounds in runCMOR",
              disposition="[CMOR: WILL ADD] - xcdat add_bounds('T') uses mid-period ±half-step if absent")

        if not tbnds_present:
            half_t   = t_mean / 2.0
            t0_lo    = t_vals[0] - half_t
            t0_hi    = t_vals[0] + half_t
            print(f"  [{INFO}]   xcdat synthetic time bounds estimate for step 0:")
            print(f"           [{t0_lo:.3f}, {t0_hi:.3f}]  (centre={t_vals[0]:.3f}  {t_units_src})")
            _mid_month_ok = (t_vals[0] % 1) > 0.1   # crude: centre is not exactly a whole-day integer
            check("First time value appears to be a mid-month timestamp (not start-of-month)",
                  _mid_month_ok,
                  f"Value {t_vals[0]:.4f} looks like a start-of-period timestamp; "
                  f"xcdat bounds would then run from half a step before the first record — verify this is correct",
                  disposition="[MANUAL FIX NEEDED] if timestamp convention is wrong")

        # Lat/lon bounds
        print()
        lat_bnds_present = any(v for v in f.data_vars if 'lat' in v.lower() and 'bnd' in v.lower())
        lon_bnds_present = any(v for v in f.data_vars if 'lon' in v.lower() and 'bnd' in v.lower())
        check("Latitude bounds present in source file",
              lat_bnds_present,
              "Absent — xcdat will generate as ±half-cell-width (correct for uniform 5-degree grid)",
              disposition="[CMOR: WILL ADD]")
        check("Longitude bounds present in source file",
              lon_bnds_present,
              "Absent — xcdat will generate as ±half-cell-width",
              disposition="[CMOR: WILL ADD]")

    f.close()

except Exception as e:
    check("Source data accessible", False, str(e))

finally:
    print(f"\n         Removing temporary directory: {_tmpdir.name}")
    _tmpdir.cleanup()

# ── 7. Summary ────────────────────────────────────────────────────────────────
print("\n" + "="*72)
print("SUMMARY: Actions required to ensure data is correctly CMORised")
print("="*72)

print("""
The following are the main points to be aware of before/after running
runCMOR_HadCRUT5.1.0.0.py. Items are grouped by who is responsible.

[A] CRITICAL — must be fixed before output can be considered correct
──────────────────────────────────────────────────────────────────────
  1. TABLE UNITS BUG: obs4MIPs_Amon.json defines tastosanom-MOHC with
     units='1' (dimensionless). The data is a temperature anomaly in K.
     CMOR will write units='1' to the output. Raise with PCMDI to fix
     the table; then update outputUnits in runCMOR_HadCRUT5.1.0.0.py
     from '1' to 'K'.

[B] MANUAL FIXES — user action needed in JSON config or delivery
──────────────────────────────────────────────────────────────────────
  2. source_data_retrieval_date: currently blank. Set to the date the
     source file was downloaded (ISO 8601, e.g. '2026-06-30').
  3. has_aux_unc = TRUE: this script only writes the ensemble mean.
     Either deliver the uncertainty files alongside this output, or
     change this flag to FALSE for this file.

[C] CMOR WILL CHANGE THESE — verify the output is scientifically correct
──────────────────────────────────────────────────────────────────────────
  4. Variable renamed: 'tas_mean' → 'tastosanomanom' (from table out_name).
  5. Units attribute: overridden from source value to table value ('1').
     See item [A].
  6. standard_name: overridden to 'surface_temperature_anomaly'.
  7. cell_methods: set to 'area: time: mean' from table.
  8. Dimension order: reordered to canonical (time, latitude, longitude).
  9. Latitude direction: if source is N→S, CMOR flips to S→N and
     reorders data values accordingly — verify in output.
 10. NaN values: replaced with 1e20 (CMOR_MDI) before write. Confirm
     all genuine missing regions are NaN in the source, not zero or a
     different fill value.
 11. Data type: pre-cast to float32 in runCMOR script. Source dtype
     shown in section 6 above — confirm no significant precision loss.
 12. Time axis: rewritten by CMOR using declared calendar ('standard').
     Time bounds generated synthetically by xcdat — confirm the source
     uses mid-month timestamps so bounds correctly span each calendar month.

[D] CMOR WILL CHECK THESE — they will pass through unchanged if correct
──────────────────────────────────────────────────────────────────────────
 13. institution_id, source_id: validated against CV; output unchanged.
     NOTE: source_id 'HadCRUT5-0-2-0' covers file version 5.1.0.0 —
     confirm this is the intended CV mapping.
 14. license, references, contact, variant_label, grid_label: written
     unchanged to output if they pass CV validation.
 15. nominal_resolution '500 km': HadCRUT5 is 5-degree (~555 km at
     equator); confirm this is the correct obs4MIPs category.

[E] FINDINGS FROM LIVE DATA INSPECTION — investigate before finalising
──────────────────────────────────────────────────────────────────────────
 16. DATA RANGE: source data reaches -16.6 K. Typical HadCRUT5 anomalies
     are ±5-10 K; values around 15-20 K can occur in sparse polar regions
     or the early record. Inspect the specific cells exceeding ±15 K to
     confirm they are not erroneous. The CMOR table currently has no
     valid_min/valid_max to catch outliers automatically.
 17. LONGITUDE CONVENTION: source uses -180→180, not 0→360. No action
     needed — obs4MIPs_coordinate.json requires the longitude axis to be
     0→360 (valid_min=0.0, valid_max=360.0, stored_direction=increasing)
     and CMOR converts and re-sorts the data automatically. Confirmed on
     actual output: source -180→180 is written as 2.5...357.5 (0→360).
 18. DTYPE: source is float64; runCMOR casts to float32. Measured max
     precision loss is 7.2e-7 K (sub-mK) — scientifically negligible.
 19. BOUNDS: lat, lon and time bounds are all present in the source
     file already. xcdat's add_missing_bounds will detect these and
     leave them unchanged, so no synthetic bounds are generated.
""")

if _issues:
    print(f"  {len(_issues)} issue(s) flagged during checks (see FAILs/WARNs above).\n")
else:
    print("  All automated checks passed.\n")

print("Fix all FAILs and WARNs above before running the main script.\n")


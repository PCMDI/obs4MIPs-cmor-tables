"""
CMORize all 200 HadCRUT5.1.0.0 ensemble members (observational uncertainty
realisations) for obs4MIPs.

Source: 20 zip files, each containing 10 per-realisation NetCDF files
(HadCRUT.5.1.0.0.analysis.anomalies.<N>.nc, N=1..200), downloaded from the
Met Office server and cached locally in RAW_CACHE_DIR (zips are kept between
runs so re-running this script does not re-download ~6.5 GB every time;
extracted per-member NetCDF files are deleted immediately after each member
is CMORized, to bound peak disk use).

Each member is written through CMOR independently (own cmor.setup/dataset_json
/load_table/close cycle per file), following the same pattern used in
inputs/NASA-GISS/RSS/PRW/runCMOR-PRW-Monthly-ensemble.py. Members are
distinguished by suffixing variant_label with "-rNNN" (zero-padded 1..200),
and all 200 outputs share a single fixed <version> so they land in the same
output directory even if the run spans more than one day / is resumed.

Usage:
    python runCMOR_HadCRUT5.1.0.0-ensembles.py             # process all 200 members
    python runCMOR_HadCRUT5.1.0.0-ensembles.py --limit 2   # smoke-test: only members 1-2
"""
import argparse
import cmor
import xcdat as xc
import numpy as np
import json
import os
import re
import sys
import tempfile
import urllib.request
import zipfile
from datetime import datetime

sys.path.append("../../../misc")  # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

# ── Dataset-specific settings ───────────────────────────────────────────────
cmorTable     = '../../../../Tables/obs4MIPs_Amon.json'
inputJson     = 'HadCRUT5.1.0.0-ensembles.json'
inputVarName  = 'tas'                     # Variable name in each per-member NetCDF (already in K, unlike the ensemble mean's 'tas_mean')
outputVarName = 'tastosanom-MOHC'         # Same table entry used for the ensemble mean
outputUnits   = '1'                       # TODO: CMOR table obs4MIPs_Amon.json defines tastosanom-MOHC with units="1" (dimensionless).
                                           # This should be "K" for temperature anomalies - same known table bug as the ensemble
                                           # mean script; raise with PCMDI to fix in master branch. Using "1" here to match the
                                           # table as-is (input data is declared/treated as already being in table units).

# Missing-data indicator used by CMOR. Source files declare a -1e30 _FillValue,
# but xarray/xcdat auto-decode this to NaN on open (confirmed empirically) - same
# masking behaviour as the ensemble mean file, so np.isnan() is used below.
CMOR_MDI = 1.e20

# ── Zip download settings ───────────────────────────────────────────────────
# sourceURL pattern is also referenced in test_HadCRUT5.1.0.0-ensembles.py — update both if it changes.
zipUrlTemplate = ('https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/'
                   'HadCRUT.5.1.0.0.analysis.anomalies.{lo}_to_{hi}_netcdf.zip')
zipRanges      = [(lo, lo + 9) for lo in range(1, 200, 10)]  # (1,10), (11,20), ..., (191,200)
RAW_CACHE_DIR  = './_raw_zips'   # Persistent local cache - NOT re-downloaded on subsequent runs. Add to .gitignore.
KEEP_ZIPS      = True            # Set False to delete each zip after its 10 members are processed (saves ~6.5GB once done)

# Fixed for the entire run so all 200 members land in the same <version> output folder,
# even if this script is re-run across multiple days to pick up any failed members.
run_version = "v" + datetime.now().strftime("%Y%m%d")

os.makedirs(RAW_CACHE_DIR, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--limit', type=int, default=200,
                     help='Only process the first N members (e.g. --limit 2 for a smoke test). Default: all 200.')
args = parser.parse_args()

with open(inputJson) as _fh:
    _cfg = json.load(_fh)
base_variant_label = _cfg.get('variant_label', 'MOHC')
_outpath  = _cfg.get('outpath', './')
print(f"Base variant_label : {base_variant_label}  (suffixed per-member below)")
print(f"Run version         : {run_version}  (fixed for this whole batch)")
print(f"Output will be written under: {os.path.abspath(_outpath)}")
if args.limit < 200:
    print(f"NOTE: --limit {args.limit} set - only the first {args.limit} member(s) will be processed.\n")
else:
    print()

member_name_re = re.compile(r'\.(\d+)\.nc$')

succeeded = []
failed    = []

for lo, hi in zipRanges:
    if len(succeeded) + len(failed) >= args.limit:
        break

    zip_name = f"HadCRUT.5.1.0.0.analysis.anomalies.{lo}_to_{hi}_netcdf.zip"
    zip_url  = zipUrlTemplate.format(lo=lo, hi=hi)
    zip_path = os.path.join(RAW_CACHE_DIR, zip_name)

    if os.path.isfile(zip_path):
        print(f"[zip {lo:3d}-{hi:3d}] cached: {zip_path}")
    else:
        print(f"[zip {lo:3d}-{hi:3d}] downloading: {zip_url}")
        urllib.request.urlretrieve(zip_url, zip_path)

    with zipfile.ZipFile(zip_path) as zf:
        members = sorted(zf.namelist(), key=lambda n: int(member_name_re.search(n).group(1)))

        for member_name in members:
            if len(succeeded) + len(failed) >= args.limit:
                break

            m = member_name_re.search(member_name)
            ridx = int(m.group(1))

            try:
                with tempfile.TemporaryDirectory() as td:
                    zf.extract(member_name, td)
                    member_path = os.path.join(td, member_name)

                    f = xc.open_dataset(member_path, decode_times=False)

                    # Source files already carry lat/lon/time bounds; only add if genuinely missing.
                    _has = lambda n: n in f or n in f.coords
                    if not (_has('latitude_bnds') or _has('lat_bnds')):
                        f = f.bounds.add_missing_bounds(axes=['Y'])
                    if not (_has('longitude_bnds') or _has('lon_bnds')):
                        f = f.bounds.add_missing_bounds(axes=['X'])
                    if not (_has('time_bnds') or _has('time_bounds')):
                        f = f.bounds.add_bounds('T')

                    d    = f[inputVarName]
                    lat  = f.latitude.values
                    lon  = f.longitude.values
                    time = f.time.values
                    tbds = f.time_bnds.values

                    # xarray/xcdat auto-decode the source's -1e30 _FillValue to NaN on open.
                    values = np.where(np.isnan(d.values), CMOR_MDI, d.values)
                    values = np.array(values, np.float32)

                    cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4)
                    cmor.dataset_json(inputJson)
                    cmor.load_table(cmorTable)
                    cmor.set_cur_dataset_attribute('history', f.attrs.get('history', ''))

                    variant_label = f"{base_variant_label}-r{ridx:03d}"
                    cmor.set_cur_dataset_attribute('variant_label', variant_label)
                    cmor.set_cur_dataset_attribute('version', run_version)

                    cmorLat  = cmor.axis("latitude",  coord_vals=lat[:],  cell_bounds=f.latitude_bnds.values,  units="degrees_north")
                    cmorLon  = cmor.axis("longitude", coord_vals=lon[:],  cell_bounds=f.longitude_bnds.values, units="degrees_east")
                    cmorTime = cmor.axis("time",      coord_vals=time[:], cell_bounds=tbds,                    units=f.time.units)
                    cmoraxes = [cmorTime, cmorLat, cmorLon]

                    varid = cmor.variable(outputVarName, outputUnits, cmoraxes, missing_value=CMOR_MDI)

                    cmor.set_variable_attribute(varid, 'long_name', 'c',
                        'Near-surface land and ocean temperature monthly mean anomalies from the 1961-1990 climatological reference period')
                    cmor.set_variable_attribute(varid, 'units_metadata', 'c', 'temperature: difference')

                    git_commit_number = obs4MIPsLib.get_git_revision_hash()
                    path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
                    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
                    cmor.set_cur_dataset_attribute("processing_code_location", f"{full_git_path}")

                    cmor.set_deflate(varid, 1, 1, 1)
                    cmor.write(varid, values, len(time))
                    outfile = cmor.close(varid, file_name=True)
                    f.close()

                succeeded.append(ridx)
                print(f"[member {ridx:3d}/{args.limit}] {variant_label} -> {outfile}")

            except Exception as e:
                failed.append((ridx, str(e)))
                print(f"[member {ridx:3d}/{args.limit}] FAILED: {e}")

    if not KEEP_ZIPS:
        os.remove(zip_path)
        print(f"[zip {lo:3d}-{hi:3d}] removed cached zip (KEEP_ZIPS=False)")

print("\n" + "=" * 72)
print(f"Done. {len(succeeded)}/{args.limit} members written successfully.")
if failed:
    print(f"{len(failed)} member(s) FAILED:")
    for ridx, err in failed:
        print(f"  r{ridx:03d}: {err}")
    print("Re-run this script to retry — cached zips mean only the failed")
    print("member(s) will need extracting again, not re-downloading.")
print("=" * 72)

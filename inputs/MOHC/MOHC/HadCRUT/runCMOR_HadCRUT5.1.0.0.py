import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import urllib.request
import tempfile
import json
import sys, os

sys.path.append("../../../misc")  # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable     = '../../../../Tables/obs4MIPs_Amon.json'  # Load target table, axis info (coordinates, grid*) and CVs
inputJson     = 'HadCRUT5.1.0.0.json'                    # Update contents of this file to set global_attributes
inputVarName  = 'tas_mean'                               # Variable name in the HadCRUT5 ensemble mean NetCDF
outputVarName = 'tastosanom-MOHC'                        # Variable name as defined in obs4MIPs_Amon.json
outputUnits   = '1'                                      # TODO: CMOR table obs4MIPs_Amon.json defines tastosanom-MOHC with units="1" (dimensionless).
                                                         # This should be "K" for temperature anomalies - raise with PCMDI to fix in master branch.
                                                         # Using "1" here to match the table as-is so the script runs locally.

# ── Download input data ────────────────────────────────────────────────────────
# The Met Office HadObs server does not support OPeNDAP, so the file is always
# downloaded fresh from the official source URL into a temporary directory.
# This avoids any dependency on local file paths and ensures reproducibility for
# all users. The temporary directory is removed automatically when the script ends.
sourceURL = 'https://www.metoffice.gov.uk/hadobs/hadcrut5/data/HadCRUT.5.1.0.0/analysis/HadCRUT.5.1.0.0.analysis.anomalies.ensemble_mean.nc'
print(f"\n[1/6] Downloading input data")
print(f"      Source : {sourceURL}")
_tmpdir = tempfile.TemporaryDirectory()
inputFilePath = os.path.join(_tmpdir.name, os.path.basename(sourceURL))
urllib.request.urlretrieve(sourceURL, inputFilePath)
print(f"      Saved to temporary directory: {_tmpdir.name}")

# ── Open and read input netcdf file, get coordinates and add bounds ────────────
print(f"\n[2/6] Reading input file")
f = xc.open_dataset(inputFilePath, decode_times=False)
d = f[inputVarName]
lat  = f.latitude.values
lon  = f.longitude.values
time = f.time.values
print(f"      Variable  : {inputVarName}  {d.shape}  ({d.dtype})")
print(f"      Time range: {f.time.values[0]:.1f} to {f.time.values[-1]:.1f} ({f.time.attrs.get('units', '')})")
print(f"      Grid      : {len(lat)} lats x {len(lon)} lons")
f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

# Replace NaNs with CMOR missing value
d = np.where(np.isnan(d), 1.e20, d)

# ── Read output settings from JSON to show user where output will be written ───
with open(inputJson) as _fh:
    _cfg = json.load(_fh)
_outpath  = _cfg.get('outpath', './')
_path_tpl = _cfg.get('output_path_template', '')
_file_tpl = _cfg.get('output_file_template', '')
print(f"\n[3/6] Initialising CMOR")
print(f"      Config    : {inputJson}")
print(f"      CV/Tables : {cmorTable}")
print(f"      Output will be written under: {os.path.abspath(_outpath)}")
print(f"      Path template : {_path_tpl}")
print(f"      File template : {_file_tpl}")

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4)  # ,logfile='cmorLog.txt'
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history', f.attrs.get('history', ''))

# ── Create CMOR axes ───────────────────────────────────────────────────────────
print(f"\n[4/6] Creating CMOR axes")
cmorLat  = cmor.axis("latitude",  coord_vals=lat[:],  cell_bounds=f.latitude_bnds.values,  units="degrees_north")
cmorLon  = cmor.axis("longitude", coord_vals=lon[:],  cell_bounds=f.longitude_bnds.values,  units="degrees_east")
cmorTime = cmor.axis("time",      coord_vals=time[:], cell_bounds=tbds,                     units=f.time.units)
cmoraxes = [cmorTime, cmorLat, cmorLon]
print(f"      latitude ({len(lat)}), longitude ({len(lon)}), time ({len(time)})")

# ── Create CMOR variable ───────────────────────────────────────────────────────
print(f"\n[5/6] Writing CMORised output")
print(f"      Output variable : {outputVarName}  (units: {outputUnits})")
varid  = cmor.variable(outputVarName, outputUnits, cmoraxes, missing_value=1.e20)
values = np.array(d, np.float32)[:]

# Set bespoke long_name to include climatology period
cmor.set_variable_attribute(varid, 'long_name', 'c',
    'Near-surface land and ocean temperature monthly mean anomalies from the 1961-1990 climatological reference period')
cmor.set_variable_attribute(varid, 'units_metadata', 'c', 'temperature: difference')

# Provenance info - produces global attribute <processing_code_location>
git_commit_number = obs4MIPsLib.get_git_revision_hash()
path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
cmor.set_cur_dataset_attribute("processing_code_location", f"{full_git_path}")

# Compress and write - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid, 1, 1, 1)  # shuffle=1, deflate=1, deflate_level=1
cmor.write(varid, values, len(time))

# cmor.close() returns the path of the file it wrote - capture and display it
outfile = cmor.close(varid, file_name=True)
cmor.close()
f.close()

print(f"      Done. Output file written to:")
print(f"      {os.path.abspath(outfile)}")

# ── Cleanup ────────────────────────────────────────────────────────────────────
print(f"\n[6/6] Cleaning up temporary download directory")
_tmpdir.cleanup()
print(f"      Complete.\n")

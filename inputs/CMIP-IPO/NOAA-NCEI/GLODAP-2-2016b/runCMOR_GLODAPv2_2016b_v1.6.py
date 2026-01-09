# Based on Peter Glecklers zonal_mean demo file 
# Test to see if this zonal mean demo can work with temperature (thetao) data for oceans in GLODAPv2.2016b dataset
# Version 1 25-12-04 PSmith updated .json file and local copy of Omon.json table for 'thetao' with dimensions longitude latitude depth0m
# Version 1.1 25-12-08 PSmith used a program to change variables(dimensions) in the original datafile from 'depth_surface' to 'depth' and
# saved as a new file 'GLODAPv2.2016c.temperature.nc' 
# Version 1.2 25-12-08 PSmith added depth bounds to fix callback error at line 45 and added 1d time value 
# Version 1.3 25-12-08 PSmith removed reference to time in the axes as it's supposed to be climatological data.
# Version 1.4 25-12-08 PSmith changed 'depth' in CMOR axes to 'olevel' and added header information to my local Omon.json table
# Version 1.5 25-12-17 PSmith added verification scripts to check issues with Omon.json, and bounds and units etc. 
# Version 1.6 25-12-17 PSmith added more verificaitons and enter depth values manually for 700m or 2000m NetCDF dataset.

# Version 1.6 worked successfully after commenting out the 'ProvenanceInfo' section - this is creating errors. 
# NOTE: Need to change local version of Omon for dimensions to read olevel latitude longitude 

import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

sys.path.append('/Users/paul.smith/obs4MIPs-cmor-tables/src/') # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable = '/Users/paul.smith/obs4MIPs-cmor-tables/Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs

# Verify the table file before loading
import os
if os.path.exists(cmorTable):
    print(f"✓ Table file exists: {cmorTable}")
    print(f"  File size: {os.path.getsize(cmorTable)} bytes")
    print(f"  Last modified: {os.path.getmtime(cmorTable)}")
    
    # Quick check of the olevel axis definition
    import json
    with open(cmorTable, 'r') as f:
        table_data = json.load(f)
    if 'axis_entry' in table_data and 'olevel' in table_data['axis_entry']:
        olevel_units = table_data['axis_entry']['olevel'].get('units', 'NOT_FOUND')
        print(f"  olevel units in table: '{olevel_units}'")
        if olevel_units != 'm':
            print(f"  ✗ ERROR: olevel units should be 'm', not '{olevel_units}'")
            sys.exit(1)
    else:
        print("  ✗ ERROR: olevel axis not found in table!")
        sys.exit(1)
else:
    print(f"✗ ERROR: Table file not found: {cmorTable}")
    sys.exit(1)

inputJson = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/NOAA-NCEI/GLODAP-2-2016b/GLODAPv2.2016b.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/NOAA-NCEI/GLODAP-2-2016b/GLODAPv2.2016c.salinity.nc'
inputVarName = 'salinity' # try 'salinity' see metadata in the NetCDF header file
outputVarName = 'so'
outputUnits = '0.001'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values 

# IMPORTANT: Use actual depth values in meters, not indices
# The file may have depth as indices, but we need actual depth values
# These are the 33 standard depth levels from GLODAPv2.2016b
lev = np.array([0., 10., 20., 30., 50., 75., 100., 125., 150., 200., 250., 300.,
                400., 500., 600., 700., 800., 900., 1000., 1100., 1200., 1300., 
                1400., 1500., 1750., 2000., 2500., 3000., 3500., 4000., 4500., 
                5000., 5500.])

print(f"\nUsing explicit depth values in meters:")
print(f"  Number of levels: {len(lev)}")
print(f"  Range: {lev.min():.1f} to {lev.max():.1f} meters")
print(f"  First 5 values: {lev[:5]}")
print(f"  Last 3 values: {lev[-3:]}")

# Verify this matches the depth dimension size in the data
if len(lev) != d.shape[0]:
    raise ValueError(f"Depth size mismatch: lev has {len(lev)} but data has {d.shape[0]} depth levels") 
# No time dimension in the temperature variable - it's climatological data
f = f.bounds.add_missing_bounds(axes=['X', 'Y'])

d = np.where(np.isnan(d),1.e20,d) 

# Create depth bounds for the 33 depth levels
# Bounds are calculated as midpoints between adjacent depth levels
# For proper monotonic bounds, each level's upper bound becomes the next level's lower bound
lev_bnds = np.zeros((len(lev), 2))

for i in range(len(lev)):
    if i == 0:
        # Surface layer: For depth=0m, bounds go from 0 to midpoint with next level
        lev_bnds[i, 0] = 0.0
        if len(lev) > 1:
            lev_bnds[i, 1] = (lev[i] + lev[i+1]) / 2.0
        else:
            # Only one level - use depth value as upper bound
            lev_bnds[i, 1] = lev[i] if lev[i] > 0 else 1.0
    elif i == len(lev) - 1:
        # Bottom layer: from previous upper bound to extrapolated depth
        lev_bnds[i, 0] = lev_bnds[i-1, 1]
        lev_bnds[i, 1] = lev[i] + (lev[i] - lev[i-1]) / 2.0
    else:
        # Middle layers: from previous upper bound to midpoint with next level
        lev_bnds[i, 0] = lev_bnds[i-1, 1]
        lev_bnds[i, 1] = (lev[i] + lev[i+1]) / 2.0

# Verify bounds are monotonic
for i in range(len(lev)):
    if lev_bnds[i, 0] >= lev_bnds[i, 1]:
        print(f"ERROR: Non-monotonic bounds at level {i}: [{lev_bnds[i, 0]}, {lev_bnds[i, 1]}]")
        raise ValueError(f"Depth bounds must be monotonic increasing")

# Optional: Print depth bounds for verification
print("Depth levels and bounds:")
print(f"lev_bnds shape: {lev_bnds.shape}")
print(f"lev_bnds dtype: {lev_bnds.dtype}")
for i in range(min(5, len(lev))):  # Print first 5 for verification
    print(f"Level {i}: depth={lev[i]:7.1f}m, bounds=[{lev_bnds[i,0]:7.1f}, {lev_bnds[i,1]:7.1f}]")
print("...")
for i in range(max(0, len(lev)-2), len(lev)):  # Print last 2
    print(f"Level {i}: depth={lev[i]:7.1f}m, bounds=[{lev_bnds[i,0]:7.1f}, {lev_bnds[i,1]:7.1f}]")

# Check for any issues with the bounds
print(f"\nBounds validation:")
print(f"  Min lower bound: {lev_bnds[:,0].min()}")
print(f"  Max upper bound: {lev_bnds[:,1].max()}")
print(f"  Bounds are C-contiguous: {lev_bnds.flags['C_CONTIGUOUS']}")
print(f"  Bounds data type: {lev_bnds.dtype}")

# Ensure bounds are C-contiguous and correct type for CMOR
if not lev_bnds.flags['C_CONTIGUOUS']:
    print("  WARNING: Making bounds C-contiguous for CMOR...")
    lev_bnds = np.ascontiguousarray(lev_bnds)

# Ensure float64 for CMOR
lev_bnds = lev_bnds.astype(np.float64)

print(f"\nFinal bounds array for CMOR:")
print(f"  Shape: {lev_bnds.shape}")
print(f"  Dtype: {lev_bnds.dtype}")
print(f"  First level bounds: [{lev_bnds[0,0]}, {lev_bnds[0,1]}]")
print(f"  C-contiguous: {lev_bnds.flags['C_CONTIGUOUS']}")
print("="*60 + "\n")
print(f"  All bounds positive: {np.all(lev_bnds >= 0)}")
print(f"  All upper > lower: {np.all(lev_bnds[:,1] > lev_bnds[:,0])}")

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# Create CMOR axes - NOW WITH DEPTH BOUNDS
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorLev = cmor.axis("olevel", coord_vals=lev[:], cell_bounds=lev_bnds, units="m")
# No time axis - this is climatological data with dimensions (olevel, lat, lon)
cmoraxes = [cmorLev, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
values  = np.array(d,np.float32)[:]

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# I've edited this out as I keep getting an error about ProvenanceInfo not defined...
# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
# gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
# full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"  
# cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values) 
cmor.close()
f.close()

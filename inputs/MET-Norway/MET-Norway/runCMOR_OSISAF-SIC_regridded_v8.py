# CMORize regridded OSISAF sea-ice files for obs4MIPs
# This version works with data regridded to regular lat/lon grid
# Based on Thomas Lavergne's original script, modified by Paul Smith with assitance from ClaudeAI 10-10-2025
# Amended to resolve missing units attribute 10-10-2025 v3
# Amended to resolve issues with longitude 10-10-2025 v4
# Amended to update the CMOR script to handle -180 to 180 longitude 10-10-2025 v5
# Amended to use np.clip() to ensure bounds never exceed valid ranges and 
# simplified bounds calculation using consistent grid spacing 10-10-2025 v6 
# Amended again due to traceback errors 
# Transpose the data from (time, typesi, lat, lon) to (lon, lat, time, typesi) to match the CMOR axes order
# and remove time_vals and time_bnds from the cmor.write() call since time is already defined
# 10-10-2025 v7
# Amended again due to a warning while writing the cmor output 10-10-2025 V8
# First try writing all the data at once....
# If that doesn't work, it will write time step by time step, it provides output so we can see what's happening

import os, sys
import cmor
import xarray as xr
import numpy as np
try:
    import simplejson as json
except ImportError:
    import json
from glob import glob
from datetime import datetime, timezone, timedelta
from calendar import monthrange

sys.path.append('/Users/paul.smith/obs4MIPs-cmor-tables/src/')
import obs4MIPsLib

# ============================================================================
# Configuration
# ============================================================================
cmorTable = '/Users/paul.smith/obs4MIPs-cmor-tables/Tables/obs4MIPs_SImon.json'
inputJson = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/MET-Norway/MET-Norway/OSISAF-SIC-V3.json'
inputFileDir = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/MET-Norway/MET-Norway/OSI-450-nh-regridded' # change for sh or nh
inputFileName = 'OBS_OSI-450-nh_reanaly_v3_OImon_sic_197901-197912_regridded.nc' # change for sh or nh
inputVarName = 'sic'
outputVarName = 'siconc'
outputUnits = '%'

# ============================================================================
# Load regridded data
# ============================================================================
print("="*70)
print("CMORizing regridded OSISAF sea ice data")
print("="*70)

f = xr.open_mfdataset(sorted(glob(os.path.join(inputFileDir, inputFileName))), 
                      decode_times=False, combine='nested', concat_dim='time')
d = f[inputVarName]

# Get 1D lat/lon coordinates from regridded file
lat = f.lat.values
lon = f.lon.values
time = f.time.values

# Get time units - handle case where it might not be in attributes
if hasattr(f.time, 'units'):
    time_units = f.time.units
elif 'units' in f.time.attrs:
    time_units = f.time.attrs['units']
else:
    # Default if not found - adjust based on your data
    time_units = 'seconds since 1978-01-01 00:00:00'
    print(f"WARNING: Time units not found, using default: {time_units}")

print(f"Time units: {time_units}")
print(f"Number of time steps: {len(time)}")
print(f"Latitude: {len(lat)} points, range [{lat.min():.2f}, {lat.max():.2f}]")
print(f"Longitude: {len(lon)} points, range [{lon.min():.2f}, {lon.max():.2f}]")
print(f"Data shape: {d.shape}")

# ============================================================================
# Create contiguous time bounds for all months
# ============================================================================

def get_month_start(year, month):
    """Get start of month as timestamp"""
    return datetime(year, month, 1, 0, 0, 0)

def get_month_end(year, month):
    """Get end of month (= start of next month) as timestamp"""
    if month == 12:
        return datetime(year + 1, 1, 1, 0, 0, 0)
    else:
        return datetime(year, month + 1, 1, 0, 0, 0)

print("\nProcessing time coordinates...")
new_time = []
new_tbds = []
missing_months = []

for n, t in enumerate(time):
    dt = datetime.fromtimestamp(t)
    
    # Check for missing months
    if n > 0:
        prev_dt = datetime.fromtimestamp(time[n-1])
        months_diff = (dt.year - prev_dt.year) * 12 + (dt.month - prev_dt.month)
        
        if months_diff > 1:
            # Fill in missing months
            for i in range(1, months_diff):
                miss_year = prev_dt.year
                miss_month = prev_dt.month + i
                if miss_month > 12:
                    miss_year += miss_month // 12
                    miss_month = miss_month % 12
                    if miss_month == 0:
                        miss_month = 12
                        miss_year -= 1
                
                # Create mid-month timestamp for missing month
                days_in_month = monthrange(miss_year, miss_month)[1]
                miss_mid = datetime(miss_year, miss_month, days_in_month // 2 + 1, 12, 0, 0)
                
                # Create contiguous bounds
                miss_start = get_month_start(miss_year, miss_month)
                miss_end = get_month_end(miss_year, miss_month)
                
                new_time.append(datetime.timestamp(miss_mid))
                new_tbds.append([datetime.timestamp(miss_start), datetime.timestamp(miss_end)])
                missing_months.append(f"{miss_year}-{miss_month:02d}")
                print(f"  Inserted missing month: {miss_year}-{miss_month:02d}")
    
    # Add current month with contiguous bounds
    month_start = get_month_start(dt.year, dt.month)
    month_end = get_month_end(dt.year, dt.month)
    
    new_time.append(t)
    new_tbds.append([datetime.timestamp(month_start), datetime.timestamp(month_end)])

# If we added missing months, reindex the data array
if len(missing_months) > 0:
    print(f"\nTotal missing months inserted: {len(missing_months)}")
    missing_times = [new_time[i] for i, val in enumerate(new_time) if i >= len(time)]
    missing_da = xr.DataArray(missing_times, dims=['time'], coords=[missing_times])
    full_time = xr.concat([f.time, missing_da], dim='time')
    full = f.reindex(time=full_time, fill_value=1.e20).sortby('time')
    d = full[inputVarName]

# Convert to numpy arrays
new_time = np.array(new_time)
new_tbds = np.array(new_tbds)

# Verify contiguity
print("\nVerifying time bounds contiguity...")
gaps_found = False
for i in range(len(new_tbds) - 1):
    if abs(new_tbds[i][1] - new_tbds[i+1][0]) > 1:
        print(f"  WARNING: Gap at index {i}: {new_tbds[i+1][0] - new_tbds[i][1]} seconds")
        gaps_found = True

if not gaps_found:
    print("  ✓ All time bounds are contiguous!")

# ============================================================================
# Initialize CMOR
# ============================================================================
print("\n" + "="*70)
print("Initializing CMOR...")
print("="*70)

cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history', f.history)

# ============================================================================
# Create CMOR axes
# ============================================================================

# Create time axis
time_axis = cmor.axis('time', coord_vals=new_time, cell_bounds=new_tbds, units=time_units)

# Create typesi dimension (ice type - set to 1 for total concentration)
typesi_axis = cmor.axis('typesi', units='1', coord_vals=np.array([1]), 
                        cell_bounds=np.array([[0.5, 1.5]]))

# Create latitude axis with bounds
# Ensure bounds don't exceed [-90, 90]
lat_bnds = np.zeros((len(lat), 2))
dlat = lat[1] - lat[0] if len(lat) > 1 else 0.5

lat_bnds[:, 0] = lat - dlat/2
lat_bnds[:, 1] = lat + dlat/2

# Clamp latitude bounds to valid range
lat_bnds = np.clip(lat_bnds, -90.0, 90.0)

# Create longitude axis with bounds
lon_bnds = np.zeros((len(lon), 2))
dlon = lon[1] - lon[0] if len(lon) > 1 else 0.5

lon_bnds[:, 0] = lon - dlon/2
lon_bnds[:, 1] = lon + dlon/2

# Clamp longitude bounds to valid range [-180, 180]
lon_bnds = np.clip(lon_bnds, -180.0, 180.0)

print(f"Latitude: {len(lat)} points, range [{lat[0]:.2f}, {lat[-1]:.2f}]")
print(f"Latitude bounds - first: [{lat_bnds[0, 0]:.2f}, {lat_bnds[0, 1]:.2f}], last: [{lat_bnds[-1, 0]:.2f}, {lat_bnds[-1, 1]:.2f}]")
print(f"Longitude: {len(lon)} points, range [{lon[0]:.2f}, {lon[-1]:.2f}]")
print(f"Longitude bounds - first: [{lon_bnds[0, 0]:.2f}, {lon_bnds[0, 1]:.2f}], last: [{lon_bnds[-1, 0]:.2f}, {lon_bnds[-1, 1]:.2f}]")

lat_axis = cmor.axis('latitude', coord_vals=lat, cell_bounds=lat_bnds, units='degrees_north')
lon_axis = cmor.axis('longitude', coord_vals=lon, cell_bounds=lon_bnds, units='degrees_east')

# Define axes in the order expected by the table: longitude, latitude, time, typesi
cmoraxes = [lon_axis, lat_axis, time_axis, typesi_axis]

print(f"✓ CMOR axes created: [longitude({len(lon)}), latitude({len(lat)}), time({len(new_time)}), typesi(1)]")

# ============================================================================
# Create CMOR variable and prepare data
# ============================================================================

varid = cmor.variable(outputVarName, outputUnits, cmoraxes, missing_value=1.e20)

# Prepare data array - need to add typesi dimension and reorder axes
values = np.array(d, np.float32)[:]

# Data is currently (time, lat, lon)
# Need to: 1) add typesi dimension, 2) reorder to match cmoraxes
# cmoraxes order is: [lon, lat, time, typesi]
# So we need: (lon, lat, time, typesi)

if values.ndim == 3:
    # Current shape: (time, lat, lon)
    # Add typesi: (time, typesi, lat, lon)
    values = values[:, np.newaxis, :, :]
    
    # Reorder to (lon, lat, time, typesi)
    # From (time, typesi, lat, lon) -> (lon, lat, time, typesi)
    values = np.transpose(values, (3, 2, 0, 1))
    
    print(f"Data shape after reordering: {values.shape}")
    print(f"Expected: (lon={len(lon)}, lat={len(lat)}, time={len(new_time)}, typesi=1)")

# Set variable attributes
cmor.set_variable_attribute(varid, 'valid_min', 'f', 0.0)
cmor.set_variable_attribute(varid, 'valid_max', 'f', 100.0)

# ============================================================================
# Write data
# ============================================================================
print("\nWriting data to CMOR...")
print(f"Writing {len(new_time)} time steps...")

cmor.set_deflate(varid, 1, 1, 1)  # Enable compression

# For data with time dimension, we need to write it properly
# CMOR expects data in shape (spatial_dims..., time_steps) for some cases
# Let's verify the shape matches what CMOR expects
print(f"Final data shape: {values.shape}")
print(f"CMOR axes order: [lon({len(lon)}), lat({len(lat)}), time({len(new_time)}), typesi(1)]")

# Write the data - CMOR will use the time axis we already defined
# For 4D data with time, we may need to write time step by time step
# Let's try writing all at once first
try:
    cmor.write(varid, values)
    print("✓ Data written successfully")
except Exception as e:
    print(f"Error writing all at once: {e}")
    print("Trying to write time step by time step...")
    
    # Alternative: write time step by time step
    for t_idx in range(len(new_time)):
        # Extract data for this time step: (lon, lat, typesi)
        data_slice = values[:, :, t_idx, :]
        cmor.write(varid, data_slice, ntimes_passed=t_idx)
    print(f"✓ Wrote {len(new_time)} time steps individually")

# ============================================================================
# Finalize
# ============================================================================
cmor.close()
f.close()

print("\n" + "="*70)
print("✓ CMOR processing completed successfully!")
print("="*70)
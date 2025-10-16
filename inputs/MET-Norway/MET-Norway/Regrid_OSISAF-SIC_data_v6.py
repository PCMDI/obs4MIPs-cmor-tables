# Regrid OSISAF-SIC-V3 sea ice data from native EASE2 25km polar stereographic grid
# to a regular 0.5° x 0.5° latitude/longitude grid for obs4MIPs processing.
# NOTE: THIS IS THE SAME AS V5 SCRIPT EXCEPT FOR SOUTHERN HEMISPHERE

# This script uses xESMF for regridding with bilinear interpolation.
# Install with: pip install xesmf or conda install -c conda-forge xesmf PS installed locally using pip 
# Paul Smith developed this script with Claude-AI help 10-10-2025 Version 2
# Fixed to preserve time units after traceback error 10-10-2025 Version 3
# Amended again for the longitude create a grid with longitude from -180° to 179.5° (avoiding the duplicate point at 180° = -180°)
# 10-10-2025 v4
# Amended again to Latitude: 0.25° to 89.75° (bounds will be 0° to 90°) 
# Longitude: -179.75° to 179.75° (bounds will be -180° to 180°)
# 10-10-2025 v5 
# Amednded information to regridd the SH datasets prepared by Axel Lauer at DLR with ESMValTool

import xarray as xr
import numpy as np
import xesmf as xe
from glob import glob
import os

# ============================================================================
# Configuration
# ============================================================================
input_dir = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/MET-Norway/MET-Norway/OSI-450-sh' # Changedto sh 
input_pattern = 'OBS_OSI-450-sh_reanaly_v3_OImon_sic_*.nc' # changed to sh
output_dir = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/MET-Norway/MET-Norway/OSI-450-sh-regridded' # changed to sh 
variable_name = 'sic'

# Target grid: 0.5° resolution
# For Northern Hemisphere, use -180° to 180° longitude (excluding endpoint)
# Latitude from 0.25° to 89.75° to keep bounds within valid range [-90, 90]
target_lat_min = -89.75   # Start at -89.75 so first bound is at 90 - changed for sh
target_lat_max = -0.25  # End at -0.25 so last bound is at 0 - changed for sh
target_lon_min = -179.75  # Start at -179.75
target_lon_max = 179.75   # End at 179.75
target_resolution = 0.5   # degrees

# ============================================================================
# Setup
# ============================================================================

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

print("="*70)
print("OSISAF Sea Ice Concentration Regridding")
print("="*70)
print(f"Input directory: {input_dir}")
print(f"Output directory: {output_dir}")
print(f"Target resolution: {target_resolution}° x {target_resolution}°")
print(f"Target domain: lat [{target_lat_min}, {target_lat_max}], lon [{target_lon_min}, {target_lon_max}]")
print("="*70)

# ============================================================================
# Find input files
# ============================================================================
input_files = sorted(glob(os.path.join(input_dir, input_pattern)))
if len(input_files) == 0:
    raise FileNotFoundError(f"No files found matching pattern: {input_pattern}")

print(f"\nFound {len(input_files)} input file(s):")
for f in input_files:
    print(f"  - {os.path.basename(f)}")

# ============================================================================
# Define target grid
# ============================================================================
n_lat = int((target_lat_max - target_lat_min) / target_resolution) + 1
# For longitude, don't include the endpoint at 180.0 to avoid duplication with -180.0
n_lon = int((target_lon_max - target_lon_min) / target_resolution)

target_lat = np.linspace(target_lat_min, target_lat_max, n_lat)
# Longitude from -180 to 179.5 (not including 180, which equals -180)
target_lon = np.linspace(target_lon_min, target_lon_max - target_resolution, n_lon)

# Create target grid dataset
ds_out = xr.Dataset({
    'lat': (['lat'], target_lat, {'units': 'degrees_north'}),
    'lon': (['lon'], target_lon, {'units': 'degrees_east'})
})

print(f"\nTarget grid: {n_lon} x {n_lat} points (lon x lat)")

# ============================================================================
# Process each file
# ============================================================================
for input_file in input_files:
    print(f"\nProcessing: {os.path.basename(input_file)}")
    
    # Load input file
    ds_in = xr.open_dataset(input_file, decode_times=False)
    
    # Check if we have the necessary coordinates
    if 'lat' not in ds_in.variables or 'lon' not in ds_in.variables:
        print("  ERROR: File missing 'lat' or 'lon' variables")
        continue
    
    # Prepare source dataset for regridding
    # xESMF needs the lat/lon to be in the dataset as coordinates
    if ds_in['lat'].ndim == 2:
        # 2D lat/lon - need to add them as coordinates
        # Create a dataset with lat/lon properly set
        ds_in = ds_in.rename({'y': 'y_index', 'x': 'x_index'})
        # xESMF can handle 2D lat/lon if they're set up correctly
    
    print(f"  Input shape: {ds_in[variable_name].shape}")
    print(f"  Input lat range: [{ds_in['lat'].values.min():.2f}, {ds_in['lat'].values.max():.2f}]")
    print(f"  Input lon range: [{ds_in['lon'].values.min():.2f}, {ds_in['lon'].values.max():.2f}]")
    
    # Create regridder (this is computed once and can be reused)
    print("  Creating regridder...")
    regridder = xe.Regridder(ds_in, ds_out, 'bilinear', periodic=False)
    
    # Apply regridding to the sea ice concentration variable
    print("  Regridding data...")
    sic_regridded = regridder(ds_in[variable_name])
    
    # Mask out any values outside valid range (can happen at edges)
    sic_regridded = sic_regridded.where((sic_regridded >= 0) & (sic_regridded <= 100))
    
    # Create output dataset with regridded data
    ds_regrid = xr.Dataset({
        variable_name: sic_regridded
    })
    
    # Copy time coordinate and bounds if present
    if 'time' in ds_in.coords:
        ds_regrid['time'] = ds_in['time']
        # Preserve time attributes
        if hasattr(ds_in['time'], 'attrs'):
            ds_regrid['time'].attrs = ds_in['time'].attrs
    if 'time_bnds' in ds_in.variables:
        ds_regrid['time_bnds'] = ds_in['time_bnds']
    
    # Copy attributes
    ds_regrid[variable_name].attrs = ds_in[variable_name].attrs
    ds_regrid.attrs = ds_in.attrs
    ds_regrid.attrs['regridding_method'] = 'bilinear interpolation using xESMF'
    ds_regrid.attrs['target_grid'] = f'{target_resolution} degree lat/lon'
    ds_regrid.attrs['original_grid'] = 'EASE2 25km polar stereographic'
    
    # Set coordinate attributes
    ds_regrid['lat'].attrs = {'units': 'degrees_north', 'long_name': 'latitude', 'standard_name': 'latitude'}
    ds_regrid['lon'].attrs = {'units': 'degrees_east', 'long_name': 'longitude', 'standard_name': 'longitude'}
    
    # Generate output filename
    output_filename = os.path.basename(input_file).replace('.nc', '_regridded.nc')
    output_path = os.path.join(output_dir, output_filename)
    
    # Save regridded data
    print(f"  Saving to: {output_filename}")
    encoding = {
        variable_name: {'zlib': True, 'complevel': 4, 'dtype': 'float32', '_FillValue': 1e20},
        'time': {'dtype': 'float64'},
        'lat': {'dtype': 'float64'},
        'lon': {'dtype': 'float64'}
    }
    ds_regrid.to_netcdf(output_path, encoding=encoding)
    
    # Clean up
    try:
        regridder.clean_weight_file()  # Older xESMF versions
    except AttributeError:
        pass  # Newer xESMF versions handle cleanup automatically
    
    ds_in.close()
    ds_regrid.close()
    
    print(f"  ✓ Complete! Output shape: {sic_regridded.shape}")

print("\n" + "="*70)
print("Regridding complete!")
print(f"Regridded files saved to: {output_dir}")
print("="*70)
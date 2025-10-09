# CMORising script for the CALIPSO ICECLOUD1.0 monthly means dataset prepared with ESMValTool for the REF
# This script developed from the original obs4MIPs demo .py files and additional assistance from Claude AI (Anthropic)
# Paul Smith 08-10-2025
# This script is for the 'cli' variable 
# Importing necessary libraries

import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import sys, os
import json

sys.path.append('/Users/XXXX/obs4MIPs-cmor-tables/src/') # change to your Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

# User provided input (CMOR table, input file, variable_id and input_json file)
cmorTable = '/Users/XXXX/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputVarName = 'cli' # this is a string not a list
inputJson = '/Users/XXXX/obs4MIPs-cmor-tables/inputs/PCMDI/NASA-LaRC/CALIPSO1.0-input.json'
inputFilePath = '/Users/XXXX/obs4MIPs-cmor-tables/inputs/PCMDI/XXXX.nc' # input file path 
outputVarName = 'cli' # keep as 'cli' but make sure varid has outputVarName not inputVarName
outputUnits = 'kg kg-1' 

# Open input dataset, read in variable & units
f = xr.open_dataset(inputFilePath, decode_times=False, decode_cf=False)
d = f['cli'].values # this might need to be changed back to d = f[inputVarName] or d = f[outputVarName] 

# Initialize and run CMOR but using this format where cmorPlev is defined
# Load both tables
cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4)
cmor.dataset_json(inputJson)
cmor.load_table('/Users/paul.smith/obs4MIPs-cmor-tables/Tables/obs4MIPs_coordinate.json')  # Load coordinate table first
cmor.load_table(cmorTable)  # Then load obs4mips_Amon.json table

# Define coordinates for CMOR
cmorLat = cmor.axis("latitude", coord_vals=f.lat[:].values, cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=f.lon[:].values, cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=f.time.values, cell_bounds=f.time_bnds.values, units=f.time.units)

# Use plev27 which is defined in the coordinate table with exactly 27 levels same as the CALIPSO netCDF data file
cmorPlev = cmor.axis("plev27", coord_vals=f.plev[:].values, units="Pa")

axes = [cmorLon, cmorLat, cmorPlev, cmorTime]
print(axes)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
# varid  = cmor.variable(inputVarName, outputUnits, axes, missing_value=1.e20)
# values = np.array(d[:],np.float32)
varid = cmor.variable(outputVarName, outputUnits, axes, missing_value=1.e20)
values = np.array(d[:], np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid, 1, 1, 1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid, values)  # This should write all time steps
f.close()
cmor.close()
print('done with', outputVarName)
print("Data shape:", values.shape) # check this value against the expected 
print("Expected: (108, 27, 85, 144)") 
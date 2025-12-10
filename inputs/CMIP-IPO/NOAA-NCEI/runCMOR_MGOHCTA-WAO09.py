# Based on Peter Glecklers 2Dmean.py demo file 
# Test to see if this zonal mean demo can work with mean ocean heat content data for oceans in MGOHCTA-WOA09 dataset
# Version 1 25-10-04 PSmith
# Version 2.0 25-12-03 updated .json file and local copy of Omon.json table to have dimensions longitude, latitude, time depth
# Used to process the heat_content data from 0-700 m netCDF file. 

import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

sys.path.append('/Users/paul.smith/obs4MIPs-cmor-tables/src/') # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable = '/Users/paul.smith/obs4MIPs-cmor-tables/Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/NOAA-NCEI/MGOHCTA-WOA09/MGOHCTA-WOA09.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/Users/paul.smith/obs4MIPs-cmor-tables/inputs/NOAA-NCEI/MGOHCTA-WOA09/heat_content_anomaly_0-2000_monthly.nc'
inputVarName = 'h18_hc' # try month_h22_WO, h18_hc etc. see metadat in the NetCDF file
outputVarName = 'ohcanom'
outputUnits = 'J'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values 
time = f.time.values  
f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime, cmorLat, cmorLon]

## COMEMENTED OUT WAS GENERATING ERRORS - not sure what the issue was? 
# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
# gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
# full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"  
# cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values)  #,len(time)) 
cmor.close()
f.close()
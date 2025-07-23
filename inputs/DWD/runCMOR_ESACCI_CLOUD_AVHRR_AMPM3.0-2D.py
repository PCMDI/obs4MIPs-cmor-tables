# This script shows how the ESA CCI Cloud dataset, pre-prepared by ESMValTool, was CMOR-ized for obs4MIPs publication.

# Please note, ESMValTool has combined the CCI Cloud AVHRR AM and PM products and created a CMOR-like dataset here, which we use to 
# fully CMOR-ize the dataset: https://github.com/ESMValGroup/ESMValTool/blob/main/esmvaltool/cmorizers/data/formatters/datasets/esacci_cloud.ncl

# Importing necessary libraries
import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

# Userprovided input (CMOR table, input file, variable_id and input_json file)
cmorTable = '/root/Obs4MIPs_demo/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputVarName = 'clt'
inputJson = '/root/Obs4MIPs_demo/obs4MIPs-cmor-tables/inputs/ESMValTool/ESACCI-CLD_input.json'
inputFilePathbgn = '/root/Obs4MIPs_demo/data/OBS_ESACCI-CLOUD_sat_AVHRR-AMPM-fv3.0_Amon_clt_198201-201612.nc'

# Open input dataset, read in variable & units
f = xr.open_dataset(inputFilePathbgn,decode_times=False, decode_cf=False)
d = f[inputVarName].values
vunits = f[inputVarName].units

# Initialize and run CMOR
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4 ,logfile='cmorLog.' + inputVarName + '.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# Define coordinates for CMOR
cmorLat = cmor.axis("latitude", coord_vals=f.lat[:].values, cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=f.lon[:].values, cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=f.time.values, cell_bounds=f.time_bnds.values, units= f.time.units)
axes = [cmorTime, cmorLat, cmorLon]
print(axes)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(inputVarName,vunits,axes,missing_value=1.e20)
values  = np.array(d[:],np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values) ; # Write variable with time axis
f.close()
cmor.close()
print('done with',inputVarName) 

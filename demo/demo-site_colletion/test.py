import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

cmorTable = '../../Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'test.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'hfbasin_Omon_UKESM1-0-LL_ssp370_r5i1p1f2_gnz_201501-204912.nc'
inputVarName = 'hfbasin'
outputVarName = 'hfbasin'
outputUnits = 'W'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
time = f.time.values  
f = f.bounds.add_missing_bounds(axes=['Y'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

sector = f.sector.values

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorBasin = cmor.axis("basin", coord_vals=sector[:],units="")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorLat, cmorBasin]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
values  = np.array(d,np.float32)[:]

cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,d,len(time)) 
cmor.close()
f.close()

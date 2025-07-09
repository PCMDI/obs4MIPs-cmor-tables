import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

cmorTable = '../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'test.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'hfls.nc'
inputVarName = 'hfls'
outputVarName = 'hfls-site-collection'
outputUnits = 'W m-2'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values
time = f.time.values  
#f = f.bounds.add_missing_bounds(axes=['lat','lon'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

#print('done')
#w = sys.stdin.readline()

sites = f.site.values

#sector = np.array(['atlantic_arctic_ocean', 'global_ocean', 'indian_pacific_ocean'])

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# First, load the grids table to set up x and y axes and the lat-long grid
grid_table_id = cmor.load_table('../../Tables/obs4MIPs_grids.json')
cmor.set_table(grid_table_id)

y_axis_id = cmor.axis(table_entry='y_deg', units='degrees', coord_vals=lat)
x_axis_id = cmor.axis(table_entry='x_deg', units='degrees', coord_vals=lon)

grid_id = cmor.grid(axis_ids=[y_axis_id, x_axis_id], latitude=lat, longitude=lon)


# Create CMOR axes
#cmorLat = cmor.axis("latitude1", coord_vals=lat[:], units="degrees_north")
#cmorLon = cmor.axis("longitude1", coord_vals=lat[:], units="degrees_east")
cmorBasin = cmor.axis("sites", coord_vals=sites,units="")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorBasin, cmorLat,cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,[grid_id,cmorTime],missing_value=1.e20)

#axis_ids=[grid_id, time_axis_id]

d = np.where(np.isnan(d), 1.0e20, d)
values  = np.array(d,np.float32)[:]

cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values)  #,len(time)) 
cmor.close()
f.close()

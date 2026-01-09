import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

sys.path.append("../inputs/misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable = '../Tables/obs4MIPs_Lmon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'OLC-ORS-V0.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'olc_ors.nc'
inputVarName = 'sm'
outputVarName = 'mrsos'
outputUnits = 'kg m-2'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values 
time = f.time.values  
f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
f = f.bounds.add_bounds("T")
# manually set the time bounds for months
##tbds = f.time_bnds.values
tbds = np.vstack([time, np.append(time[1:], time[-1]+31)]).T

# CONVERT UNITS FROM m3/m3 to kg/m2
depth_bnds = f.depth_bnds.values
thickness = depth_bnds[:,1] - depth_bnds[:,0]
if outputVarName == 'mrso':
    d = np.sum(d*thickness.reshape(1,-1,1,1)*1000., axis=1)
elif outputVarName == 'mrsos':
    d = d[:,0,:,:]*thickness[0]*1000.
d = np.where(np.isnan(d),1.e20,d).astype(np.float32)


# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history', "First created on 2021/07/25 by Wang & Mao") 

# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmorDepth = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
values  = np.array(d,np.float32)[:]

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"  
cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")
# 
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,d,len(time)) 
cmor.close()
f.close()

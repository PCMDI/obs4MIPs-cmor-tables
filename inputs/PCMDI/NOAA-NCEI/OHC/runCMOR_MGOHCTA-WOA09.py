import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

sys.path.append("../../inputs/misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

cmorTable = '../../Tables/obs4MIPs_Omon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'XXX.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'XXX'
inputVarName = 'ohcanom'
outputUnits = 'Joules'

# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.latitude.values
lev = f.altitude.values
time = f.time.values  
f = f.bounds.add_missing_bounds(axes=['Y'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

d = np.where(np.isnan(d),1.e20,d)

# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

# Create CMOR axes
cmorLat = cmor.axis("basin", coord_vals=lat[:], cell_bounds=f.latitude_bnds.values, units="XXX")
cmorLev = cmor.axis("olevel", coord_vals=lev[:]*1000., units="m")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorBasin,cmorOlevel]

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
cmor.write(varid,d)  #,len(time)) 
cmor.close()
f.close()

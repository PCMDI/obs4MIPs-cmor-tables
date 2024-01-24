import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

#sys.path.append("/home/gleckler1/git/obs4MIPs-cmor-tables/inputs/") # Path to obs4MIPsLib
sys.path.append("../inputs/misc") # Path to obs4MIPsLib

import obs4MIPsLib

#%% User provided input
cmorTable = '../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'CMAP-V1902.json' ; # Update contents of this file to set your global_attributes
inputFilePath = 'precip.mon.mean.nc'
inputVarName = 'precip'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

### USER MAY NOT NEED TO CHANGE ANYTHING BELOW THIS LINE...

# Open and read input netcdf file
f = xr.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values 
lon = f.lon.values 
time = f.time.values ; # Rather use a file dimension-based load statement
f = f.bounds.add_bounds("X")  
f = f.bounds.add_bounds("Y")  
f = f.bounds.add_bounds("T")
# CONVERT UNITS FROM mm/day to kg/m2/s 
d = np.divide(d,86400.)
d = np.where(np.isnan(d),1.e20,d)

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
cmor.set_cur_dataset_attribute('history',f.history) 

axes    = [ {'table_entry': 'time',
             'units': f.time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': f.lat_bnds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': f.lon_bnds},
          ]
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=1.e20)
values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Provenance info 
gitinfo = obs4MIPsLib.getGitInfo("./")
#commit_run,path_to_code = obs4MIPsLib.ProvenanceInfo(gitinfo)
#full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{commit_run}{path_to_code}"
commit_num = gitinfo[0].split(':')[1].strip()
paths = os.getcwd().split('/demo')
path_to_code = f"/demo{paths[1]}"
full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{commit_num}{path_to_code}"

cmor.set_cur_dataset_attribute("obs4MIPs_GH_Commit_ID",f"{full_git_path}")
 
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
f.close()
cmor.close()

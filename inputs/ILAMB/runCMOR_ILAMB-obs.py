import cmor
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import numpy as np
import cftime
import sys,os,glob
#cmor.set_logfile("cmor.log")

#%% User provided input 
cmorTable = '../../Tables/obs4MIPs_Lmon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx

#EXAMPLES with command line input
# python -i runCMOR_ILAMB-obs.py gpp WECANN_input.json /home/users/dhegedus/CMIPplacement/ILAMB-data/WECANN/in/gpp_mon_WECANN_BE_gn_200701-201512.nc

command_line  = True
if command_line == True:
 inputVarName = sys.argv[1] 
#outputVarName = sys.argv[2]
#outputUnits = sys.argv[3] 
 inputJson = sys.argv[2] 
 inputFilePathbgn = sys.argv[3]

###
f = xr.open_dataset(inputFilePathbgn,decode_times=False, decode_cf=False)
# f = f.bounds.add_missing_bounds(axes=['X', 'Y']) # ONLY IF BOUNDS NOT IN INPUT FILE
# f = f.bounds.add_bounds('T') # ONLY IF BOUNDS NOT IN INPUT FILE
d = f[inputVarName].values
vunits = f[inputVarName].units

### Initialize and run CMOR
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4 ,logfile='./cmorLog.' + inputVarName + '.txt', set_verbosity=cmor.CMOR_NORMAL)
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)

cmorLat = cmor.axis("latitude", coord_vals=f.lat[:].values, cell_bounds=f.lat_bounds.values, units="degrees_north")
cmorLon = cmor.axis("longitude", coord_vals=f.lon[:].values, cell_bounds=f.lon_bounds.values, units="degrees_east")
cmorTime = cmor.axis("time", coord_vals=f.time.values, cell_bounds=f.time_bounds.values, units= f.time.units)
axes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(inputVarName,vunits,axes,missing_value=1.e20)
values  = np.array(d[:],np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values) ; # Write variable with time axis
f.close()
cmor.close()
print('done with ',inputVarName)

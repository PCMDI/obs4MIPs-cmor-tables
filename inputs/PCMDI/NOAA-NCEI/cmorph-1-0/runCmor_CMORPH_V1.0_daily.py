import cmor
import xcdat as xc 
import xarray as xr
import numpy as np
import sys, os, glob

sys.path.append("../../../misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

targetgrid = 'orig'

cmorTable = '../../../../Tables/obs4MIPs_Aday.json' 
inputJson = 'CMORPH_V1.0_daily-input.json'  

inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/NOAA-NCEI/CMORPH-1-0/www.ncei.noaa.gov/data/cmorph-high-resolution-global-precipitation-estimates/access/daily/0.25deg/'

yrs = os.listdir(inputFilePath)
yrs.sort()
print(yrs)
#w = sys.stdin.readline()

inputVarName = 'cmorph'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

for yr in yrs:
  fi = inputFilePath + yr + '/*/*.nc'
  f = xc.open_mfdataset(fi,decode_times=False)
  d = f[inputVarName]
  d = np.divide(d,3600.)

  lat = f.lat.values  #f.getLatitude()
  lon = f.lon.values  #d.getLongitude()
  time = f.time.values   #d.get

  f = f.drop_vars(["lat_bounds","lon_bounds"])

  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")  
  f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
#####del(time_bounds) ; # Cleanup

# print('above cmor')
#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)

# Create CMOR axes
  cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=f.time_bounds.values, units= f.time.units)
  cmoraxes = [cmorTime,cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

  cmor.set_variable_attribute(varid,'valid_min','f',2.0)
  cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Add GitHub commit ID attribute to output CMOR file
  gitinfo = obs4MIPsLib.getGitInfo("./")
  commit_num = gitinfo[0].split(':')[1].strip()
  paths = os.getcwd().split('/inputs')
  path_to_code = f"/inputs{paths[1]}"
  full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{commit_num}{path_to_code}"
  cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,len(time)) ; # Write variable with time axis
  cmor.close()
  f.close()
  print('done cmorizing ', yr)

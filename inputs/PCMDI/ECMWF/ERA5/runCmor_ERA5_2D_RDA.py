import cmor
import xcdat as xc
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import numpy as np
import cftime
import sys,os,glob

sys.path.append("../../../misc/") # Path to obs4MIPsLib
import obs4MIPsLib
import fix_dataset_time

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/ECMWF/'
inputFilePathend = 'ERA5/RDA/'

inputVarName = ['VAR_2T', 'MSL','VAR_10SI','VAR_10U','VAR_10V']
outputVarName = ['tas','psl','sfcWind','uas','vas']  #['psl']  
outputUnits = ['K','Pa','m s-1','m s-1','m s-1'] 


### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE..
for vn,fi in enumerate(inputVarName):
 print(fi, outputVarName[vn])
#w = sys.stdin.readline()
 inputFilePath = inputFilePathbgn+inputFilePathend + outputVarName[vn] + '/'
 files_yearly = glob.glob(inputFilePath + '*.nc')
 files_yearly.sort()

 for fi in files_yearly:
  f = xc.open_dataset(fi,decode_times=True, decode_cf=True)
  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')
  d = f[inputVarName[vn]].values
  lat = f.latitude
  lon = f.longitude
  print(d.shape)
  time = f.time.values[:]
  attsin = f.attrs
# d.positive = outpos[fi]
  print('above wait')
# w = sys.stdin.readline()

  datumyr = 1979
  datum_start_month = 1 
  start_month = 1 
  end_month = 12
# tunits = 'days since ' str(datumyr) + '-01-01 00:00:00'
  yrs = [time[1].year]
  t, tbds, tunits = fix_dataset_time.monthly_times(datumyr, yrs, datum_start_month, start_month,end_month)

#%% Initialize and run CMOR
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4 ,logfile='cmorLog.' + outputVarName[vn] + '.' + str(yrs[0]) +'.txt')
  for origatt in attsin.keys():
     cmor.set_cur_dataset_attribute(origatt,attsin[origatt])
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

  cmorLat = cmor.axis("latitude", coord_vals=lat[:].values, cell_bounds=f.latitude_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:].values, cell_bounds=f.longitude_bnds.values, units="degrees_east")
# cmorLev = cmor.axis("plev37-ERA5", coord_vals=lev[:].values*100., units="Pa")
  cmorTime = cmor.axis("time", coord_vals=t, cell_bounds=tbds, units= tunits)
  axes = [cmorTime, cmorLat, cmorLon]
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName[vn],outputUnits[vn],axes,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
  gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
  paths = os.getcwd().split('/inputs')
  path_to_code = f"/inputs{paths[1]}"  # location of the code in the obs4MIPs GitHub directory
  full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/{path_to_code}"
  cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()
  print('done with ',vn,' ', fi)

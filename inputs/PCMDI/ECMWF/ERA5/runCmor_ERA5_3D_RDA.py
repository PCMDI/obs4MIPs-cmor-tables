import cmor
import xcdat as xc
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import numpy as np
import cftime
import sys,os,glob

sys.path.append("../../../misc/") # Path to obs4MIPsLib
import obs4MIPsLib

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/ECMWF/'
inputFilePathend = 'ERA5/RDA/'

#inputFileName = ['adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580190896.023251-25621-38-f188c480-a5cd-4284-84a7-5757315ca044.nc']
inputVarName = ['T','U','V','Z'] 
outputVarName = ['ta','ua','va','zg']  
outputUnits = ['K','m s-1','m s-1','Pa'] 

'''
inputFileName = ['adaptor.mars.internal-1582240823.3820484-23715-16-fe2f1d48-67a6-479f-9d83-6356ce7cbecb.nc','adaptor.mars.internal-1582240823.3820484-23715-16-fe2f1d48-67a6-479f-9d83-6356ce7cbecb.nc']
inputVarName = ['ewss', 'nsss']
outputVarName = ['tauu','tauv']
outputUnits = ['Pa','Pa']
outpos = ['down','down']
'''

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE..
for vn,fi in enumerate(inputVarName):
 print(fi, outputVarName[vn])
#w = sys.stdin.readline()
 inputFilePath = inputFilePathbgn+inputFilePathend + outputVarName[vn] + '/'
 files_yearly = glob.glob(inputFilePath + '*.nc')
 files_yearly.sort()

 for fi in files_yearly:
  f = xc.open_dataset(fi,decode_times=False, decode_cf=False)
  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')
  d = f[inputVarName[vn]].values
  lat = f.latitude
  lon = f.longitude
  print(d.shape)
  time = f.time.values[:]
# d.positive = outpos[fi]

#%% Initialize and run CMOR
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

  cmorLat = cmor.axis("latitude", coord_vals=lat[:].values, cell_bounds=f.latitude_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:].values, cell_bounds=f.longitude_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=time, cell_bounds=f.time_bnds.values, units= f.time.units)
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

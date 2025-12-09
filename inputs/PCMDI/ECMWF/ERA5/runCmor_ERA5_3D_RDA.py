import cmor
import xcdat as xc
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import numpy as np
import cftime
import sys,os,glob
import datetime

sys.path.append("../../../misc/") # Path to obs4MIPsLib
import obs4MIPsLib
import fix_dataset_time

ver = datetime.datetime.now().strftime('v%Y%m%d')

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/ECMWF/'
inputFilePathend = 'ERA5/RDA/'

inputVarName = ['T','U','V','Z']
outputVarName = ['ta','ua','va','zg']  
outputUnits = ['K','m s-1','m s-1','m'] 

multi  = True
if multi == True:
 vari = sys.argv[1]
 outputVarName = [vari]

 if vari == 'ta':
    inputVarName = ['T'] 
    outputUnits = ['K']
 if vari == 'ua':
    inputVarName = ['U'] 
    outputUnits = ['m s-1']
 if vari == 'va':
    inputVarName = ['V']
    outputUnits = ['m s-1']
 if vari == 'zg':
    inputVarName = ['Z']
    outputUnits = ['m']
    divconv = 9.81

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE..

for vn,fi in enumerate(inputVarName):
 print(fi, outputVarName[vn])
#w = sys.stdin.readline()
 inputFilePath = inputFilePathbgn+inputFilePathend + outputVarName[vn] + '-plev37/'
 files_yearly = glob.glob(inputFilePath + '*.nc')
 files_yearly.sort()

 for fi in files_yearly:
  f = xc.open_dataset(fi,decode_times=True, decode_cf=True)
# f.level.attrs['axis'] = 'Z'
  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')
  d = f[inputVarName[vn]].values
  lat = f.latitude
  lon = f.longitude
  lev = f.level
  print(d.shape)
  time = f.time.values[:]
  attsin = f.attrs

  if outputVarName[vn] == 'zg': d = np.divide(d,divconv)

# print(f)
# w = sys.stdin.readline()

  datumyr = 1979
  datum_start_month = 1
  start_month = 1
  end_month = 12
# tunits = 'days since ' str(datumyr) + '-01-01 00:00:00'
  yrs = [time[1].year]
  t, tbds, tunits = fix_dataset_time.monthly_times(datumyr, yrs, datum_start_month, start_month,end_month)

#%% Initialize and run CMOR
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.' + outputVarName[vn] + '.' + str(yrs[0]) +'.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

  cmorLat = cmor.axis("latitude", coord_vals=lat[:].values, cell_bounds=f.latitude_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:].values, cell_bounds=f.longitude_bnds.values, units="degrees_east")
  cmorLev = cmor.axis("plev37-ERA5", coord_vals=lev[:].values*100., units="Pa")
# cmorLev = cmor.axis("plev37-ERA5", coord_vals=lev[:].values*100., cell_bounds=f.level_bnds.values*100., units="Pa") # INCL linear plev_bnds 

  cmorTime = cmor.axis("time", coord_vals=t, cell_bounds=tbds, units= tunits)
  axes = [cmorTime,cmorLev,cmorLat,cmorLon]
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName[vn] + '-plev37',outputUnits[vn],axes,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
  git_commit_number = obs4MIPsLib.get_git_revision_hash()
  path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
  full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
  cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")
  cmor.set_cur_dataset_attribute("version",ver)

  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()
  print('done with ',vn,' ', fi)

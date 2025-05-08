import cmor
import xcdat as xc
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import numpy as np
import cftime
import sys,os,glob

sys.path.append("../../misc/") # Path to obs4MIPsLib
import obs4MIPsLib
import fix_dataset_time

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_SImon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputJson = 'OSI-SAF_input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/EUMETSAT/OSI-SAF-450-a-3-0/'
inputFilePathend = 'v20231201/'

inputVarName = 'ice_conc'
outputVarName = 'sic'    
outputUnits = '%' 

yrr = range(1978,2020)
yrs = list(yrr)

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE..
#for vn,fi in enumerate(inputVarName):
for yr in yrs[0:1]: 
#w = sys.stdin.readline()
 inputFilePath = inputFilePathbgn+inputFilePathend + '*1979*.nc' 
 files_yearly = glob.glob(inputFilePath)
 files_yearly.sort()
 fi = inputFilePath

#for fi in files_yearly:
 for yr in yrs[0:1]:
         
  f = xc.open_mfdataset(fi,decode_times=True, decode_cf=True)
  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')
  d = f[inputVarName].values
# lat = f.latitude
# lon = f.longitude
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
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4 ,logfile='cmorLog.' + outputVarName + '.' + str(yrs[0]) +'.txt')
  for origatt in attsin.keys():
     cmor.set_cur_dataset_attribute(origatt,attsin[origatt])
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

  grid_table_id = cmor.load_table('../../../Tables/obs4MIPs_grids.json')
  cmor.set_table(grid_table_id)

  grid = gen_irreg_grid(d.shape[1], d.shape[2])

  y_axis_id = cmor.axis(table_entry='y_deg', units='degrees',
                          coord_vals=grid.y, cell_bounds=grid.y_bnds)
  x_axis_id = cmor.axis(table_entry='x_deg', units='degrees',
                          coord_vals=grid.x, cell_bounds=grid.x_bnds)

  grid_id = cmor.grid(axis_ids=[y_axis_id, x_axis_id],
                        latitude=grid.lat,
                        longitude=grid.lon,
                        latitude_vertices=grid.lat_bnds,
                        longitude_vertices=grid.lon_bnds)


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

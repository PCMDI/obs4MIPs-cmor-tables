import cmor
import xcdat as xc
import numpy as np
import json
import sys
import glob

sys.path.append("../../../misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Aday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'PRISM_OSU_inputs.json' ; # Update contents of this file to set your global_attributes

vars_lst = ['PPT','TMAX','TMEAN', 'TMIN'] 
#vars_lst = ['PPT']

for vr in vars_lst:

 inputDatasets = '/p/user_pub/PCMDIobs/obs4MIPs_input/OSU/PRISM/daily/' + vr + '/*.nc' # change to local path on user's machine where files are stored

 units_mult_conv = 1
 if vr == 'PPT':
   outputVarName = 'pr'
   outputUnits = 'kg m-2 s-1'
   units_conv = 1/86400. 
 if vr == 'TMAX':
   outputVarName = 'tasmax'
   outputUnits = 'K'
   units_conv = 273.15
 if vr == 'TMIN':
   outputVarName = 'tasmin'
   outputUnits = 'K'
   units_conv = 273.15
 if vr == 'TMEAN':
   outputVarName = 'tas'
   outputUnits = 'K'
   units_conv = 273.15

 lst = glob.glob(inputDatasets)
 lst.sort()
 lst = lst[0:len(lst)-1]

 print('Number of files ', len(lst))

 for yearlyFile in lst:

  f = xc.open_mfdataset(yearlyFile, mask_and_scale=True, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')

  d = f[vr]
  if vr == 'PPT': d = np.multiply(d,units_conv)
  if vr in ['TMAX','TMIN','TMEAN']: d = np.add(d,units_conv)
  time = f.time
  tunits = time.units
  lat = f.lat   
  lon = f.lon   
  lat['axis'] = "Y"
  lon['axis'] = "X"
  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')
  lat_bounds = f.lat_bnds
  lon_bounds = f.lon_bnds
  time_bounds = f.time_bnds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history)

  cmorLat = cmor.axis("latitude", coord_vals=lat.values, cell_bounds=f.lat_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon.values, cell_bounds=f.lon_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals= np.double(f.time.values), cell_bounds= np.double(time_bounds.values), units= tunits)
  axes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d["units"] = outputUnits
  varid   = cmor.variable(outputVarName,str(d.units.values),axes,missing_value=1.e20)
# values  = np.array(d[:],np.float32)
  values = np.where(np.isnan(d),1.e20,d)

# Appene valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_variable_attribute(varid,'valid_min','f',-1.8) # set manually for the time being
  cmor.set_variable_attribute(varid,'valid_max','f',45.)

# Add GitHub commit ID attribute to output CMOR file
  gitinfo = obs4MIPsLib.getGitInfo("./")
# gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
  commit_num = gitinfo[0].split(':')[1].strip()
  paths = os.getcwd().split('/inputs')
  path_to_code = f"/inputs{paths[1]}"
  full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{commit_num}{path_to_code}"
  cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()
  print('done processing ', yearlyFile)

import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys, os
sys.path.append("../../../inputs/misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib
import cftime
import glob

#%% User provided input
# TODO don't have a currently support obs4MIPs table for hourly site specific data
cmorTable = '../../../Tables/obs4MIPs_A1hrPt.json'
inputJson = 'ARMBE_SGP_ATM.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/LLNL/ARMBE_Vxy/sgparmbeatmC1.c1.20180101.003000.nc'
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/LLNL/ARMBE_Vxy/sgparmbeatmC1.c1/sgparmbeatmC1.c1.*.nc'

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds


# 2D vars
vrs = ['precip_rate_sfc','temperature_sfc','u_wind_sfc','v_wind_sfc','relative_humidity_sfc','sensible_heat_flux_baebbr','latent_heat_flux_baebbr']
# 3D vars
#vrs = ['u_wind_p','v_wind_p', 'temperature_p', 'relative_humidity_p']

vrs = ['precip_rate_sfc']

for vr in vrs:
  print(vr)
  if vr =='precip_rate_sfc':
     inputVarName = vr  # Unit is mm/hour
     outputVarName = 'pr'
     outputUnits = 'kg m-2 s-1'
  if vr =='temperature_sfc':
     inputVarName = vr  
     outputVarName = 'tas'
     outputUnits = 'K'
  if vr =='temperature_p':
     inputVarName = vr 
     outputVarName = 'ta'
     outputUnits = 'K'
  if vr =='u_wind_sfc':
     inputVarName = vr 
     outputVarName = 'uas'
     outputUnits = 'm s-1'
  if vr =='u_wind_p':
     inputVarName = vr 
     outputVarName = 'ua'
     outputUnits = 'm s-1'
  if vr =='v_wind_sfc':
     inputVarName = vr 
     outputVarName = 'vas'
     outputUnits = 'm s-1'
  if vr =='v_wind_p':
     inputVarName = vr 
     outputVarName = 'va'
     outputUnits = 'm s-1'
  if vr =='relative_humidity_sfc':
     inputVarName = vr 
     outputVarName = 'hurs'
     outputUnits = '%'
  if vr =='relative_humidity_p':
     inputVarName = vr 
     outputVarName = 'hur'
     outputUnits = '%'
  if vr =='sensible_heat_flux_baebbr':
     inputVarName = vr 
     outputVarName = 'hfss'
     outputUnits = 'W m-2'
  if vr =='latent_heat_flux_baebbr':
     inputVarName = vr 
     outputVarName = 'hfls'
     outputUnits = 'W m-2'

  files_yearly = glob.glob(inputFilePath)
  files_yearly.sort() 
  
  for file_yr in files_yearly:
    f = xr.open_dataset(file_yr,decode_times=False)
# f = xr.open_mfdataset(inputFilePath,decode_times=False)
# f = xc.open_mfdataset(inputFilePath, mask_and_scale=False, decode_times=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
# f = f.isel(time=slice(0,24)) # TEST 2 DAYS ONLY

    d = f[inputVarName]
    lat = f.lat.values  
    lon = f.lon.values  
    time = f.time.values ; # Rather use a file dimension-based load statement
    tbds = f.time_bounds.values
# tunits = "seconds since 2013-01-01 00:00:00 0:00"
    tunits = "seconds since 1970-1-1 0:00:00 0:00"

    f = f.bounds.add_bounds("T")
# UNIT Conversions 
    if outputVarName == 'pr': d = np.divide(d,86400.*24.)
    d = np.where(np.isnan(d),1.e20,d)

#%% Initialize and run CMOR - for more information see https://cmor.llnl.gov/mydoc_cmor3_api/
    cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
    cmor.dataset_json(inputJson)
    cmor.load_table(cmorTable)
    cmor.set_cur_dataset_attribute('original_history',f.attrs) 
    cmor.set_cur_dataset_attribute("product","site-observations")

    j = open(inputJson)
    jdic = json.load(j)
    site_id = jdic['site_id']
    cmor.set_cur_dataset_attribute("grid_label","site-"+ site_id)

# cftime.date2num(tdc,tunits)
# cmorLat = cmor.axis("latitude1", coord_vals=np.array([lat]), units="degrees_north")

    cmorLat = cmor.axis("latitude1", coord_vals=np.array([lat]), units="degrees_north")
    cmorLon = cmor.axis("longitude1", coord_vals=np.array([lon]), units="degrees_east")
    cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
# cmorTime = cmor.axis("time", coord_vals=cftime.date2num(time,tunits), cell_bounds=cftime.date2num(f.time_bnds,tunits), units= tunits)

    if vr == 'temperature_sfc':
      cmorHeight = cmor.axis("height2m", coord_vals=np.array([2.0]), units="m")
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
    if vr in ['u_wind_sfc', 'v_wind_sfc']:
      cmorHeight = cmor.axis("height10m", coord_vals=np.array([10.0]), units="m")
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
    elif vr in ["u_wind_p", "v_wind_p", "temperature_p", "relative_humidity_p"]:
      cmorHeight = cmor.axis("plev37-ERA5", coord_vals=np.array(f.pressure.values),units='hPa') 
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
    else:
      cmoraxes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    if outputVarName in ['hfss', 'hfls']:
      varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,positive="up",missing_value=1.e20)
    else:
      varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
    values  = np.array(d[:],np.float32)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
    git_commit_number = obs4MIPsLib.get_git_revision_hash()
    path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1] 
    full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
    cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
    cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
#cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bounds.values) ; # Write variable with time axis
    cmor.write(varid,values) ; # Write variable with time axis
    f.close()
    cmor.close()

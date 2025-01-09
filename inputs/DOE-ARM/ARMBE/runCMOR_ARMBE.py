import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json

#%% User provided input
# TODO don't have a currently support obs4MIPs table for hourly site specific data
cmorTable = '../../../Tables/obs4MIPs_1hrPt.json'
inputJson = 'ARMBE_ATM.json' ; # Update contents of this file to set your global_attributes
#inputFilePath = '/Users/zhang40/Documents/ARM/armbe_sample/sgparmbeatmC1.c1.20200101.003000.nc'
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/LLNL/ARMBE_Vxy/sgparmbeatmC1.c1.20180101.003000.nc'

# 2D vars
vrs = ['precip_rate_sfc','temperature_sfc','u_wind_sfc','v_wind_sfc','relative_humidity_sfc','sensible_heat_flux_baebbr','latent_heat_flux_baebbr']
# 3D vars
#vrs = ['u_wind_p','v_wind_p', 'temperature_p', 'relative_humidity_p']


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

### USER MAY NOT NEED TO CHANGE ANYTHING BELOW THIS LINE...

# Open and read input netcdf file
  f = xr.open_dataset(inputFilePath,decode_times=False)
  d = f[inputVarName]
  lat = f.lat.values 
  lon = f.lon.values 
  print(lat, lon)
  time = f.time.values ; # Rather use a file dimension-based load statement
  tbds = f.time_bounds.values
#f = f.bounds.add_bounds("T")
# UNIT Conversions 
  if outputVarName == 'pr': d = np.divide(d,86400.*24.)
  d = np.where(np.isnan(d),1.e20,d)

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
  cmor.set_cur_dataset_attribute('original_history',f.attrs) 

  cmorLat = cmor.axis("latitude1", coord_vals=np.array([lat]), units="degrees_north")
  cmorLon = cmor.axis("longitude1", coord_vals=np.array([lon]), units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
  if vr == 'temperature_sfc':
      cmorHeight = cmor.axis("height2m", coord_vals=np.array([2.0]), units="m")
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
  if vr in ['u_wind_sfc', 'v_wind_sfc']:
      cmorHeight = cmor.axis("height10m", coord_vals=np.array([10.0]), units="m")
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
  elif vr in ["u_wind_p", "v_wind_p", "temperature_p", "relative_humidity_p"]:
      cmorHeight = cmor.axis("plev37", coord_vals=np.array(f.pressure.values),units='hPa') 
      cmoraxes = [cmorTime, cmorLat, cmorLon, cmorHeight]
  else:
      cmoraxes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  if outputVarName in ['hfss', 'hfls']:
      varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,positive="up",missing_value=1.e20)
  else:
      varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)

  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_variable_attribute(varid,'valid_min','f',2.0)
  cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
#cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bounds.values) ; # Write variable with time axis
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()

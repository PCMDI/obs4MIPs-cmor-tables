import cmor
import xarray as xa
import xcdat as xc
import numpy as np
import sys

sys.path.append("../../misc/") 
from fix_dataset_time import monthly_times

def extract_date(ds):   # preprocessing function when opening multiple files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'TropFlux-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/INCOIS-NIO-IPSL/TropFlux/monthly/data/'
inputVarName = ['swr','lwr','q2m','ws','t2m','sst','netflux','lhf','shf','taux','tauy']
outputVarName = ['rss','rls','huss','sfcWind','tas','ts','hfns','hfls','hfns','tauu','tauv']
outputUnits = ['W m-2','W m-2','1','m s-1','K','K','W m-2','W m-2','W m-2','Pa','Pa']
outpos = ['up','up','','','','','up','up','up','down','down']     #,'','up','down','down','up','','','','down','down','']
####['W m-2',"W m-2","Pa",'kg m-2 s-1','W m-2','W m-2','W m-2','W m-2',"m s-1",'m s-1','m s-1','Pa','Pa','K]]

for fi in range(len(inputVarName)):
# print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+'/' + inputVarName[fi] + '/*.nc' 
# f = xc.open_mfdataset(inputFilePath, decode_times=False, decode_cf=False,preprocess=extract_date)
  f = xc.open_mfdataset(inputFilePath, decode_times=True, decode_cf=True,preprocess=extract_date)

  d = f[inputVarName[fi]]
  if outputVarName[fi] in ['tas','ts']: d = np.add(d,273.15)
  if outputVarName[fi] in ['hfss','hfls','hfns','rss','rls']: 
      d = np.multiply(d,-1.)
      pos = outpos[fi]

  lat = f.latitude.values
  lon = f.longitude.values 
  time = f.time.values ; # Rather use a file dimension-based load statement

  datum = f.time.values[0].year
  datummnth = f.time.values[0].month
  start_month = datummnth
  end_month = f.time.values[f.time.values.shape[0]-1].month
  yrs = []
  years = [date.year for date in f.time.values]
  for i in years:
     if i not in yrs: yrs.append(i)

  time_adj,time_bounds_adj,tunits = monthly_times(datum, yrs, datum_start_month=datummnth, start_month=start_month, end_month=end_month)

# w = sys.stdin.readline()

  f = f.bounds.add_missing_bounds(axes=['X', 'Y']) # ONLY IF BOUNDS NOT IN INPUT FILE
  f = f.bounds.add_bounds('T')
# tunits = "days since 1950-01-01 00:00:00"

#%% Initialize and run CMOR - more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= inputVarName[fi] + '_cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

  cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.latitude_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.longitude_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=time_adj[:], cell_bounds=time_bounds_adj, units=tunits)
  cmoraxes = [cmorTime,cmorLat, cmorLon]

  if outputVarName[fi] in ['tas','ts','sfcWind','huss']:
    varid = cmor.variable(outputVarName[fi],outputUnits[fi],cmoraxes,missing_value=1.e20)
  if outputVarName[fi] in ['hfls','hfss','hfns','tauu','tauv','rss','rls']:
    varid = cmor.variable(outputVarName[fi],outputUnits[fi],cmoraxes,missing_value=1.e20,positive = pos)

  values  = np.array(d[:],np.float32)
  values = np.where(values < -1.e10,1.e20,values)
  values = np.where(np.isnan(values),1.e20,values)


  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()
  print('done with ', outputVarName[fi], str(np.average(np.ma.array(values[0]))))

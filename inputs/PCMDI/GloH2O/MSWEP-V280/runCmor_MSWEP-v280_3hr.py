import cmor
import xcdat as xc 
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import cftime
import glob
import numpy as np
import sys, os, glob

freq = 'A3hr' #'Amon' #'Aday'  #'Amon'
version = 'Past'  # 'Past'  #'Past-nogauge'  #'Past'  # NRT   # Past-nogauge 
cmorTable = '../../../../Tables/obs4MIPs_A3hr.json'
avgp = '3hourly'
inputJson = 'MSWEP-V280-' + version + '_input.json' ; 

print('inputJson ', inputJson)

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

inputFilePathbgn = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' 
inputFilePathend = version.replace('-','_') 

lsttmp = glob.glob(inputFilePathbgn+inputFilePathend + '/*.nc')  # TRAP ALL FILES
lsttmp.sort()

lstyrs = []  # TRAP ALL YEARS
for i in lsttmp:
  stryr = i.split(avgp+'/')[1].split('.nc')[0][0:4]
  if stryr not in lstyrs:lstyrs.append(stryr)
lstyrs.sort()

inputVarName = 'precipitation'
inputUnits = 'mm/3hr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

lstyrs = ['1979', '1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']
#lstyrs = ['1981']

mos = ['01','02','03','04','05','06','07','08','09','10','11','12']

for yr in lstyrs:  # LOOP OVER YEARS
  print('starting ', yr)
  pathind = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' + version + '/' + avgp + '/' + yr + '*.nc'
  fc = xc.open_mfdataset(pathind, mask_and_scale=False, decode_times=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
  fc = fc.bounds.add_missing_bounds(axes=['X', 'Y'])
  fc = fc.bounds.add_bounds('T')
  tunits = "days since 1900-1-1 00:00:00"  #fc.time.units
  lat = fc.lat
  lon = fc.lon   #.values
  lat['axis'] = "Y"
  lon['axis'] = "X"

  for mo in mos:

   fcc = fc.sel(time=slice(yr + "-" + mo,yr + "-" + mo))
   tdc = fcc.time.values[:]  # days-since to hours-since
   tbds =fcc.time_bnds.values[:]
   ddc = fcc[inputVarName].values
   conv = 3600.*24./8.  # 3hrly
   d = np.divide(ddc,conv)

   cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= 'cmorLog.txt')
   cmor.dataset_json(inputJson)
   cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

   cmorLat = cmor.axis("latitude", coord_vals=lat.values, cell_bounds=fc.lat_bnds.values, units="degrees_north")
   cmorLon = cmor.axis("longitude", coord_vals=lon.values, cell_bounds=fc.lon_bnds.values, units="degrees_east")
   cmorTime = cmor.axis("time", coord_vals= cftime.date2num(tdc,tunits), cell_bounds=cftime.date2num(tbds,tunits), units= tunits)
   axes = [cmorTime, cmorLat, cmorLon]
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
   varid   = cmor.variable(outputVarName,outputUnits,axes,missing_value=1.e20)
   values  = np.array(d[:],np.float32)

#  print('above cmor.write')
# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
   cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
   cmor.write(varid,values) ; # Write variable with time axis
   cmor.close()
   print('done cmorizing ', yr,' ',mo)
   fc.close()


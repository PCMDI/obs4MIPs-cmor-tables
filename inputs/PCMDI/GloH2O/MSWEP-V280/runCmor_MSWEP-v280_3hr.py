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
 
#w = sys.stdin.readline()

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

def dom(yr,mo):
  if mo in ['01','03','05','07','08','10','12']: endofMoDay = '31' 
  if mo in ['04','06','09','11']: endofMoDay = '30'
  if mo == '02': endofMoDay = '28'
  if mo == '02' and yr in ['1980','1984', '1988', '1992', '1996', '2000','2004', '2008', '2012', '2016', '2020']: endofMoDay = '29'
  return endofMoDay
#April, June, September, and November
#January, March, May, July, August, October, and December.

inputVarName = 'precipitation'

inputUnits = 'mm/3hr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

lstyrs = ['1979', '1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']

lstyrs = ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']


#lstyrs = ['1979','1980']
#lstyrs = ['1981']

for yr in lstyrs:  # LOOP OVER YEARS
#lstall = glob.glob(inputFilePathbgn+inputFilePathend + '*' + yr + '*.nc')
#lstall.sort()
#print(yr,'len of lstall', len(lstall))
#w = sys.stdin.readline()

 pathin = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' + version + '/' + avgp + '/' + yr + '*.nc'
#pathin = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' + version.replace('-','_') + '/' + avgp + '/' + yr + '*.nc'

 if avgp == 'Daily': mos = ['01','02','03','04','05','06','07','08','09','10','11','12'] 
 if avgp == 'Monthly': mos = ['01']
 if avgp == '3hourly': mos = ['01','02','03','04','05','06','07','08','09','10','11','12'] 

 dayz = []
 tmp = glob.glob(pathin)
 for t in tmp:
  tmp2 = t.split('/')[10]
  tmp3 = tmp2.split('.')[0]
  tmp4 = tmp3.split(yr)[1]
  print(tmp4)
  if tmp4 not in dayz: dayz.append(tmp4)
 dayz.sort()
 print(len(dayz))
#w = sys.stdin.readline()

#print('above fc')
#fc = xc.open_mfdataset(pathin, mask_and_scale=False, decode_times=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
#fc = fc.bounds.add_missing_bounds(axes=['X', 'Y', 'T'])   
#print('below fc')

#for mo in mos:
#  endmo = dom(yr,mo)

 for dy in dayz:
 
   print('above fc')
   pathind = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' + version + '/' + avgp + '/' + yr + dy + '*.nc'

   fc = xc.open_mfdataset(pathind, mask_and_scale=False, decode_times=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
   fc = fc.bounds.add_missing_bounds(axes=['X', 'Y', 'T'])
   print('below fc')
   fa = xc.open_mfdataset(pathind, mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
   units = fa.time.units
 
   if avgp == 'Daily':
    datestart = yr + '-' + mo + '-01'
    dateend =   yr + '-' + mo + '-' + endmo 

   if avgp == 'Monthly':
    datestart = yr + '-01'  
    dateend =   yr + '-12'
#  if yr == '1979': datestart = yr + '-02'

   if avgp == '3hourlydfdd':
    if str(dy) in ['1','2','3','4','5','6','7','8','9']: dy = '0' + str(dy)
    datestart = yr + '-' + mo + '-' + str(dy) + ' 00'
    dateend =   yr + '-' + mo + '-' + str(dy) + ' 21'
    if yr == '1979': datestart = yr + '-' + mo + '-01-00'

#  print('above fc')
#  fc = xc.open_mfdataset(pathin, mask_and_scale=False, decode_times=True, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
#  fc = fc.bounds.add_missing_bounds()   
#  print('below fc')

#  tdc = fc.time.sel(time=slice(datestart, dateend)).values
#  tbds = fc.time_bnds.sel(time=slice(datestart, dateend)).values
#  ddc = fc[inputVarName].sel(time=slice(datestart, dateend)).values

   tdc = fc.time.values
   tbds = fc.time_bnds.values
   ddc = fc[inputVarName].values

#  tdc['axis'] = "T"
#  print('below tdc print')

#  units = tdc.time.encoding['units']
#  calendar = tdc.time.encoding['calendar']
#  tdc = encode_cf_datetime(tdc.time, units, calendar)
#  print('tdc ', tdc[0])

#  ddc = ddc.to_numpy()    
#  print('ddc[0:4,100,100]', ddc[0:4,100,100])

#  units = tbds.time.encoding['units']
#  calendar = tbds.time.encoding['calendar']
#  tbds = encode_cf_datetime(tbds.values, units, calendar)
#  print('tbds ', tbds[0])

#  THE UNITS IN THE ORIGINAL FILES DEPEND ON FREQUENCY
   if avgp == 'Daily':  conv = 3600.*24.
   if avgp == '3hourly':  conv = 3600.*24.*3.
   if avgp == 'Monthly': conv = 1000*3600.*24.*float(endmo) 
   d = np.divide(ddc,conv)
   print('d read',d.shape)

   lat = fc.lat
   lon = fc.lon   #.values

   lat['axis'] = "Y"
   lon['axis'] = "X"

   tunits = "days since 1900-1-1 00:00:00"

#  print('above cmor ', yr,' ',mo)
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


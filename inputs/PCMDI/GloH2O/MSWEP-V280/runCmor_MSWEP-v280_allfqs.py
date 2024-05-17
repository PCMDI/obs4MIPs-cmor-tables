import cmor
import xcdat as xc 
import xarray as xr
from xarray.coding.times import encode_cf_datetime
import cftime
import glob
import numpy as np
import sys, os, glob
sys.path.append("../../../misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib



freq = 'Aday' #'Amon' #'Aday'  #'A3hr'
version = 'Past'  #-nogauge'  # 'Past'  #'Past-nogauge'  #'Past'  # NRT   # Past-nogauge 

if freq == 'Amon': avgp = 'Monthly'
if freq == 'A3hr': avgp = '3hourly'
if freq == 'Aday': avgp = 'Daily'

cmorTable = '../../../../Tables/obs4MIPs_ATABLE.json'  #A3hr
cmorTable = cmorTable.replace('ATABLE',freq) 

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
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

lstyrs = ['1979', '1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020']
#lstyrs = ['1981']

for yr in lstyrs:  # LOOP OVER YEARS
   print('starting ', yr)
   yr = yr    #+ '00' #day    # '001 for 3hr'
   pathind = '/p/user_pub/PCMDIobs/obs4MIPs_input/GloH2O/MSWEP-V280/MSWEP_V280/' + version + '/' + avgp + '/' + yr + '*.nc'
   fc = xc.open_mfdataset(pathind, mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date, data_vars='all')
   fc = fc.bounds.add_missing_bounds(axes=['X', 'Y'])
   fc = fc.bounds.add_bounds('T')
#  tunits = "hours since 1900-1-1 00:00:00"  #fc.time.units
#  tunits = "days since 1900-1-1"
   tunits = fc.time.units
   tdc = np.multiply(fc.time.values[:],1) #,24)  # days-since to hours-since
   tbds =np.multiply(fc.time_bnds.values[:],1) #,24)  #added last 2 for monthly
   ddc = fc[inputVarName].values
   if freq == 'Amon': conv = 3600.*24.*30.4  #OK?
   if freq == 'Aday': conv = 3600.*24.   #OK
   if freq == 'A3hr': conv = 3600.*24./8. #OK
   d = np.divide(ddc,conv)
   lat = fc.lat
   lon = fc.lon   
   lat['axis'] = "Y"
   lon['axis'] = "X"

   cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile= 'cmorLog.txt')
   cmor.dataset_json(inputJson)
   cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history

   cmorLat = cmor.axis("latitude", coord_vals=lat.values, cell_bounds=fc.lat_bnds.values, units="degrees_north")
   cmorLon = cmor.axis("longitude", coord_vals=lon.values, cell_bounds=fc.lon_bnds.values, units="degrees_east")
   cmorTime = cmor.axis("time", coord_vals=tdc, cell_bounds=tbds, units= tunits)
   axes = [cmorTime, cmorLat, cmorLon]
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
   varid   = cmor.variable(outputVarName,outputUnits,axes,missing_value=1.e20)
   values  = np.array(d[:],np.float32)

# Provenance info 
   gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
   paths = os.getcwd().split('/inputs')
   path_to_code = f"/inputs{paths[1]}"  # location of the code in the obs4MIPs GitHub directory
   full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/{path_to_code}"
   cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
   cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
   cmor.write(varid,values) ; # Write variable with time axis
   cmor.close()
   print('done cmorizing ', yr)
   fc.close()


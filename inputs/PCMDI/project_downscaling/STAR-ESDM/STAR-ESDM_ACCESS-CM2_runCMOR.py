import cmor
import xcdat as xc
import xarray as xr
import cftime
import numpy as np
import sys, os, glob



#sys.path.append("../../../misc") # Path to obs4MIPsLib used to trap provenance
#import obs4MIPsLib

targetgrid = 'orig'

#cmorTable = '../../../../Tables/obs4MIPs_Aday.json'
cmorTable = 'obs4MIPs_Aday.json'
inputJson = 'STAR-ESDM_ACCESS-CM2_input.json'

inputFilePath = '/global/cfs/projectdirs/m3522/cmip6/STAR-ESDM/ssp245/downscaled.ACCESS-CM2.r1i1p1f1.pr.ssp245.gn.nclimgrid.star.1950.2100.tllc.nc'
inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
yrs = [1]

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds


yrs = [('1950','1954'),('1955','1959'),('1960','1964'),('1965','1969'),('1970','1974'),('1975','1979'),('1980','1984'),('1985','1989'),('1990','1994'),('1995','1999'),('2000','2004'),('2005','2009'),('2010','2014')]
yrs = [yrs[0]]

fi = inputFilePath
fc = xc.open_dataset(fi,decode_times=False,use_cftime=False)   #,preprocess=extract_date)
fc.time.attrs['calendar'] = '365_day'
fd = fc
fd.coords['time'] = cftime.num2date(fc.time.values, 'days since 1950-01-01', calendar='365_day')
# fe = fd.sel(time=str('1951'))

for yr in yrs:
  f = fd.sel(time=slice(yr[0],yr[1]))

  print('above stop')
# w = sys.stdin.readline()

  d = f[inputVarName]
# d = np.divide(d,3600.)

  lat = f.latitude.values  #f.getLatitude()
  lon = f.longitude.values  #d.getLongitude()
  time = f.time.values   #d.get
  tunits = "days since 1950-01-01"

  print('below time')

# f = f.drop_vars(["lat_bounds","lon_bounds"])

  f = f.bounds.add_bounds("X")  #, width=0.5)
  f = f.bounds.add_bounds("Y")
  f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
#####del(time_bounds) ; # Cleanup
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)

  time_np = cftime.date2num(time,tunits)
  time_np = np.array(time_np[:],np.float32)  #time_np.astype(np.float32)  
  tbds_np = cell_bounds=cftime.date2num(f.time_bnds.values,tunits)
  tbds_np = np.array(tbds_np[:],np.float32)  #tbds_np.astype(np.float32)

# Create CMOR axes
  cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.latitude_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.longitude_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=time_np, cell_bounds=tbds_np, units= tunits)
  cmoraxes = [cmorTime,cmorLat, cmorLon]
# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

  cmor.set_variable_attribute(varid,'valid_min','f',2.0)
  cmor.set_variable_attribute(varid,'valid_max','f',3.0)

  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,len(time)) ; # Write variable with time axis
  cmor.close()
  f.close()
  print('done cmorizing ')
                                                          

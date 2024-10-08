import cmor
import xcdat as xc
import xarray as xr
import cftime
import numpy as np
import sys, os, glob

# TEST CASE OF USING CMOR WITH MODIFIED CORDEX SPECIFICATIONS WITH LOCA2 DATA @NERSC PERLMUTTER
# PJG  10052024


cmorTable = 'Downscaling_Aday.json'
inputJson = 'LOCA2_ACCESS-CM2_input.json'
inputFilePath = '/global/cfs/projectdirs/m3522/cmip6/LOCA2/ACCESS-CM2/0p0625deg/r1i1p1f1/historical/pr/pr.ACCESS-CM2.historical.r1i1p1f1.1950-2014.LOCA_16thdeg_v20220519.nc'

inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'
yrs = [1]

# FUNCTION USEFUL WHEN USING mfopen
def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

yrs = list(range(1950,2014))

for yr in yrs:
  fi = inputFilePath 
  fc = xc.open_dataset(fi,decode_times=True,use_cftime=True)   #,preprocess=extract_date)
  f = fc.sel(time=str(yr))
  d = f[inputVarName]

  lat = f.lat.values  #f.getLatitude()
  lon = f.lon.values  #d.getLongitude()
  time = f.time.values   #d.get
  tunits = "days since 1900-01-01"

# f = f.drop_vars(["lat_bounds","lon_bounds"])
  f = f.bounds.add_bounds("X") 
  f = f.bounds.add_bounds("Y")
  f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)

# Create CMOR axes
  cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals=cftime.date2num(time,tunits), cell_bounds=cftime.date2num(f.time_bnds.values,tunits), units= tunits)
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
  print('done cmorizing ',yr)
                                                          

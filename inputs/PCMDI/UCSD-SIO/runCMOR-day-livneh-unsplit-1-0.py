import cmor
import xcdat as xc
import numpy as np
import json
import sys
import glob

def extract_date(ds):   # preprocessing function when opening files
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Aday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'livneh-unsplit_UCSD-SIO_inputs.json' ; # Update contents of this file to set your global_attributes

vars_lst = ['PRCP']   #, 'tmax','tmin'] 

for vr in vars_lst:
 inputDatasets = '/p/user_pub/PCMDIobs/obs4MIPs_input/UCSD-SIO/nonsplit_precip/precip/livneh_unsplit_precip.*.nc' # change to local path on user's machine where files are stored
 lst = glob.glob(inputDatasets)
 lst.sort()

 print('Number of files ', len(lst))

 for yearlyFile in lst:

  f = xc.open_dataset(yearlyFile)
  d = f[vr]

  f.lon.attrs["axis"] = "X"
  f.lat.attrs["axis"] = "Y"
  f.Time.attrs["axis"] = "T"

  time = f.Time
  tunits = time.units
  lat = f.lat.values
  lon = f.lon.values

# f = f.bounds.add_missing_bounds() # create lat,lon, and time bounds

  f = f.bounds.add_missing_bounds(axes=['X', 'Y'])
  f = f.bounds.add_bounds('T')

  if vr == 'PRCP':
   outputVarName = 'pr'
   outputUnits = 'kg m-2 s-1'
   units_conv = 1/86400. 
  if vr == 'tmax':
   outputVarName = 'tasmax'
   outputUnits = 'K'
   units_conv = 273.15
  if vr == 'tmin':
   outputVarName = 'tasmin'
   outputUnits = 'K'
   units_conv = 273.15
  if vr == 'tas':
   outputVarName = 'tas'
   outputUnits = 'K'
   units_conv = 273.15

  lat_bounds = f.lat_bnds
  lon_bounds = f.lon_bnds
  time_bounds = f.Time_bnds

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history)

  cmorLat = cmor.axis("latitude", coord_vals=lat, cell_bounds=f.lat_bnds.values, units="degrees_north")
  cmorLon = cmor.axis("longitude", coord_vals=lon, cell_bounds=f.lon_bnds.values, units="degrees_east")
  cmorTime = cmor.axis("time", coord_vals= np.double(time.values), cell_bounds= np.double(time_bounds.values), units= tunits)
  axes = [cmorTime, cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d["units"] = outputUnits
  varid   = cmor.variable(outputVarName,str(d.units.values),axes,missing_value=1.e20)
  values  = np.array(d[:],np.float32)

  if vr == 'PRCP': values = np.multiply(values,units_conv)
  values[np.isnan(values)] = 1.e20

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_variable_attribute(varid,'valid_min','f',-1.8) # set manually for the time being
  cmor.set_variable_attribute(varid,'valid_max','f',45.)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values) ; # Write variable with time axis
  f.close()
  cmor.close()
#sys.exit()
  print('done processing ', yearlyFile)

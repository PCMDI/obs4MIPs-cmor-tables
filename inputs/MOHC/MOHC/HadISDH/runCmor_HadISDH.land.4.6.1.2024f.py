import cmor
import numpy as np
import xcdat as xc
import xarray as xr
import json
import sys, os
import pdb

# ISSUES:
# license in _CV.joson only gives Creative Commons license option. What can we not use other licenses? - OGL
# Need HadISDH source_id added into _CV.json file
# "HadISDH-land-4-6-1-2024f":{
#                "region":"global_land",
#                "source":"HadISDH.land.4.6.1.2024f (2025): HadISDH near surface humidity anomalies over land",
#                "source_type":"gridded_insitu",
#                "source_version_number":"5.0.2.0"
#   
# I'd rather provide anomalies - that is how HadCRUT5 is listed. But where would the climatology bounds be stored? This is crucial??? Are
# we happy with hussanom as inputvar and outputvar and specifc_humidity_anomaly as a new standard name?
# For now hussanom is added to the obs4MIPs_Amon.json but this doesn't include climatological bounds though.
# How to store additional info - uncertainty, actual values etc...
          


sys.path.append("../../../misc/")
from fix_dataset_time import make_continuous_bounds

CMOR_MDI = 1.e20 # I've set this as global variable

#%% User provided input
cmorTable = "../../../../Tables/obs4MIPs_Amon.json" ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'HadISDH.land.4.6.1.2024f.json' ; # Update contents of this file to set your global_attributes
# EDITABLE - where is the input file?
inputFilePathbgn = os.environ['SCRATCH']+'/RANDOM/'
inputFileName = ['huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc', 'huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc']  
inputVarName = ['huss', 'hussanom']    # I actually want to provide the anomaly field (hussa) rather than actual values.
outputVarName = ['huss', 'hussanom']
outputUnits = ['1', '1']    # its g/kg and I convert here to kg/kg

for fi in range(len(inputVarName)):
 inputFilePath = inputFilePathbgn
 #f = xr.open_dataset(inputFilePath+inputFileName[fi],decode_times=True,decode_cf=True)
 f = xr.open_dataset(inputFilePath+inputFileName[fi],decode_times=False,decode_cf=True)
# d = f[inputVarName[fi]] 
# d = d / 1000.
# d = np.where(np.less(d,-100),1.e20,d)
# d = np.where(np.isnan(d),1.e20,d)
# It doens't seem to like the above so I'm resetting NaNs first then transforming data
 d = f[inputVarName[fi]].values
 d = np.where(np.isnan(d), CMOR_MDI, d)
 d = np.where(np.less(d,-100), CMOR_MDI, d) # this shouldn't catch anything but might if using RH anomalies althuogh still really shouldn't
 d = np.where(d < CMOR_MDI, d / 1000., CMOR_MDI) 

# pdb.set_trace()

 lat = f.latitude.values  
 lon = f.longitude.values  
 time = f.time.values   

# BOUNDS GENERATED WITH XCDAT/XARRAY - but HadISDH already has bounds_lat, bounds_lon and bounds_time so may not need this?
 f = f.bounds.add_bounds("X") 
 f = f.bounds.add_bounds("Y") 
 f = f.bounds.add_bounds("T")


 # REPAIR TIME COORDINATE IF NECESSARY - HADISDH TIME BOUNDS ARE NOT CONTINUOUS
 if (np.sum(f.bounds_time.values[1:,0] - f.bounds_time.values[:-1,1]) == len(f.bounds_time.values)-1):
  # Then there is a 1 day gap between time boundaries
  f.bounds_time.values = make_continuous_bounds(f.bounds_time.values)


#%% Initialize and run CMOR - more information see https://cmor.llnl.gov/mydoc_cmor3_api/
 cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
 cmor.dataset_json(inputJson)
 cmor.load_table(cmorTable)

 cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.bounds_lat.values, units="degrees_north")
 cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.bounds_lon.values, units="degrees_east")
 cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=f.bounds_time.values, units=f.time.units)
 cmoraxes = [cmorTime,cmorLat, cmorLon]


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 varid   = cmor.variable(outputVarName[fi], outputUnits[fi], cmoraxes, missing_value=CMOR_MDI)
 values  = np.array(d[:], np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid, values) ; # Write variable with time axis
 f.close() 
 cmor.close()

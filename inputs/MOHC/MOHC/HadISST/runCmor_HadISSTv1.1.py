import cmor
import numpy as np
import xcdat as xc
import xarray as xr
import json
import sys, os
import cftime

sys.path.append("../../../misc/")
from fix_dataset_time import monthly_times

CMOR_MDI = 1.e20
#%% User provided input
cmorTable = "../../../../Tables/obs4MIPs_Amon.json" ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'HadISSTv1.1.json' ; # Update contents of this file to set your global_attributes
# EDITABLE - where is the input file?
inputFilePathbgn = os.environ['SCRATCH']+'/RANDOM/'
inputFileName = ['HadISST_sst.nc']  
inputVarName = ['sst']
outputVarName = ['ts']
outputUnits = ['K']

for fi in range(len(inputVarName)):
 inputFilePath = inputFilePathbgn
 f = xr.open_dataset(inputFilePath+inputFileName[fi],decode_times=True,decode_cf=True)
 #d = f[inputVarName[fi]] 
 #d = d + 273.15
 #d = np.where(np.less(d,-100),1.e20,d)
 #d = np.where(np.isnan(d),1.e20,d)
 d = f[inputVarName[fi]].values
 d = np.where(np.isnan(d), CMOR_MDI, d)
 d = np.where(np.less(d,-100), CMOR_MDI, d) # this shouldn't catch anything but might if using RH anomalies althuogh still really shouldn't
 d = np.where(d < CMOR_MDI, d + 273.15, CMOR_MDI) 

 lat = f.latitude.values  
 lon = f.longitude.values  
 time = f.time.values   

# BOUNDS GENERATED WITH XCDAT/XARRAY
 f = f.bounds.add_bounds("X") 
 f = f.bounds.add_bounds("Y") 
 f = f.bounds.add_bounds("T")

### REPAIR TIME COORDINATE - FIRST TWO VALUES WITH INPUT ARE NOT CORRECT
 datum = int(str(f.time.values[0]).split('-')[0])
 datummnth = int(str(f.time.values[0]).split('-')[1])
 start_month = datummnth
 end_month = int(str(f.time.values[f.time.values.shape[0]-1]).split('-')[1])
 yrs = []
 for t in f.time.values:
     yr = int(str(t).split('-')[0])
     if yr not in yrs: yrs.append(yr)
 time_adj,time_bounds_adj,tunits = monthly_times(datum, yrs, datum_start_month=datummnth, start_month=start_month, end_month=end_month)
###

#%% Initialize and run CMOR - more information see https://cmor.llnl.gov/mydoc_cmor3_api/
 cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
 cmor.dataset_json(inputJson)
 cmor.load_table(cmorTable)

 cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.latitude_bnds.values, units="degrees_north")
 cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.longitude_bnds.values, units="degrees_east")
 cmorTime = cmor.axis("time", coord_vals=time_adj[:], cell_bounds=time_bounds_adj, units=tunits)
#cmorTime = cmor.axis("time", coord_vals=time_adj[:], cell_bounds=cftime.date2num(time,tunits), units=tunits)
 cmoraxes = [cmorTime,cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 varid   = cmor.variable(outputVarName[fi],outputUnits[fi],cmoraxes,missing_value=1.e20)
 values  = np.array(d[:],np.float32)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid,values) ; # Write variable with time axis
 f.close() 
 cmor.close()

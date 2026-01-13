import cmor
import numpy as np
import xcdat as xc
import xarray as xr
import json
import sys, os
import pdb

# ISSUES:
# license in _CV.joson only gives Creative Commons license option. Why can we not use other licenses? - OGL add within the HadISDH.land.4.6.1.2024f.json file?
#   
# I'd rather provide anomalies - that is how HadCRUT5 is listed. But where would the climatology bounds be stored? This is crucial??? Are
# we happy with hussanom as inputvar and outputvar and specifc_humidity_anomaly as a new standard name?
# For now hussanom is added to the obs4MIPs_Amon.json but this doesn't include climatological bounds though.
# How to store additional info - uncertainty, actual values etc...
          
sys.path.append("../../../misc/")
from fix_dataset_time import make_continuous_bounds # this is in misc/
import obs4MIPsLib # this is in misc/

CMOR_MDI = 1.e20 # I've set this as global variable

#%% User provided input
cmorTable = "../../../../Tables/obs4MIPs_Amon.json" ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'HadISDH.land.4.6.1.2024f.json' ; # Update contents of this file to set your global_attributes
# EDITABLE - where is the input file?
inputFilePathbgn = os.environ['SCRATCH']+'/RANDOM/'
inputFileName = ['huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc', 
                 'huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'huss-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'hurs-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'hurs-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'hurs-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc',
                 'hurs-land_HadISDH_HadOBS_v4-6-1-2024f_19730101-20241231.nc']  
inputVarName = ['huss', 'hussa', 'stncount', 'stdunc', 'hurs', 'hursa', 'stncount', 'stdunc']    # I actually want to provide the anomaly field (hussa) rather than actual values.
outputVarName = ['huss', 'hussanom', 'hussnobs', 'hussustd', 'hurs', 'hursanom', 'hursnobs', 'hursustd']
outputUnits = ['1', '1', '1', '1', '1', '1', '1', '1']    # its g/kg and I convert here to kg/kg, or for RH its %rh.

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
 # convert data depening on what variable it is
 if (outputVarName[fi] == 'huss') or (outputVarName[fi] == 'hussanom'): # original units are g/kg
  d = np.where(d < CMOR_MDI, d / 1000., CMOR_MDI) 
 elif (outputVarName[fi] == 'hussustd'): # original standard uncertainty is k=2 but obs4MIPS wants k=1
  d = np.where(d < CMOR_MDI, (d / 2.) / 1000., CMOR_MDI) 
 elif (outputVarName[fi] == 'hussnobs'): # number of observations - change -1s to CMOR_MDI
  d = np.where(d < 0, CMOR_MDI, d)
 elif (outputVarName[fi] == 'hurs') or (outputVarName[fi] == 'hursanom'): # original units are g/kg
  d = np.where(d < CMOR_MDI, d, CMOR_MDI) 
 elif (outputVarName[fi] == 'hursustd'): # original standard uncertainty is k=2 but obs4MIPS wants k=1
  d = np.where(d < CMOR_MDI, d / 2., CMOR_MDI) 
 elif (outputVarName[fi] == 'hursnobs'): # number of observations - change -1s to CMOR_MDI
  d = np.where(d < 0, CMOR_MDI, d)
 #pdb.set_trace()

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
 #pdb.set_trace()

 ## Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 #cmor.set_variable_attribute(varid,'valid_min','f',np.min(values[values < CMOR_MDI]))
 #cmor.set_variable_attribute(varid,'valid_max','f',np.max(values[values < CMOR_MDI]))

# Set bespoke attributes associated with anomalies
 if outputVarName[fi] == 'hussanom':
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'near-surface (~2m) specific humidity monthly mean anomalies from the 1991-2020 climatological reference period')
  cmor.set_variable_attribute(varid, 'units_metadata', 'c', 'specific humidity: difference')

# set bespoke attributes associated with number of observations
 elif outputVarName[fi] == 'hussnobs':
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'number of stations used in the calculation of gridbox monthly mean near-surface (~2m) specific humidity')

# set bespoke attributes associated with standard uncertainty
 elif outputVarName[fi] == 'hussustd': 
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'standard uncertainty (k=1) in the monthly mean near-surface (~2m) specific humidity from uncertainty in measurement, homogeneity adjustment, climatology and gridbox sampling')

 elif outputVarName[fi] == 'hursanom':
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'near-surface (~2m) relative humidity monthly mean anomalies from the 1991-2020 climatological reference period')
  cmor.set_variable_attribute(varid, 'units_metadata', 'c', 'relative humidity: difference')

# set bespoke attributes associated with number of observations
 elif outputVarName[fi] == 'hursnobs':
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'number of stations used in the calculation of gridbox monthly mean near-surface (~2m) relative humidity')

# set bespoke attributes associated with standard uncertainty
 elif outputVarName[fi] == 'hursustd': 
  cmor.set_variable_attribute(varid, 'long_name', 'c', 'standard uncertainty (k=1) in the monthly mean near-surface (~2m) relative humidity from uncertainty in measurement, homogeneity adjustment, climatology and gridbox sampling')

# Set bespoke variable attributes for HadISDH 
 #cmor.set_variable_attribute(varid, 'cell_methods', 'c', 'time: mean over station month, area: mean over gridbox')

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
 gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
 full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"  
 cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid, values) ; # Write variable with time axis
 f.close() 
 cmor.close()

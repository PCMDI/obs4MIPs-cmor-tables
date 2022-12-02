import cmor
import cdms2 as cdm
import numpy as np
import xcdat as xc
import xarray as xr
import json
#import MV2
#import cdutil
#cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'HadISSTv1.1.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/HadISSTv1.1/'   #xmls/'
#inputFilePathend = '/TMP/'
inputFileName = ['HadISST_sst.nc']   #['HadISST.xml']
inputVarName = ['sst']
outputVarName = ['ts']
outputUnits = ['K']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file

for fi in range(len(inputVarName)):

 inputFilePath = inputFilePathbgn+inputFilePathend
#f = cdm.open(inputFilePath+inputFileName[fi])
 f = xr.open_dataset(inputFilePath+inputFileName[fi],decode_times=False)
#cdm.setAutoBounds('on')
 d = f[inputVarName[fi]] 
 d = d + 273.15
 d = np.ma.masked_where(np.ma.equal(d,-1e+30), d)
 d = np.where(np.less(d,-100.),1.e20,d)

#cdm.setAutoBounds('off')
#cdutil.times.setTimeBoundsMonthly(d)
 lat = f.latitude.values  #f.getLatitude()
 lon = f.longitude.values  #d.getLongitude()
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
 time = f.time.values   #d.getAxis(0) ; # Rather use a file dimension-based load statement

 f = f.bounds.add_bounds("X")  #, width=0.5)
 f = f.bounds.add_bounds("Y")  #, width=0.5)

 f = f.drop_vars(["time_bnds"])
 f = f.bounds.add_bounds("T")

# Deal with problematic "months since" calendar/time axis
#time_bounds = f.time_bnds.values  #getBounds()
#time_bounds[:,0] = time[:]
#time_bounds[:-1,1] = time[1:]
#time_bounds[-1,1] = time_bounds[-1,0]+1
#time.setBounds(time_bounds)
#del(time_bounds) ; # Cleanup

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
 cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
 cmor.dataset_json(inputJson)
 cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
 axes    = [ {'table_entry': 'time',
             'units': f.time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': f.latitude_bnds},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': f.longitude_bnds},
          ]
 axisIds = list() ; # Create list of axes
 for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#d.units = outputUnits[fi]
 varid   = cmor.variable(outputVarName[fi],outputUnits[fi],axisIds,missing_value=1.e20)
 values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#cmor.set_variable_attribute(varid,'valid_min',2.0)
#cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid,values,time_vals=time[:],time_bnds=f.time_bnds.values) ; # Write variable with time axis
 f.close()
 cmor.close()

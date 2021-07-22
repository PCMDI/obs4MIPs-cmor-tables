import cmor
import cdms2 as cdm
import numpy as np
import cdutil
import glob
cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../Tables/PMPObs_A3hr.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'TRMM_3B43v.7-input_3hr.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/TRMM_3hr_ccovey/gpfs/fs1/p/cgd/cas/zhangyx/TRMM.3HRLY/'   # '/TRMM_3B43v.7_mo_03162018/python_rewrite/'
#inputFileName = ['TRMM_3B42.xml']
inputFileName = glob.glob(inputFilePathbgn + inputFilePathend + '/*.nc')

inputVarName = ['precip']
outputVarName = ['pr']
outputUnits = ['kg m-2 s-1']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputFileName)):
  print(fi, inputFileName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
# f = cdm.open(inputFilePath+inputFileName[fi])
  f = cdm.open(inputFileName[fi])
  d = f(inputVarName[0])
  lat = d.getLatitude()
  lon = d.getLongitude()
  print(d.shape)
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
  time = d.getAxis(0) ; # Rather use a file dimension-based load statement

# Deal with problematic "months since" calendar/time axis
  time_bounds = time.getBounds()
  time_bounds[:,0] = time[:] -1.5
  time_bounds[:,1] = time[:] + 1.5 
# time_bounds[-1,1] = time_bounds[-1,0]+1
  time.setBounds(time_bounds) #####time_bounds)
#####del(time_bounds) ; # Cleanup

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units': time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat.getBounds()},
             {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon.getBounds()},
          ]
  axisIds = list() ; # Create list of axes
  for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d.units = outputUnits[0]
  varid   = cmor.variable(outputVarName[0],d.units,axisIds,missing_value=d.missing)
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=time_bounds)  #time.getBounds()) ; # Write variable with time axis
  f.close()

  cmor.close()

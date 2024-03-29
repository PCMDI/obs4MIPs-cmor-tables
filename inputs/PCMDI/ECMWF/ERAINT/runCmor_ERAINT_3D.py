import cmor
import cdms2 as cdm
import numpy as np
import MV2 as mv
import cdutil
cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'ERAINT-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/ERA-INT_10082017/'
inputFileName = ['va_era_interim.nc','ta_era_interim.nc','ua_era_interim.nc','hur_era_interim.nc','hus_era_interim.nc','zg_era_interim.nc']
inputVarName = ['v','t','u','r','q','z']
outputVarName = ['va','ta','ua','hur','hus','zg']
outputUnits = ['m s-1','K','m s-1','%','kg kg**-1','m']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = cdm.open(inputFilePath+inputFileName[fi])
  d1 = f(inputVarName[fi])
  cdutil.times.setTimeBoundsMonthly(d1)
  if inputVarName[fi] in ['z']:
     d1.data[:,:,:,:] = d1.data[:,:,:,:] / 9.8
  plev17 = d1.getAxis(1)  #getLevel()
  lat = d1.getLatitude()
  lon = d1.getLongitude()
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
  time = d1.getAxis(0) ; # Rather use a file dimension-based load statement

# Deal with problematic "months since" calendar/time axis
  time_bounds = time.getBounds()
# time_bounds[:,0] = time[:]
# time_bounds[:-1,1] = time[1:]
# time_bounds[-1,1] = time_bounds[-1,0]+1

# Deal with plev17 to plev19 conversion
  plev17[:] = plev17[:]*100.
  plev19 = np.append(plev17[-1::-1],[500.,100.]) ; # Add missing upper two values
  plev19 = cdm.createAxis(plev19,id='plev')
  plev19.designateLevel()
  plev19.axis = 'Z'
  plev19.long_name = 'pressure'
  plev19.positive = 'down'
  plev19.realtopology = 'linear'
  plev19.standard_name = 'air_pressure'
  plev19.units = 'Pa'

# Pad data array with missing values
  d2 = np.ma.array(np.ma.ones([d1.shape[0],2,d1.shape[2],d1.shape[3]]),mask=True)*1e20
  d11 = d1[:,-1::-1,:,:]
  print(d2.shape,d11.shape)
  d = mv.concatenate((d11,d2),axis=1)

  del(d1,d11,d2,plev17) ; # Cleanup

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units': time.units, # 'days since 1870-01-01',
             },
             {'table_entry': 'plev19',
              'units': 'Pa',
              'coord_vals': plev19[:],
              'cell_bounds': plev19.getBounds()},
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
  d.units = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],d.units,axisIds,missing_value=d.missing)
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#cmor.set_variable_attribute(varid,'valid_min','f',2.0)
#cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
  f.close()
  cmor.close()

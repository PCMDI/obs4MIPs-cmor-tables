import cmor
import cdms2 as cdm
import numpy as np
import MV2 as mv
import cdutil
import cdtime

cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/ERA5-CREATEIP/'

inputFilePathend = ['']
inputFileName = ['ua_ERA5.xml','va_ERA5.xml','ta_ERA5.xml','zg_ERA5.xml']
inputFileName = ['va_ERA5.xml','ta_ERA5.xml','zg_ERA5.xml']

inputVarName = ['ua','va']  #,'ta','zg']
inputVarName = ['ta','zg']
inputVarName = ['va','ta','zg']
 
outputVarName = ['uaplev37_ERA5']
outputVarName = ['vaplev37_ERA5','taplev37_ERA5','zgplev37_ERA5'] 
 
outputUnits = ['m s-1','K','m']


### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
 for i in range(40):
  yr = 1979 + i

  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend[fi]
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = cdm.open(inputFilePath+inputFileName[fi])
# d1 = f(inputVarName[fi], time = (cdtime.comptime(yr,0,),cdtime.comptime(yr,12)),longitude=(6,10),latitude=(6,10))
  d1 = f(inputVarName[fi], time = (cdtime.comptime(yr,0,),cdtime.comptime(yr+1,0)))

  plev1 = d1.getLevel()

  plev1[:] = plev1[:]*1 
  plev1 = cdm.createAxis(plev1,id='plev')
  plev1.designateLevel()
  plev1.axis = 'Z'
  plev1.long_name = 'pressure'
  plev1.positive = 'down'
  plev1.realtopology = 'linear'
  plev1.standard_name = 'air_pressure'
  plev1.units = 'Pa'

  print(plev1[:])

  lat = d1.getLatitude()
  lon = d1.getLongitude()
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
  time = d1.getAxis(0) ; # Rather use a file dimension-based load statement

  

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)

# if inputVarName[fi] == 'z_0001':

  heightAx = {'table_entry': 'plev37_ERA5',
                            'units': 'Pa',
                            'coord_vals': plev1[:]}

  axes    = [ 
              {'table_entry': 'time',
              'units': time.units, # 'days since 1870-01-01',
             },
              heightAx,
              {'table_entry': 'latitude',
              'units': 'degrees_north',
              'coord_vals': lat[:],
              'cell_bounds': lat.getBounds()
              },
              {'table_entry': 'longitude',
              'units': 'degrees_east',
              'coord_vals': lon[:],
              'cell_bounds': lon.getBounds()
              },]


  axisIds = list() ; # Create list of axes
  for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

#pdb.set_trace() ; # Debug statement

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d1.units = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],d1.units,axisIds,missing_value=d1.missing)
  values  = np.array(d1[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#cmor.set_variable_attribute(varid,'valid_min','f',2.0)
#cmor.set_variable_attribute(varid,'valid_max','f',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
  f.close()
  cmor.close()

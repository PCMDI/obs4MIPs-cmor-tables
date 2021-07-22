import cmor
import cdms2 as cdm
import numpy as np
import cdutil
cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../Tables/PMPObs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/ERA5/fromMARS/'

inputFileName = ['adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580171536.0444872-8315-37-02e9201d-5e7b-41b5-98ff-3b9b3a83d82d.nc','adaptor.mars.internal-1580190896.023251-25621-38-f188c480-a5cd-4284-84a7-5757315ca044.nc']
inputVarName = ['t2m_0001','u10_0001','v10_0001','msl_0001'] 
outputVarName = ['tas','uas','vas','psl']  
outputUnits = ['K','m s-1','m s-1','Pa'] 
outpos = ['','','',''] 

'''
inputFileName = ['adaptor.mars.internal-1582240823.3820484-23715-16-fe2f1d48-67a6-479f-9d83-6356ce7cbecb.nc','adaptor.mars.internal-1582240823.3820484-23715-16-fe2f1d48-67a6-479f-9d83-6356ce7cbecb.nc']
inputVarName = ['ewss', 'nsss']
outputVarName = ['tauu','tauv']
outputUnits = ['Pa','Pa']
outpos = ['down','down']
'''

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE..
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = cdm.open(inputFilePath+inputFileName[fi])
  d = f(inputVarName[fi])(squeeze=1)
  lat = d.getLatitude()
  lon = d.getLongitude()
  print(d.shape)
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
  time = d.getAxis(0) ; # Rather use a file dimension-based load statement

  time_bounds = time.getBounds()

  d.positive = outpos[fi]

#####time.setBounds() #####time_bounds)
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


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  d.units = outputUnits[fi]
  varid   = cmor.variable(outputVarName[fi],d.units,axisIds,missing_value=d.missing,positive=d.positive)
  values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  #cmor.set_variable_attribute(varid,'valid_min',2.0)
  #cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
  cmor.write(varid,values,time_vals=time[:],time_bnds=time_bounds) ; # Write variable with time axis
  f.close()

  cmor.close()

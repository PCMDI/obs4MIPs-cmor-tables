import cmor
import cdms2 as cdm
import numpy as np
import MV2 as mv
import cdutil
cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../Tables/PMPObs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'ERA5-MARS-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/ERA5/fromMARS/'
inputFileName = ['adaptor.mars.internal-1580176461.3999553-15526-5-337023bb-5748-4ecb-82cd-756b011747e8.nc','adaptor.mars.internal-1580176461.3999553-15526-5-337023bb-5748-4ecb-82cd-756b011747e8.nc','adaptor.mars.internal-1580176461.3999553-15526-5-337023bb-5748-4ecb-82cd-756b011747e8.nc','adaptor.mars.internal-1580176461.3999553-15526-5-337023bb-5748-4ecb-82cd-756b011747e8.nc']
inputVarName = ['z_0001','u_0001','v_0001','t_0001'] 
outputVarName = ['zgplev3a','uaplev3a','vaplev3a','taplev3a']  
outputUnits = ['m','m s-1','m s-1','K']

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = cdm.open(inputFilePath+inputFileName[fi])
  d1 = f(inputVarName[fi])  #,plev=(1000., 850.))
# cdutil.times.setTimeBoundsMonthly(d1)
  #d11 = d1[:,-1::-1,:,:]
#[100000.,92500.,85000.,70000.,60000.,50000.,40000.,30000.,25000.,20000.,15000.,10000.,7000.,5000.,3000.,2000.,1000.,500.,100.])
  plev1 = d1.getLevel()

  plev1[:] = plev1[:]*100.
  plev1 = cdm.createAxis(plev1,id='plev')
  plev1.designateLevel()
  plev1.axis = 'Z'
  plev1.long_name = 'pressure'
  plev1.positive = 'down'
  plev1.realtopology = 'linear'
  plev1.standard_name = 'air_pressure'
  plev1.units = 'Pa'

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

  heightAx = {'table_entry': 'plev3a',
                            'units': 'Pa',
                            'coord_vals': cdm.createAxis([85000.,50000.,20000.],id='level') }

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

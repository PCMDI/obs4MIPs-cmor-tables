import cmor
import cdms2 as cdm
import numpy as np
import MV2
import cdutil
cdm.setAutoBounds('on') # Caution, this attempts to automatically set coordinate bounds - please check outputs using this option
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = '../Tables/PMPObs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'TropFlux-input.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = 'TropFlux/monthly/xmls/'
inputFileName = ['Tropflux_t2m_mo.xml','Tropflux_sst_mo.xml','Tropflux_netflux_mo.xml','Tropflux_lhf_mo.xml','Tropflux_shf_mo.xml','Tropflux_taux_mo.xml','Tropflux_tauy_mo.xml']
inputVarName = ['t2m','sst','netflux','lhf','shf','taux','tauy']
outputVarName = ['tas','ts','hfns','hfls','hfss','tauu','tauv']
outputUnits = ['K','K','W m-2','W m-2','W m-2','Pa','Pa']
outpos = ['','','up','up','up','down','down']     #,'','up','down','down','up','','','','down','down','']
####['W m-2',"W m-2","Pa",'kg m-2 s-1','W m-2','W m-2','W m-2','W m-2',"m s-1",'m s-1','m s-1','Pa','Pa','K]]


### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
for fi in range(len(inputVarName)):
  print(fi, inputVarName[fi])
  inputFilePath = inputFilePathbgn+inputFilePathend
#%% Process variable (with time axis)
# Open and read input netcdf file
  f = cdm.open(inputFilePath+inputFileName[fi])
  d = f(inputVarName[fi])
  if inputVarName[fi] in ['t2m','sst']: d = MV2.add(d,273.15)
  if inputVarName[fi] in ['hfss','hfls']: d = MV2.multiplty(d,-1.)
# cdutil.times.setTimeBoundsMonthly(d)
  lat = d.getLatitude()
  lon = d.getLongitude()
  print(d.shape)
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
  time = d.getAxis(0) ; # Rather use a file dimension-based load statement

# Deal with problematic "months since" calendar/time axis
  time_bounds = time.getBounds()
  d.positive = outpos[fi]

# time_bounds[:,0] = time[:]
# time_bounds[:-1,1] = time[1:]
# time_bounds[-1,1] = time_bounds[-1,0]+1
#####time.setBounds() #####time_bounds)
#####del(time_bounds) ; # Cleanup

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
  cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
  cmor.dataset_json(inputJson)
  cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
  axes    = [ {'table_entry': 'time',
             'units':'days since 1950-01-01 00:00:00' # 'days since 1979-01-01', #time.units, # 'days since 1870-01-01',
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

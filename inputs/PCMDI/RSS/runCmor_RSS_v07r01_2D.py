import cmor
import cdms2 as cdm
import numpy as np
import MV2
import cdutil
#cdm.setAutoBounds('on') # Caution, this automatically sets coordinate bounds - please check outputs using this option

#%% User provided input
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'RSS_prw_v07r01.json' ; # Update contents of this file to set your global_attributes
inputFilePathbgn = '/p/user_pub/pmp/pmp_obs_preparation/orig/data/'
inputFilePathend = '/RSS_02142019/'
inputFileName = ['tpw_v07r01_198801_201812.nc3.nc','ws_v07r01_198801_201812.nc3.nc']
inputVarName = ['precipitable_water','wind_speed']
outputVarName = ['prw','sfcWind']
outputUnits = ['kg m-2','m s-1']

# Open and read input netcdf file

for fi in range(len(inputVarName)):

 inputFilePath = inputFilePathbgn+inputFilePathend
 f = cdm.open(inputFilePath+inputFileName[fi])
 d = f(inputVarName[fi])
#cdutil.times.setTimeBoundsMonthly(d)
 if inputVarName[fi] == 'wind_speed': 
   d = MV2.where(MV2.less(d,0.),1.e20,d)

 lat = d.getLatitude()
 lon = d.getLongitude()
 time = d.getAxis(0) ; # Rather use a file dimension-based load statement

# Deal with problematic "months since" calendar/time axis
 time_bounds = time.getBounds()

# DATA RETRIVAL README INFO APPENDED TO HISTORY  
R = open('README_RSS_v20190219.txt')
Rhist = ' '
for RR in R.readlines():
 Rhist = Rhist + RR[:-1] + ' ' 

#%% Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
 cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
 cmor.dataset_json(inputJson)
 cmor.load_table(cmorTable)
 cmor.set_cur_dataset_attribute('history',f.history + Rhist) ; # Force input file attribute as history
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
 varid   = cmor.variable(outputVarName[fi],d.units,axisIds,missing_value=d.missing)
 values  = np.array(d[:],np.float32)

# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
#cmor.set_variable_attribute(varid,'valid_min',2.0)
#cmor.set_variable_attribute(varid,'valid_max',3.0)

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
 cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
 cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
 f.close()
 cmor.close()

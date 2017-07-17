import cmor
import cdms2 as cdm
import numpy as np
#import pdb ; # Debug statement - import if enabling below

#%% User provided input
cmorTable = 'Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'rssSsmiPrw-input.json' ; # Update contents of this file to set your global_attributes
inputDataPath = 'rss_ssmi_prw_v06.6-demo.nc'
inputVarName = 'prw'
outputVarName = 'prw'
outputUnits = 'kg m-2'

### BETTER IF THE USER DOES NOT CHANGE ANYTHING BELOW THIS LINE...
#%% Process variable (with time axis)
# Open and read input netcdf file
f = cdm.open(inputDataPath)
d = f(inputVarName)
lat = d.getLatitude()
lon = d.getLongitude()
#time = d.getTime() ; # Assumes variable is named 'time', for the demo file this is named 'months'
time = d.getAxis(0)

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

d.units = outputUnits
varid   = cmor.variable(outputVarName,d.units,axisIds,missing_value=d.missing)
values  = np.array(d[:],np.float32)
cdm.setAutoBounds('on') # PJG - Caution, this attempts to automatically set coordinate bounds - please check outputs using this option

cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,values,time_vals=time[:],time_bnds=time.getBounds()) ; # Write variable with time axis
f.close()
cmor.close()
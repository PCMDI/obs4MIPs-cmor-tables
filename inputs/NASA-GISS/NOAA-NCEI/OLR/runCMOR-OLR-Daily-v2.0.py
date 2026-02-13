
import cmor
import xcdat as xc
import numpy as np
import glob
import sys
import cftime
import os

sys.path.append("../../../../inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Aday.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'OLR-v2.0.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/NOAA-NCEI/OLR/OLR-Daily_v02r00/' # change to local path on user's machine where files are stored
inputVarName = 'olr'
outputVarName = 'rlut'
outputUnits = 'W m-2'
outpos = 'up'
cmor_missing = np.float32(1.0e20)

for year in range(1979, 2025):  # put the years you want to process here
        # Opening file from the dataset for a specific year 
        inputFileName = f"OLR-Daily_v02r00_s{year}0101_e{year}1231.nc"
        f = xc.open_mfdataset(inputFilePath+inputFileName, mask_and_scale=False, decode_times=False, decode_cf=False)
        d = f[inputVarName]
        
        time = f.time
        lat = f.lat
        lon = f.lon
        
        lat_bounds = f.lat_bounds
        lon_bounds = f.lon_bounds
        time_bounds = f.time_bounds

        #%% Initialize and run CMOR
        # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
        cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
        cmor.dataset_json(inputJson)
        cmor.load_table(cmorTable)
        cmor.set_cur_dataset_attribute('history',f.history)
        axes    = [ {'table_entry': 'time',
                     'units': time.units,
                     },
                     {'table_entry': 'latitude',
                      'units': 'degrees_north',
                      'coord_vals': lat.values,
                      'cell_bounds': lat_bounds.values},
                     {'table_entry': 'longitude',
                      'units': 'degrees_east',
                      'coord_vals': lon.values,
                      'cell_bounds': lon_bounds.values},
                  ]
        
        axisIds = list() ; # Create list of axes
        for axis in axes:
            axisId = cmor.axis(**axis)
            axisIds.append(axisId)
        
        # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=cmor_missing,positive=outpos)
        values  = np.array(d.values,np.float32)
        fill = getattr(d, "_FillValue", None) 
        mask = ~np.isfinite(values) | (values == fill) 
        values = np.where(mask, cmor_missing, values)
        
        # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_variable_attribute(varid,'valid_min','f',float(d.valid_min))
        cmor.set_variable_attribute(varid,'valid_max','f',float(d.valid_max))
        
        # Provenance info
        git_commit_number = obs4MIPsLib.get_git_revision_hash()
        path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
        full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code.lstrip('/')}"
        cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")
        
        # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
        cmor.write(varid,values,time_vals=time.values,time_bnds=time_bounds.values) ; # Write variable with time axis
        f.close()
        cmor.close()

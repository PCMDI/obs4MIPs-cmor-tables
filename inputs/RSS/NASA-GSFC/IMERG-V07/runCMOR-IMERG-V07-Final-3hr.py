
import cmor
import xcdat as xc
import numpy as np
import glob
import datetime
import calendar
from make_IMERG_3hr import avg_3hr_imerg
import sys
import os

sys.path.append("/home/manaster1/obs4MIPs-cmor-tables/inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_A3hr.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'IMERG-V07-Final-3hr.json' ; # Update contents of this file to set your global_attributes
# inputDir = '/mnt/sagan/g/ACCESS/output_files/_temp/imerg/12/' # change to local path on user's machine where files are stored.
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/NASA-GSFC/IMERGV07/half-hourly/'
inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

files_list = sorted(glob.glob(os.path.join(inputFilePath,f'*.HDF5')))
for year in range(2000, 2024):  # put the years you want to process here
    inputDatasets = []
    for month in range(1,13):

        # Must make sure the day before and the day after a given month exist otherwise the 3-hourly averaging code will break
        previous_date = datetime.datetime(year,month,1) - datetime.timedelta(days=1)
        previous_year = previous_date.year
        previous_month = previous_date.month
        previous_day = previous_date.day

        res = calendar.monthrange(year, month)
        last_day = res[1]

        future_date = datetime.datetime(year,month,last_day) + datetime.timedelta(days=1)
        future_year = future_date.year
        future_month = future_date.month
        future_day = future_date.day

        yyyymmdd_prev = f"{previous_year}{str(previous_month).zfill(2)}{str(previous_day).zfill(2)}"
        yyyymmdd_futr = f"{future_year}{str(future_month).zfill(2)}{str(future_day).zfill(2)}"

        
        valid_files_prev = [file for file in files_list if yyyymmdd_prev in file]
        valid_files_futr = [file for file in files_list if yyyymmdd_futr in file]

        if valid_files_prev == []:
            print(f"No files for {previous_year}-{str(previous_month).zfill(2)}-{str(previous_day).zfill(2)}. Averaging unavailable")
            continue
        elif valid_files_futr == []:
            print(f"No files for {future_year}-{str(future_month).zfill(2)}-{str(future_day).zfill(2)}. Averaging unavailable")
            continue
        
        print(f'Starting averaging for {year}-{month:02}')
        # Function to average IMERG data to 3-hourly maps.  'ext' is the file extension.  This code will
        # work for 'RT-H5', 'HDF5'/'H5', 'nc', and 'nc4' file extensions.  'RT-H5' for the sake of this demo.
        # inputDataset = avg_3hr_imerg(inputDir, start_year, end_year, start_month, end_month, ext='HDF5')
        inputDataset = avg_3hr_imerg(inputFilePath, year, year, month, month, ext='HDF5', ver='7')

        inputDataset = inputDataset.bounds.add_missing_bounds(axes=["X","Y"])
        inputDataset = inputDataset.bounds.add_bounds("T")

        d = inputDataset[inputVarName]

        time = inputDataset.time
        time_bounds = inputDataset.time_bnds

        # The following lines are written to address floating point representation errors within the IMERG lat/lon data
        lat = ['{:g}'.format(float('{:.4g}'.format(i))) for i in inputDataset.lat.values]
        lon = ['{:g}'.format(float('{:.5g}'.format(i))) for i in inputDataset.lon.values]
        lat_bounds = ['{:g}'.format(float('{:.4g}'.format(i))) for i in np.ravel(inputDataset.lat_bnds.values)]
        lon_bounds = ['{:g}'.format(float('{:.5g}'.format(i))) for i in np.ravel(inputDataset.lon_bnds.values)]
        
        lat = np.asarray(lat,dtype=float)
        lon = np.asarray(lon,dtype=float)
        lat_bounds = np.reshape(np.asarray(lat_bounds,dtype=float), (1800,2))
        lon_bounds = np.reshape(np.asarray(lon_bounds,dtype=float), (3600,2))

        lat_bounds[(lat_bounds > -0.1) & (lat_bounds < 0.1)] = 0.0
        lon_bounds[(lon_bounds > -0.1) & (lon_bounds < 0.1)] = 0.0


        #%% Initialize and run CMOR
        # For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
        cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
        cmor.dataset_json(inputJson)
        cmor.load_table(cmorTable)

        axes    = [ {'table_entry': 'time',
                    'units': time.units,
                    },
                    {'table_entry': 'latitude',
                    'units': 'degrees_north',
                    'coord_vals': lat[:],
                    'cell_bounds': lat_bounds},
                    {'table_entry': 'longitude',
                    'units': 'degrees_east',
                    'coord_vals': lon[:],
                    'cell_bounds': lon_bounds},
                ]

        axisIds = list() ; # Create list of axes
        for axis in axes:
            axisId = cmor.axis(**axis)
            axisIds.append(axisId)

        # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        d["units"] = outputUnits
        varid   = cmor.variable(outputVarName,str(d.units.values),axisIds,missing_value=d._FillValue)
        pr_array = np.array(d[:],np.float32)
        pr_array[pr_array != d._FillValue] /= 3600. #  IMERG data are in units of mm/hr. Converting to kg m-2 s-1 (assuming density of water=1000 kg/m^3) and keeping missing values
        values = pr_array
        
        # Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_variable_attribute(varid,'valid_min','f',0.0)
        cmor.set_variable_attribute(varid,'valid_max','f',100.0/3600.) # setting these manually for the time being.

        # Provenance info 
        gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))

        paths = os.getcwd().split('/inputs')
        path_to_code = f"/inputs{paths[1]}"  # location of the code in the obs4MIPs GitHub directory

        full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/{path_to_code}"
        cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")


        # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
        cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
        cmor.write(varid,values,time_vals=time.values[:],time_bnds=time_bounds.values[:]) ; # Write variable with time axis
        inputDataset.close()
        cmor.close()

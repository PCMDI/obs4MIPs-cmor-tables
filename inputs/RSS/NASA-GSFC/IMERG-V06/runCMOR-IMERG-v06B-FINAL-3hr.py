
import cmor
import xcdat as xc
import numpy as np
import glob
from make_IMERG_3hr import avg_3hr_imerg
import sys
import os

sys.path.append("/home/manaster1/obs4MIPs-cmor-tables/inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'IMERG-v06B-FINAL-3hr.json' ; # Update contents of this file to set your global_attributes
# inputDir = '/mnt/sagan/g/ACCESS/output_files/_temp/imerg/12/' # change to local path on user's machine where files are stored.
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/NASA-GSFC/IMERG6/half-hourly/'
inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'


for year in range(2001, 2002):  # put the years you want to process here
    inputDatasets = []
    for month in range(1,2):


        print(f'Starting averaging for {year}-{month:02}')
        # Function to average IMERG data to 3-hourly maps.  'ext' is the file extension.  This code will
        # work for 'RT-H5', 'HDF5'/'H5', 'nc', and 'nc4' file extensions.  'RT-H5' for the sake of this demo.
        # inputDataset = avg_3hr_imerg(inputDir, start_year, end_year, start_month, end_month, ext='HDF5')
        inputDataset = avg_3hr_imerg(inputFilePath, year, year, month, month, ext='HDF5')

        inputDataset = inputDataset.bounds.add_missing_bounds(axes=["X","Y"])
        inputDataset = inputDataset.bounds.add_bounds("T")

        d = inputDataset[inputVarName]
        time = inputDataset.time
        lat = inputDataset.lat.values
        lon = inputDataset.lon.values

        # Due to CMOR warnings related to the way latitudes and longitudes are read in/rounded
        # need to round lat and lon bounds to 3 places after the decimal
        lat_bounds = np.around(inputDataset.lat_bnds, 3)
        lon_bounds = np.around(inputDataset.lon_bnds, 3)
        time_bounds = inputDataset.time_bnds


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
        values  = np.array(d[:],np.float32)/3600. # IMERG data are in units of mm/hr. Converting to kg m-2 s-1 assuming density of water=1000 kg/m^3

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
        sys.exit()

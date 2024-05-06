
import cmor
import xcdat as xc
import numpy as np
import glob
import sys
import os

sys.path.append("/home/manaster1/obs4MIPs-cmor-tables/inputs/misc/") # Path to obs4MIPsLib

import obs4MIPsLib

def extract_date(ds):   # preprocessing function when opening files
    print(f"Extracting time for: {ds.encoding['source']}")
    for var in ds.variables:
        if var == 'time':
            dataset_time = ds[var].values
            dataset_units = ds[var].units
            ds.assign(time=dataset_time)
            ds["time"].attrs = {"units": dataset_units}
    return ds

#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
inputJson = 'IMERG-V07-Final.json' ; # Update contents of this file to set your global_attributes
inputFilePath = '/p/user_pub/PCMDIobs/obs4MIPs_input/NASA-GSFC/IMERGV07/half-hourly/'
inputVarName = 'precipitation'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

for year in range(2000, 2024):  # put the years you want to process here
    inputDatasets = []
    for month in range(1,13):
        inputFiles = glob.glob(f"{inputFilePath}/3B-HHR.MS.MRG.3IMERG.{year}{month:02}*.HDF5")
        inputFiles.sort() # to ensure data files are in chronological order. Code will break otherwise
        for inputFile in inputFiles:
            inputDatasets.append(inputFile)

        print(inputDatasets)
        print(f'Datasets gathered for {year}-{month:02}')

        # Opening and concatenating files from the dataset
        f = xc.open_mfdataset(inputDatasets, group='Grid', mask_and_scale=False, decode_times=False, combine='nested', concat_dim='time', preprocess=extract_date)
        
        print(f'Datasets concatenated for {year}-{month:02}')

        d = f[inputVarName]
        d = d.transpose('time','lat','lon') # need to transpose the IMEG latitudes and longitudes

        time = f.time
        time_bounds = f.time_bnds

        # The following lines are written to address floating point representation errors within the IMERG lat/lon data
        lat = ['{:g}'.format(float('{:.4g}'.format(i))) for i in f.lat.values]
        lon = ['{:g}'.format(float('{:.5g}'.format(i))) for i in f.lon.values]
        lat_bounds = ['{:g}'.format(float('{:.4g}'.format(i))) for i in np.ravel(f.lat_bnds.values)]
        lon_bounds = ['{:g}'.format(float('{:.5g}'.format(i))) for i in np.ravel(f.lon_bnds.values)]
        
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
        # cmor.set_cur_dataset_attribute('history',f.history) # commented.  Does not appear that there is a 'history' attribute for the read-in files
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
        f.close()
        cmor.close()
        print(f"File written for {year}-{month:02}")

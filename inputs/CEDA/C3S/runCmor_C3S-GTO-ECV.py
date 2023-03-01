#Test file to convert C3S ozone to obs4mips format

import xarray as xr
import xcdat
import numpy as np
import datetime,cftime
import cmor
import glob

#inputs  (initially just start with a single file)
input_dir = 'files_for_obs4mips_v9/'
input_path = input_dir+'*'

#get filelist
filelist = glob.glob(input_path)

######
#Time information is only present as attributes in the files, so first need to get the time information
i=0
for input_file in filelist:
  print('Processing:',input_file)

  #######
  #Read in the data - need to get time from each so reading separately.
  ds_i = xcdat.open_dataset(input_file,decode_times=False,decode_cf=True)   #this adds the bounds too?  does it need a later verison of xcdat?

  #get the time coordinate from the attributes  y
  start_time = ds_i.attrs['time_coverage_start'] 
  end_time = ds_i.attrs['time_coverage_end']

  #convert to datetime object
  stime=datetime.datetime.strptime(start_time,"%Y%m%d")
    #make sure starts at the start of the month
  if stime.day !=1:
    stime=stime.replace(day=1)

  etime=datetime.datetime.strptime(end_time,"%Y%m%d")  
  #input is last day of the month (or shorter if days missing) - adjust to start of next day to get continuous time bounds.  Also extend to be complete month
  if etime.month < 12:
    etime=datetime.datetime(etime.year,etime.month+1,1,0,0) 
  else:
    etime=datetime.datetime(etime.year+1,1,1)

  time_bnds_i=[cftime.date2num(stime,'days since 1970-01-01'),cftime.date2num(etime,'days since 1970-01-01')]
  time_i=cftime.date2num(stime,'days since 1970-01-01')  

  if i == 0:
    time=np.array(time_i,dtype=int)
    time_bnds=np.array([time_bnds_i],dtype=int)
  else:
    time=np.append(time,time_i)
    time_bnds=np.append(time_bnds,[time_bnds_i],axis=0)

  i=1


#---------------------------
#determine other axis values
latitude_units = ds_i['latitude'].units
latitude_values = ds_i['latitude'].values
latitude_bounds = ds_i['latitude_bnds'].values

longitude_units = ds_i['longitude'].units
longitude_values = ds_i['longitude'].values
longitude_bounds = ds_i['longitude_bnds'].values

#-------------------
#set up CMOR inputs to convert to obs4mips format

#User provided input
cmorTable = '../cmor/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json' #ozone toc variable in AMON table
inputJson = 'ozone/cci_ozone_input.json' # File to set global attributes
#inputFilePath = 'rss_ssmi_prw_v06.6-demo.nc'
inputVarName = 'total_ozone_column'
outputVarName = 'toz'
outputUnits = 'm'

# Initialize and run CMOR
# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='../cmor/obs4MIPs-cmor-tables/Tables/',netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)
#cmor.set_cur_dataset_attribute('history',f.history) ; # Force input file attribute as history
axes    = [ {'table_entry': 'time',
             'units': 'days since 1970-01-01', 
             },
             {'table_entry': 'latitude',
              'units': latitude_units,
              'coord_vals': latitude_values,
              'cell_bounds': latitude_bounds},
             {'table_entry': 'longitude',
              'units': longitude_units,
              'coord_vals': longitude_values,
              'cell_bounds': longitude_bounds},
            ]       
axisIds = list() ; # Create list of axes
for axis in axes:
    axisId = cmor.axis(**axis)
    axisIds.append(axisId)

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
missing = np.nan   
varid   = cmor.variable(outputVarName,outputUnits,axisIds,missing_value=missing)

#prepare variable for writing
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data

#------------------------
#loop over data to read in
i=0
for input_file in filelist:
  ds = xcdat.open_dataset(input_file)
  
  #extract ozone variable
  values  = np.single(ds['total_ozone_column'].values)*2241.399/1e5

# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
  cmor.write(varid,values,time_vals=time[i],time_bnds=time_bnds[i,:]) ; # Write variable with time axis

  ds.close()
  i+=1
#----------
#close file
cmor.close()
###
#!/usr/bin/env python
# coding: utf-8

# ### Notebook to test the new demo file for zonal mean datasets. 

# This is a test for obs4mIPs proposal #49 'Mole Fraction of O3-satellite(merged). The original dataset can be found here

# In[1]:


# CMOR demo https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/demo/demo-zonalmeans/runCMORdemo_zonalmean.py
# Test notebook to sese if the demo file can be processed on Mac offline using Jupyter environ.
# Input file pths, .jsons and tables defined for local machine

# import common libraries 

import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

#sys.path.append("/Users/paul.smith/obs4MIPs-cmor-tables/inputs/misc") # Path to obs4MIPsLib used to trap provenance
sys.path.append("../../../inputs/misc") # Path to obs4MIPsLib used to trap provenance

import obs4MIPsLib

#cmorTable = '/Users/paul.smith/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
#inputJson = '/Users/paul.smith/obs4MIPs-cmor-tables/demo/demo-zonalmeans/zonalmean-demo_input.json' ; # Update contents of this file to set your global_attributes
#inputFilePath = '/Users/paul.smith/obs4MIPs-cmor-tables/demo/demo-zonalmeans/BSVerticalOzone_MR_GPH_Tier1.3_v1.0.nc'
cmorTable = '../../../Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr - Load target table, axis info (coordinates, grid*) and CVs
#inputJson = '../../../demo/demo-zonalmeans/zonalmean-demo_input.json' ; # Update contents of this file to set your global_attributes
inputJson = './SAGE-CCI-OMPS_input.json'
#inputFilePath = '../../../demo/demo-zonalmeans/BSVerticalOzone_MR_GPH_Tier1.3_v1.0.nc'
inputFilePath = './OBS6_ESACCI-OZONE_sat_L3_AERmon_o3_198410-202212.nc'

inputVarName = 'o3'
outputVarName = 'o3zm'
outputUnits = 'mol mol-1'


# In[2]:


# Open and read input netcdf file, get coordinates and add bounds
f = xc.open_dataset(inputFilePath,decode_times=False)
d = f[inputVarName]
lat = f.lat.values
lev = f.alt16.values
time = f.time.values  
#f = f.bounds.add_missing_bounds(axes=['Y'])
f = f.bounds.add_bounds("T")
tbds = f.time_bnds.values

d = np.where(np.isnan(d),1.e20,d)


# In[3]:


# Initialize and run CMOR. For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
cmor.dataset_json(inputJson)
cmor.load_table(cmorTable)


# In[4]:


# Create CMOR axes
cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
cmorLev = cmor.axis("height", coord_vals=lev[:]*1000., units="m")
cmorTime = cmor.axis("time", coord_vals=time[:], cell_bounds=tbds, units= f.time.units)
cmoraxes = [cmorTime,cmorLev,cmorLat]


# In[5]:


# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
values  = np.array(d,np.float32)[:]


# In[6]:


# Append valid_min and valid_max to variable before writing using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_variable_attribute(varid,'valid_min','f',2.0)
cmor.set_variable_attribute(varid,'valid_max','f',3.0)


# In[7]:


# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 
gitinfo = obs4MIPsLib.ProvenanceInfo(obs4MIPsLib.getGitInfo("./"))
full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{gitinfo['commit_number']}/demo"  
cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")


# In[8]:


# Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
cmor.write(varid,d)  #,len(time)) 
cmor.close()
f.close()


# In[ ]:





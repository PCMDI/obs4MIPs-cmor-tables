# This script shows how the ESA CCI Cloud dataset, pre-prepared by ESMValTool, was CMOR-ized for obs4MIPs publication.

# Please note, ESMValTool has combined the CCI Cloud AVHRR AM and PM products and created a CMOR-like dataset here, which we use to 
# fully CMOR-ize the dataset: https://github.com/ESMValGroup/ESMValTool/blob/main/esmvaltool/cmorizers/data/formatters/datasets/esacci_cloud.ncl

# Importing necessary libraries
import cmor
import xarray as xr
import xcdat as xc
import numpy as np
import json
import sys,os

# User0provided input (CMOR table, input file, variable_id and input_json file)
cmorTable = '/root/Obs4MIPs_demo/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json' ; # Aday,Amon,Lmon,Omon,SImon,fx
inputVarName = 'clt'
inputJson = '/root/Obs4MIPs_demo/obs4MIPs-cmor-tables/inputs/ESMValTool/ESACCI-CLD_input.json'
inputFilePathbgn = '/root/Obs4MIPs_demo/data/OBS_ESACCI-CLOUD_sat_AVHRR-AMPM-fv3.0_Amon_clt_198201-201612.nc'


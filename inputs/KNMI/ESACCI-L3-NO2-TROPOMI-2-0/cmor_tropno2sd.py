#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 26 16:20:03 2026

@author: anglou
"""

import numpy as np
import cmor
import xarray as xr
import datetime
import sys
import os

dataset='02x02'

# Open dataset 

ds = xr.open_dataset(f'/nobackup/users/anglou/data/obs4MIPs/TROPOMI/{dataset}/ESACCI-L3-NO2-TROPOMI-2-0_201805-202311.nc', decode_times=False)

# Set up CMOR

cmor.setup(
    inpath="/usr/people/anglou/Obs4MIPs/obs4mips_repo/obs4MIPs-cmor-tables/Tables/",
    netcdf_file_action=cmor.CMOR_REPLACE_4,
    # logfile=f"/usr/people/anglou/Obs4MIPs/NO2/logs/cmor_tropno2sd_{datetime.datetime.now().strftime('%Y%m%dT%H%M')}.log",
)

#Read dataset json 

cmor.dataset_json("tropno2sd.json")

#Read relevant obs4MIPs table

table = os.path.abspath('/usr/people/anglou/Obs4MIPs/obs4mips_repo/obs4MIPs-cmor-tables/Tables/obs4MIPs_Amon.json')
table_id = cmor.load_table(table)
cmor.set_table(table_id)

#Set up coordinates

lat_id = cmor.axis(
    table_entry="latitude",
    units="degrees_north",
    coord_vals=ds.lat.values,
    cell_bounds=ds.lat_bnds.values,
)

lon_id = cmor.axis(
    table_entry="longitude",
    units="degrees_east",   
    coord_vals=ds.lon.values,
    cell_bounds=ds.lon_bnds.values,
)

time_id = cmor.axis(
    table_entry="time",
    units= ds["time"].attrs["units"], # "days since 1995-01-01 00:00:00", #ds.time["units"],
    # calendar= ds["time"].attrs["calendar"],
    coord_vals=ds.time.values,
    cell_bounds=ds.time_bnds.values,
)

# Read variable

var_sd = cmor.variable(
    table_entry="tropno2sd",
    axis_ids=[lon_id, lat_id, time_id],
    units="molecules cm^-2",
    comment="Temporal standrad deviation of tropno2.",
    data_type='d',
)
missing_value = 1e20

ds["tropno2sd"] = ds["tropno2sd"].fillna(missing_value)

# Provenance info - produces global attribute <obs4MIPs_GH_Commit_ID> 

sys.path.append("../../misc") # Path to obs4MIPsLib used to trap provenance
import obs4MIPsLib

git_commit_number = obs4MIPsLib.get_git_revision_hash()
path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code}"
cmor.set_cur_dataset_attribute("processing_code_location",f"{full_git_path}")

#Make file

cmor.write(var_sd,ds["tropno2sd"].values.astype('float64'))
cmor.close()
import os, sys
import json
import xcdat as xc
import xarray as xr
import numpy as np
import glob

vars_list = ['pr']
fqs_list = ['day']  # 'monthly','day']

for var in vars_list:
    for fq in fqs_list:
        
        pathin_template = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_' + fq + '_byVar_catalogue_v????????.json'
        pathin = sorted(glob.glob(pathin_template))[-1]  # select the latest catalogue file

        print('\nvar, fq, catalogue:', var, fq, pathin.split('/')[-1])

        ddic = json.load(open(pathin))
        srcs = sorted(list(ddic[var].keys()))
        
        print('\nSource'.ljust(20), '\t', 'Mean @ t=0'.ljust(10), '\t','Min'.ljust(10),'\t','Max'.ljust(10),'\t', 'Units'.ljust(10),'\t')  #, 'missing_value'.ljust(10),'\t', 'FillValue'.ljust(10))
        print('----------------', '\t', '------------', '\t', '----------','\t', '------------', '\t', '----------','\t', '------------', '\t', '----------')

#       srcs = ['livneh-1-0'] 
        for src in srcs:
            if 'default' not in src and 'alternate' not in src:  # exclude 'default' or 'alternate?' keys
                template = '/p/user_pub/PCMDIobs/' + ddic[var][src]['template']
                ds = xc.open_mfdataset(
                    template,
                    mask_and_scale=True,
                    decode_times=False,
                    decode_cf=True,
                    combine='nested',
                    concat_dim='time',
                    data_vars='all')
#               ds = xc.open_dataset(
#                   template,
#                   mask_and_scale=True,
#                   decode_times=False,
#                   decode_cf=False)
                # get spatial mean of the first time step
                ds_avg = float(ds.isel(time=3).spatial.average(var)[var])
                ds_max = ds.isel(time=0)[var].max().values
                ds_min = ds.isel(time=0)[var].min().values
                # print on screen 
                print(src.ljust(20), '\t', '{:.10f}'.format(ds_avg),'\t','{:.10f}'.format(ds_min),'\t','{:.10f}'.format(ds_max), '\t', ds[var].units.ljust(10),'\t')  #,ds[var].attrs['missing_value'],'\t','\t', ds[var].attrs['_FillValue'])
#               w = sys.stdin.readline()
                ds.close()

      

print('\n')

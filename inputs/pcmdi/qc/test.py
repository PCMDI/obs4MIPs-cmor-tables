import os, sys
import json
import xcdat as xc
import numpy as np

var = 'pr'
fq = 'day' # "monthly"


pathin = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_' + fq + '_byVar_catalogue_v20230530.json'
ddic = json.load(open(pathin))
srcs = ddic[var].keys()

for src in srcs:
  template = '/p/user_pub/PCMDIobs/' + ddic['pr'][src]['template']
# f = xc.open_dataset(template, decode_times=False, decode_cf=False)
  f= xc.open_mfdataset(template, mask_and_scale=True, decode_times=False, combine='nested', concat_dim='time', data_vars='all')
  d = f[var] 
# d0 = d[0]
# ga = np.average(d0)
  ga = d.isel(time=0).spatial.average(data_var = var)

  print(src,'  ', ga) 


# w = sys.stdin.readline()

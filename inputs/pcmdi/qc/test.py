import os, sys
import json
import xcdat as xc


var = 'pr'
fq = 'day' # "monthly"


pathin = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_' + fq + '_byVar_catalogue_v20230530.json'
ddic = json.load(open(pathin))
srcs = ddic[var].keys()

for src in srcs:
  print(src)
  template = '/p/user_pub/PCMDIobs/' + ddic['pr'][src]['template']
  f = xc.open_dataset(template, decode_times=False, decode_cf=False)
  d = f[var] 
  d0 = d[0]
  ds_global_avg = d0.spatial.average(var)



  w = sys.stdin.readline()

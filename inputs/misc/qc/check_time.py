from pcmdi_metrics.utils import check_monthly_time_axis
import json, sys
import xcdat as xc

pin = '/p/user_pub/PCMDIobs/'
cat = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_monthly_byVar_catalogue_v20240716.json'
f = open(cat)
dic = json.load(f)
vars = dic.keys()

for v in vars:
#print(dic[v])
 srcs = dic[v].keys() 

 for src in srcs:
#  print(v,' ',src,' ',dic[v][src]['template'])
   pth = pin + dic[v][src]['template']

   if pth.find('*') != -1: fc = xc.open_mfdataset(pth)
   if pth.find('*') == -1: fc = xc.open_dataset(pth)

   try:
    print('problem with ',v,' ', src,' ', dic[v][src]['template'])
    check_monthly_time_axis(fc)
   except:
    pass

   fc.close()


print('done!')

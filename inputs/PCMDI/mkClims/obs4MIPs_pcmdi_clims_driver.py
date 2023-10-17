import glob
import xcdat as xc
import os

ver = 'v20230109'
lstt = '/p/user_pub/PCMDIobs/obs4MIPs/*/*/mon/*/gn/' + ver 

lst = glob.glob(lstt + '/*.nc')

print(len(lst))
for l in lst:
 print(l)

f_time_series = lst[0]
f_clim = f_time_series.replace('/mon/','/Cmon/')
print(f_clim)
base_path = f_clim.split('/Cmon/')[0] + '/Cmon'

print(base_path) 

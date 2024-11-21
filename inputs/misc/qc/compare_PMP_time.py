import xcdat as xc
import sys

#pathin = '/p/user_pub/PCMDIobs/obs4MIPs/NOAA-ESRL-PSD/CMAP-V1902/mon/pr/gn/v20230612/pr_mon_CMAP-V1902_PCMDI_gn_197901-202210.nc'

pathin = sys.argv[1] 

ds = xc.open_dataset(pathin)

for t in ds.time.values[0:10]:
 print(t)



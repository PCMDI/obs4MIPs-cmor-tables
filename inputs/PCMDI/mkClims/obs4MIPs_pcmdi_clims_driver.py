import glob
import xcdat as xc
import os, sys
import datetime

ver_out = datetime.datetime.now().strftime('v%Y%m%d')

ver = 'v20230109'
#ver = 'latest'

pin = '/p/user_pub/PCMDIobs/obs4MIPs/*/ERA-5/mon/ta/*/' + ver 

pin = '/p/user_pub/PCMDIobs/obs4MIPs/NASA-LaRC/CERES-EBAF-4-1/mon/rlut/gn/' + ver 

lstt = glob.glob(pin + '/*.nc')

lst = []
for l in lstt:
  pd = os.path.dirname(l)
  nf = glob.glob(pd + '/*.nc')
  nfiles = len(nf)
  if pd not in lst and nfiles ==1: lst.append(l)

print('number of files ',len(lst))
#w = sys.stdin.readline()

for infile in lst:
#  infile = os.path.realpath(infile) 
   var = infile.split('/')[8]
   tmp = infile.replace('/obs4MIPs/','/obs4MIPs_tmp/') 
   outfile = tmp
   outfile = outfile.replace(ver,ver_out)
#  print(outfile)
   cmd = 'pcmdi_compute_climatologies.py -p test_obs_param.py --infile ' + infile + ' --outfile ' + outfile + ' --vars ' + var
   os.popen(cmd).readlines()
   print(cmd)

# obs4MIPs/REMSS-PRW-v07r01/mon/sfcWind/100km/climatology/v20230520
# sfcWind-tclm-h010-hxy-x_mon_REMSS-PRW-v07r01_PCMDI_gn_20001-202212.nc

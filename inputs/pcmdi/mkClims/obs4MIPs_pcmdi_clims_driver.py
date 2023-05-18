import glob
import xcdat as xc
import os, sys
import datetime

ver_out = datetime.datetime.now().strftime('v%Y%m%d')

ver = 'v20230109'
ver = 'latest'

pin = '/p/user_pub/PCMDIobs/obs4MIPs/*/ERA-5/mon/ta/*/' + ver 

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
   tmp = infile.replace('/mon/','/monC/') 
   outfile = tmp.replace('_mon_','_monC_')
   outfile = outfile.replace(ver,ver_out)
#  print(outfile)
   cmd = 'pcmdi_compute_climatologies.py -p test_obs_param.py --infile ' + infile + ' --outfile ' + outfile + ' --vars ' + var
   os.popen(cmd).readlines()
   print(cmd)

import os, glob
import time

# GENERATES A SYMBOLIC LINK TO THE LATEST VERSION OF DATASET 

## TIME SERIES
pin = '/p/user_pub/PCMDIobs/obs4MIPs/'
lst = glob.glob(pin + '*/*/*/*/*/')

### CLIMS
#pin = '/p/user_pub/PCMDIobs/obs4MIPs_clims/'
#lst = glob.glob(pin + '*/*/')


for l in lst:
   pthi = os.path.dirname(l)
   vers = os.listdir(pthi)
#   latest = sorted(vers)[-1]
   os.chdir(pthi)
   print(pthi,' ', vers)
   for ver in vers:
     dirt = pthi + '/' + ver 
#    print(dirt)
     empty = os.listdir(dirt)
     if len(empty) == 0:
      print(dirt, ' ------------------ IS EMPTY')
      cmd = 'rm -rf ' + dirt 
      try:
       os.popen(cmd).readlines()
      except:
       pass
      time.sleep(0.01)

#    if len(empty) != 0:
#     print(dirt, 'OCCUPIED')


import os, glob
import time

# GENERATES A SYMBOLIC LINK TO THE LATEST VERSION OF DATASET 

## TIME SERIES
pin = '/p/user_pub/PCMDIobs/obs4MIPs/'
#lst = glob.glob(pin + '*/*/*/*/*/')
lst = glob.glob(pin + '*/*/day/*/*/')


### CLIMS
#pin = '/p/user_pub/PCMDIobs/obs4MIPs_clims/'
#lst = glob.glob(pin + '*/*/')


for l in lst:
   pthi = os.path.dirname(l)
   vers = os.listdir(pthi)
   latest = sorted(vers)[-1]
   print(pthi,'   ', vers,'   ', latest)

   os.chdir(pthi)

   try:
    cmd0 = 'rm latest'
    os.popen(cmd0).readlines() 
    time.sleep(0.01)
   except:
    pass

   cmd = 'ln -s ' + latest + ' ' 'latest' 
   print(cmd)
   os.popen(cmd).readlines() 
   time.sleep(0.01)



import os, glob
import time

# GENERATES A SYMBOLIC LINK TO THE LATEST VERSION OF DATASET 

pin = '/p/user_pub/PCMDIobs/PCMDIobs2.0-beta/'

lst = glob.glob(pin + '*/*/*/*/*/')

for l in lst:
   pthi = os.path.dirname(l)
   vers = os.listdir(pthi)
   latest = sorted(vers)[-1]
   print(pthi,'   ', vers,'   ', latest)

   try:
    os.popen('rm ' + pthi + '/latest').readlines()
   except:
    pass

   os.chdir(pthi)

   cmd = 'ln -s ' + latest + ' ' 'latest' 

   print(cmd)
   os.popen(cmd).readlines() 
   time.sleep(0.01)

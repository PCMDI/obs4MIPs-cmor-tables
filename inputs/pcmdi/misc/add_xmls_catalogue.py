import json, os
import glob

fq = 'mon'

pin = '/p/user_pub/PCMDIobs/obs4MIPs/*/*/mon/*/*/latest/'

lst = glob.glob(pin + '*.xml')

print(len(lst))

for l in lst:
  print(l)

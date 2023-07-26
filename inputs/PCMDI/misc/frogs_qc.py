import cdms2
import glob
import cdutil

pin  = '/p/user_pub/PCMDIobs/obs4MIPs/*/*/day/pr/1x1/latest/*.nc'

lst = glob.glob(pin)

for l in lst:
 print(l)
 f = cdms2.open(l)
 d = f('pr',time = slice(0,1))(squeeze=1)
 dsp = d(longitude=(0,1),latitude=(-89,-90)) 
 ga = cdutil.averager(d,axis='xy')
 print('global average at t=0 is ', ga,' ', dsp) 


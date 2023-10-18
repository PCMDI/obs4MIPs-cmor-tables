import os, glob
import cdms2
import time

fq = 'mon'
#fq = '3hr'
pin = '/p/user_pub/PCMDIobs/obs4MIPs/*/*/' + fq + '/*/*/latest/'
bd = '/p/user_pub/PCMDIobs/obs4MIPs/'



lst = glob.glob(pin + '*.nc')

lstdirs = []

for l in lst:
  diri = os.path.dirname(l)
  if diri not in lstdirs: 
   lstdirs.append(diri)
   print(diri)

print(len(lstdirs))

xmldirs = []
for ll in lstdirs:
  lsti = glob.glob(ll + '/*.nc')
  if len(lsti) > 1:
    print(len(lsti),' ', ll)
    xmldirs.append(ll)

for x in xmldirs:
# print(x.split('/'))
  product = x.split('/')[6]
  vr = x.split('/')[8] 
  grid =  x.split('/')[9] 
  fno = vr + '_' + product + '_PCMDI_' + grid + '.xml'
  os.chdir(x)
  cmd = 'cdscan -x ' + fno + ' *.nc'
  os.popen(cmd).readlines()
  print('finished with ' + cmd) 
  time.sleep(0.1) 
  f = cdms2.open(fno)
  d = f[vr]
  t = d.getTime()
  c = t.asComponentTime()
  most = str(c[0].month)
  yrst = str(c[0].year)
  moen = str(c[len(c)-1].month)
  yren = str(c[len(c)-1].year)

  fno1 = vr + '_mon_' + product + '_PCMDI_' + grid + '_' + yrst+most + '-' + yren+moen + '.xml'
  cmd2 = 'mv ' + fno + ' ' + fno1  
  os.popen(cmd2).readlines()
  print('done with ', cmd2)

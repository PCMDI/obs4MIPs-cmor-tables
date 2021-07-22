import cdms2
import glob
import os
from regrid2 import Regridder
import datetime

ver_out = datetime.datetime.now().strftime('v%Y%m%d')

dbver = 'PCMDIobs2'
ver = 'v20200612'
ver = 'v20200707'
target = '1x1'

pin = '/p/user_pub/PCMDIobs/' + dbver + '/atmos/mon/*/CERES-EBAF-4-1/gn/' + ver + '/'
pin = '/p/user_pub/PCMDIobs/' + dbver + '/atmos/mon/*/ERA-5/gn/' + ver + '/'

lst = glob.glob(pin + 'ua_*198001*.nc')

# TARGET 1x1 grid

fit = '/p/user_pub/PCMDIobs/PCMDIobs1/atm/mo/rlut/CERES/ac/rlut_CERES_000001-000012_ac.nc'
fo = cdms2.open(fit)
do = fo['rlut']
tgrid = do.getGrid()


for l in lst:   #[0:2]:
#print(l)

 newfile = l.replace('gn',target)
 newfile = newfile.replace(ver,ver_out)
 newdir_tmp = newfile.split('/')[0:9]  
 var = newfile.split('/')[7] 
 rep = '/'
 newdir = rep.join(newdir_tmp)
#print(newdir)

 try:
  os.mkdir(newdir + '/' + target)
 except:
  print('cant make dir ' + newdir + '/' + target)

 try:
  os.mkdir(newdir + '/' + target + '/' + ver_out + '/')
 except:
  pass


 fc = cdms2.open(l)
 d = fc(var)
 orig_grid = d.getGrid()

 regridFunc = Regridder(orig_grid,tgrid)

 dn = regridFunc(d)
 dn.id = var

 g = cdms2.open(newfile,'w+')
 g.write(dn)
 g.close()

#print(newdir)
 print('done with ', newfile)


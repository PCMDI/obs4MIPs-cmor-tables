import cdms2
import glob
import os
from regrid2 import Regridder
import datetime

ver_out = datetime.datetime.now().strftime('v%Y%m%d')

dbver = 'obs4MIPs'
ver = 'v20200612'
ver = 'v20210728'
ver = '*'
target = '1x1'

pin = '/p/user_pub/PCMDIobs/' + dbver + '/atmos/mon/*/CERES-EBAF-4-1/gn/' + ver + '/'
pin = '/p/user_pub/PCMDIobs/' + dbver + '/ECMWF/ERA-5/mon/*/gn/' + ver + '/'
#           /p/user_pub/PCMDIobs/obs4MIPs/ECMWF/ERA-5/mon/ta/gn/v20210729

lst = glob.glob(pin + 'ua_*198001*.nc')
lst = glob.glob(pin + '*.nc')

# TARGET 1x1 grid

fit = '/p/user_pub/PCMDIobs/PCMDIobs1/atm/mo/rlut/CERES/ac/rlut_CERES_000001-000012_ac.nc'
fit = '/p/user_pub/PCMDIobs/obs4MIPs/NASA-LaRC/CERES-EBAF-4-1/mon/rlut/gn/v20210727/rlut_mon_CERES-EBAF-4-1_PCMDI_gn_200301-201812.nc'
fo = cdms2.open(fit)
do = fo['rlut']
tgrid = do.getGrid()

for l in lst:   #[0:2]:
#print(l)

 newfile = l.replace('gn',target)
 newfile = newfile.replace(ver,ver_out)
 newdir_tmp = newfile.split('/')[0:9]  
 orig_ver = newfile.split('/')[10]
 newfile = newfile.replace(orig_ver,ver_out)
 var = newfile.split('/')[8] 
 rep = '/'
 newdir = rep.join(newdir_tmp)
#print(newdir)

 try:
  os.mkdir(newdir + '/' + target)
 except:
# print('cant make dir ' + newdir + '/' + target)
  pass

 try:
  os.mkdir(newdir + '/' + target + '/' + ver_out + '/')
 except:
  pass

 print('working on ', newfile)
 fc = cdms2.open(l)
 d = fc(var)
 orig_grid = d.getGrid()

 regridFunc = Regridder(orig_grid,tgrid)
 dn = regridFunc(d)
 dn.id = var

 g = cdms2.open(newfile,'w+')

 for att in fc.attributes.keys():
  setattr(g,att,fc.attributes[att]) 

 g.write(dn)
 g.close()
 fc.close()

#print(newdir)
 print('done with ', newfile)


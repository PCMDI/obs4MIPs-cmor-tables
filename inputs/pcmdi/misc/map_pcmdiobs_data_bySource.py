import os, sys
import glob

# MAPS PCMDIObs FROM BY VARIABLE TO BY SOURCE VIA SYMBOLIC LINKS

base_dir = '/p/user_pub/PCMDIobs/'
data_ver = 'PCMDIobs2.0-beta'
root = base_dir + '/' + data_ver + '/'

lstx = ['TRMM-3B43v-7', 'ERA-5']


try:
 new_root = root +'bySource'
 os.mkdir(new_root)
except:
 pass

lst = glob.glob(root + '*/mon/*/*/*/latest/*.nc')
lstx = glob.glob(root + '*/*/*/*/1x1/latest/*.xml')
products = []
for l in lst: 
  p = l.split('/')[9]
  if p not in products: products.append(p)

try:
  os.mkdir(new_root)
except:
  pass

for p in products:
 try:
  os.mkdir(new_root + '/' + p)
 except:
  pass

 pp= root + '*/*/*/' + p + '/*/latest/*.nc'
 lstp = glob.glob(pp)
 print(p,' ', len(lstp))

 for l in lstp:
   fn = l.split('/')[12]
   if 'ERA-5' not in fn and 'TRMM-3B43v-7' not in fn:
    print('----- ', fn) 

    try:
     os.remove(new_root + '/' + p + '/' + fn)
    except:
     pass
    print(l,new_root + '/' + p + '/' + fn)
    os.symlink(l,new_root + '/' + p + '/' + fn)

for l in lstx:
    fn = l.split('/')[12]
    p = l.split('/')[9]
    print('+++++ ', ) 
    try:
     os.remove(new_root + '/' + p + '/' + fn)
    except:
     pass
    print(new_root + '/' + p + '/' + fn)
    os.symlink(l,new_root + '/' + p + '/' + fn)


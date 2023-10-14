import os, glob
import sys

# THIS SCRIPT USES CDSCAN TO PRODUCE XMLS IN PCMDIobs IN CASES WHERE A TIME SERIES SPANS MULTIPLE netCDF FILES

scans = ['ERA-5_3d_mon_1x1']
scans = ['pr_3r_2x2']

for scan in scans:
 if scan == 'ERA-5_3d_mon_1x1':

   pin = '/p/user_pub/PCMDIobs/obs4MIPs/ECMWF/ERA-5/mon/*/1x1/*/'
   lst = glob.glob(pin)

   for l in lst:
     pthi = os.path.dirname(l)
     print(pthi.split('/'))

     var = pthi.split('/')[8]
     source = pthi.split('/')[6]

     if var in ['ta','zg','ua','va','hus','hur']:
      os.chdir(l)
      try:
        lst_nc = glob.glob('*.nc')
        lst_nc.sort()
        print(lst_nc[0],' ', lst_nc[len(lst_nc)-1])  

        startd = lst_nc[0].split('_')[5]
        startd = startd.split('-')[0]
        endd = lst_nc[len(lst_nc)-1].split('_')[5]
        endd = endd.split('-')[1]
        endd = endd.split('.nc')[0]

        fnmb = lst_nc[0].split('_1979')[0] + '_' + startd + '-' + endd + '.xml'
        cmd = 'cdscan -x ' + fnmb + ' *.nc'
        print(cmd)
        os.popen(cmd).readlines()
      except:
       pass       

####

 if scan == 'pr_3r_2x2':

   pin = '/p/user_pub/PCMDIobs/obs4MIPs/*/*/3hr/*/2x2/*/'
   lst = glob.glob(pin)

   for l in lst:
     pthi = os.path.dirname(l)
     print(pthi.split('/'))

     var = pthi.split('/')[8]
     source = pthi.split('/')[6]

     if var in ['pr']:
      os.chdir(l)

     try:
      lst_nc = glob.glob('*.nc')
      lst_nc.sort()
      print(lst_nc[0],' ', lst_nc[len(lst_nc)-1])

      startd = lst_nc[0].split('_')[5]
      startd = startd.split('-')[0]
      endd = lst_nc[len(lst_nc)-1].split('_')[5]
      endd = endd.split('-')[1]
      endd = endd.split('.nc')[0]

      fnmb = lst_nc[0].split('_2x2')[0] + '_' + startd + '-' + endd + '.xml'
      cmd = 'cdscan -x ' + fnmb + ' *.nc'
      print(cmd)
      os.popen(cmd).readlines()
     except:
      pass


 

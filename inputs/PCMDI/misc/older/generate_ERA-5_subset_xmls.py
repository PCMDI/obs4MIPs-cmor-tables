import os, glob

# THIS SCRIPT USES CDSCAN TO PRODUCE XMLS IN PCMDIobs IN CASES WHERE A TIME SERIES SPANS MULTIPLE netCDF FILES


pin = '/p/user_pub/PCMDIobs/PCMDIobs2/atmos/'


xmls_needed =  ['*/ta/ERA-5/*/*/']

for x in xmls_needed:
  pth = pin + x
 
  lst = glob.glob(pth)

  for l in lst:
   pthi = os.path.dirname(l)
#  print(pthi)

   var = pthi.split('/')[7]
   source = pthi.split('/')[8]

   if var in ['ta','zg','ua','va','hus','hur']:
    os.chdir(pthi)

    try:
     lst_nc = glob.glob('*.nc')
     lst_nc.sort()
#   print(lst_nc[0],' ', lst_nc[len(lst_nc)-1])  

     startd = lst_nc[0].split('_')[6]
     startd = startd.split('-')[0]
     endd = lst_nc[len(lst_nc)-1].split('_')[6]
     endd = endd.split('-')[1]
     endd = endd.split('.nc')[0]

     fnmb = lst_nc[0].split('_1979')[0] + '_' + startd + '-' + endd + '.xml'
#   print(fnmb)

     cmd = 'cdscan -x ' + fnmb + ' *.nc'
     print(cmd)
     os.popen(cmd).readlines()
    except:
     pass       



 

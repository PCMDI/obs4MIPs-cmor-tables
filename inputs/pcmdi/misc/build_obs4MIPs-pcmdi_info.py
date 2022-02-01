#!/bin/env python

# PJG 10212014 NOW INCLUDES SFTLF FROM
# /obs AND HARDWIRED TEST CASE WHICH
# NEEDS FIXIN

import cdms2
import gc
import glob
import json
import os
import sys
import time
import datetime

ver = datetime.datetime.now().strftime('v%Y%m%d')

verin = 'v20210727'
verin = 'latest'
#verin = 'v20210804'

###############################################################
datatype = 'clim'  
#datatype = 'monthly'
datatype = 'day'
#datatype = '3hr'

if len(sys.argv) > 1:
    data_path = sys.argv[1]
else:
    data_path = '/p/user_pub/PCMDIobs/obs4MIPs/'

if datatype == 'clim': 
    data_path = '/p/user_pub/PCMDIobs/obs4MIPs_clims/'
    comb = data_path + '/*/*/' + verin + '/*_*AC.*nc'

if datatype == 'monthly': comb = data_path + '*/*/mon/*/*/' + verin + '/*.nc' 
if datatype == 'day': comb = data_path + '*/*/day/*/*/' + verin + '/*.nc'
if datatype == '3hr': comb = data_path + '*/*/3hr/*/*/' + verin + '/*.xml'

pathout = '/p/user_pub/PCMDIobs/catalogue/'

lstt = glob.glob(comb)
lst = []

##### DO NOT INCLUDE CASES WITH MULTIPLE NC FILES - THOSE ARE ADDED AS XMLS IN SEPERATE SCRIPT
for l in lstt:
  print(l.split('/'))
  source_tmp = l.split('/')[6]
  if datatype != 'clim':
   vr  = l.split('/')[8]
   gr  = l.split('/')[9]
  if datatype == 'clim':
   vr  = l.split('/')[5]
#  gr  = l.split('/')[9]
#  w = sys.stdin.readline()

# print(source_tmp,' ', vr)
  if datatype == 'monthly':
    if source_tmp !='ERA-5': lst.append(l)
    if source_tmp =='ERA-5' and vr not in ['ua','va','ta','zg']: lst.append(l)
    if source_tmp =='ERA-5' and vr in ['ua','va','ta','zg']:
       tmpdir = os.path.dirname(l)
       xfile = glob.glob(tmpdir + '/*.xml')[0] 
       if xfile not in lst and xfile.find('1x1') !=-1:  
         lst.append(xfile)
         print('xfile is ', xfile)

  if datatype == 'day': lst.append(l)
  if datatype == '3hr': lst.append(l)

if datatype == 'clim': lst = lstt

#################################################################

print ('len of list ', len(lst))
#w = sys.stdin.readline()


# FOR MONTHLY MEAN OBS
obs_dic_in = {'rlut': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rst': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsut': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsds': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rlds': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsdt': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsdscs': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rldscs': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rlus': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsus': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rlutcs': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rsutcs': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rstcre': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'rltcre': {'default': 'CERES-EBAF-4-1','alternate1': 'CERES-EBAF-4-0'},
              'pr': {'default': 'GPCP-2-3',
                     'alternate1': 'TRMM-3B43v-7',
                     'alternate2': 'CMAP-V1902'},
              'prw': {'default': 'REMSS-PRW-v07r01'},
              'sfcWind': {'default': 'REMSS-PRW-v07r01','alternate1':'ERA-INT'},
              'tas': {'default': 'ERA-5',
                      'alternate1': 'ERA-INT',
                      'alternate2': 'ERA-40'},
              'psl': {'default': 'ERA-5',
                      'alternate2': 'ERA-40',
                      'alternate1': 'ERA-INT'},
              'ua':  {'default': 'ERA-5',
                     'alternate1': 'ERA-INT',
                     'alternate3': 'JRA25',
                     'alternate2': 'ERA-40'},
              'va': {'default': 'ERA-5',
                     'alternate1': 'ERA-INT',
                     'alternate2': 'ERA-40'},
              'uas': {'default': 'ERA-5',
                      'alternate1': 'ERA-INT',
                      'alternate2': 'ERA-40'},
              'hus': {'default': 'ERA-INT',
                      'alternate2': 'JRA25',
                      'alternate1': 'ERA-40'},
              'vas': {'default': 'ERA-5',
                      'alternate2': 'ERA-INT',
                      'alternate1': 'ERA-40'},
              'ta': {'default': 'ERA-5',
                     'alternate2': 'ERA-INT',
                     'alternate1': 'ERA-40'},
              'zg': {'default': 'ERA-5',
                     'alternate1': 'ERA-INT',
                     'alternate2': 'ERA-40'},
              'tauu': {'default': 'ERA-INT',
                       'alternate2': 'JRA25',
                       'alternate1': 'ERA-40'},
              'tauv': {'default': 'ERA-INT',
                       'alternate2': 'JRA25',
                       'alternate1': 'ERA-40'},
              'tos': {'default': 'UKMETOFFICE-HadISST-v1-1'},
              'zos': {'default': 'AVISO-1-0'},
              'sos': {'default': 'NODC-WOA09'},
              'ts': {'default': 'ERA-5', 'alternate1':'HadISST-1-1','alternate2':'OISST-L4-AVHRR-only-v2'},
              'thetao': {'default': 'WOA13v2',
                         'alternate1': 'UCSD',
                         'alternate2': 'Hosoda-MOAA-PGV',
                         'alternate3': 'IPRC'}
              }

obs_dic = {}

for filePath in lst:
    subp = filePath.split('/')
    tmp = os.path.dirname(filePath)
    versiontmp = os.readlink(tmp)
    template = filePath.split(data_path)[1]
    template = template.replace('latest',versiontmp)
    version = 'latest'

    if datatype != 'clim':
#    template = filePath.split(data_path)[1]
#    realm = subp[5]
     source = subp[6] 
     var = subp[8]
     product = source  #subp[8]
     grid = subp[9]

#    tmp = os.path.dirname(filePath)
#    versiontmp = os.readlink(tmp)
#    template = template.replace('latest',versiontmp)
#    version = 'latest' 

#    w = sys.stdin.readline()

##########
    if datatype == 'clim':
#    template = filePath.split(data_path)[1]
#    realm = subp[5]
     print('subp is ', subp)
     var = subp[5]
     source = subp[6]
     product = source 
     tmp1 = subp[8]
     tmp2 = tmp1.split('_')[4]
     grid = tmp2.split('.')[0]
     period = tmp2.split('.')[1]
#    version = subp[7] 


#    w = sys.stdin.readline()
###########
    fileName = subp[len(subp)-1]
    print('Filename:', fileName)

    if datatype == 'clim':  period = period.split('.')[0]
    if datatype in ['monthly','day']:
      tmp1 = fileName.split('_')[5]
      period = tmp1.split('.nc')[0]
    if datatype == '3hr':
      tmp1 = fileName.split('_')[4]
      period = tmp1.split('.xml')[0]
#     print('3hr period is ', period)
#   w = sys.stdin.readline()

    # TRAP FILE NAME FOR OBS DATA
    if var not in list(obs_dic.keys()):
#       print('CREATING FOR ---- ', var,' ', product,' ', obs_dic.keys())
        obs_dic[var] = {}

    if product not in list(obs_dic[var].keys()): obs_dic[var][product] = {}

#   obs_dic[var][product]['version'] = version 
    obs_dic[var][product]['template'] = template 
    obs_dic[var][product]['filename'] = fileName
#   obs_dic[var][product]['CMIP_CMOR_TABLE'] = tableId
    obs_dic[var][product]['period'] = period
#       obs_dic[var][product]['RefName'] = source 
    obs_dic[var][product]['RefTrackingDate'] = time.ctime(os.path.getmtime(filePath.strip()))
    md5 = os.popen('md5sum ' + filePath)
    md5 = md5.readlines()[0].split()[0]
    obs_dic[var][product]['MD5sum'] = md5
    f = cdms2.open(filePath)
    table_id = f.table_id
    d = f[var]
    shape = d.shape
    shape = repr(d.shape)
    obs_dic[var][product]['CMIP_CMOR_TABLE'] = table_id.replace('obs4MIPs_','')
    f.close()
    obs_dic[var][product]['shape'] = shape
    obs_dic[var][product]['shape'] = shape
    del(d, fileName)
    gc.collect()

    try:
        for r in list(obs_dic_in[var].keys()):
            # print '1',r,var,product
            # print obs_dic_in[var][r],'=',product
            if obs_dic_in[var][r] == product:
                # print '2',r,var,product
                obs_dic[var][r] = product
    except BaseException:
        pass

gc.collect()

# ADD SPECIAL CASE SFTLF FROM TEST DIR
#product = 'UKMETOFFICE-HadISST-v1-1'
#var = 'sftlf'
#obs_dic[var][product] = {}
#obs_dic[var][product]['CMIP_CMOR_TABLE'] = 'fx'
#obs_dic[var][product]['shape'] = '(180, 360)'
#obs_dic[var][product]['filename'] = \
#    'sftlf_pcmdi-metrics_fx_UKMETOFFICE-HadISST-v1-1_198002-200501-clim.nc'
#obs_dic[var][product]['RefName'] = product
#obs_dic[var][product]['MD5sum'] = ''
#obs_dic[var][product]['RefTrackingDate'] = ''
#obs_dic[var][product]['period'] = '198002-200501'
#del(product, var)
#gc.collect()

# Save dictionary locally and in doc subdir
if datatype == 'clim':  
  json_name = pathout + 'obs4MIPs_PCMDI_clims_byVar_catalogue_' + ver + '.json'
  json_name_GH = '../catalogue/' + 'obs4MIPs_PCMDI_clims_byVar_catalogue_' + ver + '.json'
if datatype == 'monthly':  
  json_name = pathout + 'obs4MIPs_PCMDI_monthly_byVar_catalogue_' + ver + '.json'
  json_name_GH = '../catalogue/' + 'obs4MIPs_PCMDI_monthly_byVar_catalogue_' + ver + '.json'
if datatype == 'day':  
  json_name = pathout + 'obs4MIPs_PCMDI_day_byVar_catalogue_' + ver + '.json'
  json_name_GH = '../catalogue/' + 'obs4MIPs_PCMDI_day_byVar_catalogue_' + ver + '.json'
if datatype == '3hr':  
  json_name = pathout + 'obs4MIPs_PCMDI_3hr_byVar_catalogue_' + ver + '.json'
  json_name_GH = '../catalogue/'  + 'obs4MIPs_PCMDI_3hr_byVar_catalogue_' + ver + '.json'

json.dump(obs_dic, open(json_name, 'w'), sort_keys=True, indent=4,
          separators=(',', ': '))
json.dump(obs_dic, open(json_name_GH, 'w'), sort_keys=True, indent=4,
          separators=(',', ': '))

time.sleep(2)

### REMAP JSON BY SOURCE

catalogue_json_bySourceID = json_name.replace('byVar','bySource')
catalogue_json_bySourceID_GH = json_name_GH.replace('byVar','bySource')

print(catalogue_json_bySourceID)

f_catalogue  = open(json_name)  #open(catalogue_json)
f_catalogue_GH = open(json_name_GH)
dict_catalogue = json.loads(f_catalogue.read())

#
# Collect variables
#
var_list = sorted(list(dict_catalogue.keys()))
print('var_list:', var_list)

#
# Collect data sources
#
data_source_list = []
for var in var_list:
    data_source_list.extend(list(dict_catalogue[var].keys()))
# Remove any duplicates
data_source_list = sorted(list(dict.fromkeys(data_source_list)))
# Remove other than data source
remove_elements_list = ['default', 'alternate1', 'alternate2']
for element in remove_elements_list:
    try:
        data_source_list.remove(element)
    except:
        pass

print('data_source_list:', data_source_list)

#
# New dictionary with layer switched (var/dataSource to dataSource/var)
#
dict_catalogue_new = {}
for data_source in data_source_list:
    dict_catalogue_new[data_source] = {}
    for var in var_list:
        try:
            dict_catalogue_new[data_source][var] = dict_catalogue[var][data_source]
        except:
            pass
#
# Rewrite
#
with open(catalogue_json_bySourceID, "w") as f_catalogue_new:
    json.dump(dict_catalogue_new, f_catalogue_new, indent=4, sort_keys=True)
with open(catalogue_json_bySourceID_GH, "w") as f_catalogue_new_GH:
    json.dump(dict_catalogue_new, f_catalogue_new_GH, indent=4, sort_keys=True)




#/!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script generates all necessary json files for obs4MIPs 

Original version created Tue Jul 12 16:11:44 2016 Paul J. Durack (PJD) 
Substantially modified by Peter Gleckler (PJG) since 2016
Several functions adopted from durolib now included and updated to PY3

"""

import os, json, ssl,shutil,sys, gc, re, copy

#######################################################################
def readJsonCreateDict_dep(buildList):
    """
    Documentation for readJsonCreateDict(buildList):
    -------
    The readJsonCreateDict() function reads web-based json files and writes
    their contents to a dictionary in memory
    Author: Paul J. Durack : pauldurack@llnl.gov
    The function takes a list argument with two entries. The first is the
    variable name for the assigned dictionary, and the second is the URL
    of the json file to be read and loaded into memory. Multiple entries
    can be included by generating additional embedded lists
    Usage:
    ------
    Adopted from Durolib to be used in obs4MIPS.  CONVERTED TO PY3 by PJG in 2021

    """

    import os, json, ssl  #, urllib2   # urllib.request this is for PY3
    import urllib.request  # CONVERTED TO PY3 by PJG in 2021 
    from urllib.request import urlopen #PY3

    # Test for list input of length == 2
    if len(buildList[0]) != 2:
        print('Invalid inputs, exiting..')
        sys.exit()
    # Create urllib2 context to deal with lab/LLNL web certificates
    ctx                 = ssl.create_default_context()
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE
    # Iterate through buildList and write results to jsonDict
    jsonDict = {}
    for count,table in enumerate(buildList):
        #print 'Processing:',table[0]
        # Read web file
#       jsonOutput = urllib2.urlopen(table[1], context=ctx) # Py2
        jsonOutput = urlopen(table[1], context=ctx) # Py3
        tmp = jsonOutput.read()
        vars()[table[0]] = tmp
        jsonOutput.close()
        # Write local json
        tmpFile = open('tmp.json','w')
        tmpFile.write(eval(table[0]))
        tmpFile.close()
        # Read local json
        vars()[table[0]] = json.load(open('tmp.json','r'))
        os.remove('tmp.json')
        jsonDict[table[0]] = eval(table[0]) ; # Write to dictionary

    return jsonDict

def readJsonCreateDict(buildList):

    import os, json, ssl  #, urllib2   # urllib.request this is for PY3
    import urllib.request  # CONVERTED TO PY3 by PJG in 2021 
    from urllib.request import urlopen #PY3

    # Test for list input of length == 2
    if len(buildList[0]) != 2:
        print('Invalid inputs, exiting..')
        sys.exit()
    # Create urllib2 context to deal with lab/LLNL web certificates
    ctx                 = ssl.create_default_context()
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE
    # Iterate through buildList and write results to jsonDict
    jsonDict = {}
    for count,table in enumerate(buildList):
        print('Processing:',table[0])
        jsonOutput = urlopen(table[1], context=ctx) # Py3
        tmp = jsonOutput.read()
        jsonDict[table[0]] = tmp #eval(table[0]) ; # Write to dictionary

    return jsonDict


#%% Determine path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))

#%% Create urllib2 context to deal with lab/LLNL web certificates
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% List target tables
masterTargets = [
 'Aday',
 'A3hr',
 'A6hr',
 'Oday',
 'SIday',
 'Amon',
 'Lmon',
 'Omon',
 'SImon',
 'fx',
# 'monNobs',
# 'monStderr',
 'coordinate',
 'formula_terms',
 'frequency',
 'grid_label',
 'grids',
 'institution_id',
 'license_',
 'nominal_resolution',
 'product',
 'realm',
 'region',
 'required_global_attributes',
 'source_id',
 'source_type',
 'table_id'
 ] ;

#%% Tables
sha = '87218055a04f6e01c36039a75652d3824d1649ad'
tableSource = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_coordinate.json'],
 ['formula_terms','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_formula_terms.json'],
 ['frequency','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_frequency.json'],
 ['fx','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_fx.json'],
 ['grid_label','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_grid_label.json'],
 ['grids','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_grids.json'],
 ['nominal_resolution','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_nominal_resolution.json'],
#['product','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_product.json'],
 ['product','https://raw.githubusercontent.com/PCMDI/input4MIPs-cmor-tables/master/input4MIPs_product.json'],
 ['Amon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Amon.json'],
 ['Lmon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Lmon.json'],
 ['Omon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Omon.json'],
 ['SImon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SImon.json'],
 ['Aday','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_day.json'],
 ['A6hr','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_6hrPlev.json'],
 ['A3hr','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_3hr.json'], 
 ['Oday','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Oday.json'],
 ['SIday','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SIday.json'],
#['monNobs','https://raw.githubusercontent.com/PCMDI/obs4mips-cmor-tables/master/Tables/obs4MIPs_monNobs.json'],
#['monStderr','https://raw.githubusercontent.com/PCMDI/obs4mips-cmor-tables/master/Tables/obs4MIPs_monStderr.json'],
 ['region','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_region.json'],
 ['realm','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_realm.json'],
 ['source_type','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_source_type.json'],
 ['table_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_table_id.json'],
 ['institution_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_institution_id.json']
 ] ;

#%% Loop through tables and create in-memory objects
# Loop through tableSource and create output tables
tmp = readJsonCreateDict(tableSource)
for count,table in enumerate(tmp.keys()):
    #print 'table:', table
#   if table in ['frequency','grid_label','nominal_resolution']:
#       vars()[table] = tmp[table].get(table)
#   else:
        vars()[table] = tmp[table]
del(tmp,count,table) ; gc.collect()

print('product dic is ', vars()['product'])

#w = sys.stdin.readline()

#########
'''
# Cleanup by extracting only variable lists
for count2,table in enumerate(tableSource):
    tableName = table[0]
    print('tableName:',tableName)
    #print eval(tableName)
    if tableName in ['coordinate','formula_terms','frequency','grid_label','nominal_resolution']:
        continue
    else:
        if tableName in ['monNobs', 'monStderr']:
            eval(tableName)['Header'] = copy.deepcopy(Amon['Header']) ; # Copy header info from upstream file
            del(eval(tableName)['Header']['#dataRequest_specs_version']) ; # Purge upstream identifier
            eval(tableName)['Header']['realm'] = 'aerosol atmos atmosChem land landIce ocean ocnBgchem seaIce' ; # Append all realms
        eval(tableName)['Header']['Conventions'] = 'CF-1.7 ODS-2.1' ; # Update "Conventions": "CF-1.7 CMIP-6.0"
        if tableName not in ['monNobs', 'monStderr']:
            eval(tableName)['Header']['#dataRequest_specs_version'] = eval(tableName)['Header']['data_specs_version']
        eval(tableName)['Header']['data_specs_version'] = '2.1.0'
        if 'mip_era' in eval(tableName)['Header'].keys():
            eval(tableName)['Header']['#mip_era'] = eval(tableName)['Header']['mip_era']
            del(eval(tableName)['Header']['mip_era']) ; # Remove after rewriting
        eval(tableName)['Header']['product'] = 'observations' ; # Cannot be 'observations reanalysis'
        eval(tableName)['Header']['table_date'] = time.strftime('%d %B %Y')
        eval(tableName)['Header']['table_id'] = ''.join(['Table obs4MIPs_',tableName])
        # Attempt to move information from input.json to table files - #84 - CMOR-limited
        #eval(tableName)['Header']['activity_id'] = 'obs4MIPs'
        #eval(tableName)['Header']['_further_info_url_tmpl'] = 'http://furtherinfo.es-doc.org/<activity_id><institution_id><source_label><source_id><variable_id>'
        #eval(tableName)['Header']['output_file_template'] = '<variable_id><table_id><source_id><variant_label><grid_label>'
        #eval(tableName)['Header']['output_path_template'] = '<activity_id><institution_id><source_id><table_id><variable_id><grid_label><version>'
        #eval(tableName)['Header']['tracking_prefix'] = 'hdl:21.14102'
        #eval(tableName)['Header']['_control_vocabulary_file'] = 'obs4MIPs_CV.json'
        #eval(tableName)['Header']['_AXIS_ENTRY_FILE'] = 'obs4MIPs_coordinate.json'
        #eval(tableName)['Header']['_FORMULA_VAR_FILE'] = 'obs4MIPs_formula_terms.json'
        if 'baseURL' in eval(tableName)['Header'].keys():
            del(eval(tableName)['Header']['baseURL']) ; # Remove spurious entry
'''
########

# Cleanup realms

Amon = eval(Amon)
Lmon = eval(Lmon)
Omon = eval(Omon)
SImon = eval(SImon)
fx = eval(fx)
Aday = eval(Aday)
A3hr = eval(A3hr)
A6hr = eval(A6hr)
Oday = eval(Oday)
SIday = eval(SIday)
#coordinate = eval(coordinate)

Amon['Header']['realm']     = 'atmos'
Amon['variable_entry'].pop('pfull')
Amon['variable_entry'].pop('phalf')
Lmon['Header']['realm']     = 'land'
Omon['Header']['realm']     = 'ocean'
SImon['Header']['realm']    = 'seaIce'
fx['Header']['realm']       = 'fx'
A3hr['Header']['realm']     = 'atmos'
A6hr['Header']['realm']     = 'atmos'
Oday['Header']['realm']     = 'ocean'
SIday['Header']['realm']    = 'seaIce'

Amon['Header']['table_id']  = 'Table obs4MIPs_Amon'
Lmon['Header']['table_id']  = 'Table obs4MIPs_Lmon'
Omon['Header']['table_id']  = 'Table obs4MIPs_Omon'
SImon['Header']['table_id']  = 'Table obs4MIPs_SImon'
fx['Header']['table_id']  = 'Table obs4MIPs_fx'
Aday['Header']['table_id']  = 'Table obs4MIPs_Aday'
A3hr['Header']['table_id']  = 'Table obs4MIPs_A3hr'
A6hr['Header']['table_id']  = 'Table obs4MIPs_A6hr'
Oday['Header']['table_id']  = 'Table obs4MIPs_Oday'
SIday['Header']['table_id'] = 'Table obs4MIPs_SIday'
SIday['Header']['realm']    = 'seaIce'

#realm = eval(realm)

# Clean out modeling_realm
for jsonName in [Aday,A3hr,A6hr,Oday,SIday,Amon,Lmon,Omon,SImon,fx]:
  try:
   jsonName['Header']["Conventions"] = "CF-1.7 ODS-2.1"
   jsonName['Header']["data_specs_version"] = "2.1.0"
  except:
   pass

for jsonName in masterTargets:
  if jsonName in []:
    dictToClean = eval(jsonName)
    for key, value in dictToClean.iteritems():
        if key == 'Header':
            continue
        for key1,value1 in value.iteritems():
            if 'modeling_realm' in dictToClean[key][key1].keys():
                dictToClean[key][key1].pop('modeling_realm')
            if 'cell_measures' in dictToClean[key][key1].keys():
                dictToClean[key][key1]['cell_measures'] = '' ; # Set all cell_measures entries to blank

'''
# Set missing value for integer variables
for tab in (Aday,A3hr,A6hr,Oday,SIday,Amon,Lmon,Omon,SImon,fx,monNobs,monStderr):
    tab['Header']['int_missing_value'] = str(-2**31)
'''

# Add new variables
# 

'''
# Test for variable lists
for var in SIday['variable_entry'].keys():
    print var
sys.exit()
'''

'''
Amon['variable_entry']['uaplev37_ERA5'] = {}
Amon['variable_entry']['uaplev37_ERA5']['cell_measures'] = ''
Amon['variable_entry']['uaplev37_ERA5']['cell_methods'] = 'time: mean'
Amon['variable_entry']['uaplev37_ERA5']['comment'] = ''
Amon['variable_entry']['uaplev37_ERA5']['dimensions'] = 'longitude latitude plev37_ERA5 time'
Amon['variable_entry']['uaplev37_ERA5']['frequency'] = 'mon'
Amon['variable_entry']['uaplev37_ERA5']['long_name'] = 'Eastward Wind'
Amon['variable_entry']['uaplev37_ERA5']['ok_max_mean_abs'] = ''
Amon['variable_entry']['uaplev37_ERA5']['ok_min_mean_abs'] = ''
Amon['variable_entry']['uaplev37_ERA5']['out_name'] = 'ua'
Amon['variable_entry']['uaplev37_ERA5']['positive'] = ''
Amon['variable_entry']['uaplev37_ERA5']['standard_name'] = 'eastward_wind'
Amon['variable_entry']['uaplev37_ERA5']['type'] = 'real'
Amon['variable_entry']['uaplev37_ERA5']['units'] = 'm s-1'
Amon['variable_entry']['uaplev37_ERA5']['valid_max'] = ''
Amon['variable_entry']['uaplev37_ERA5']['valid_min'] = ''

Amon['variable_entry']['vaplev37_ERA5'] = {}
Amon['variable_entry']['vaplev37_ERA5']['cell_measures'] = ''
Amon['variable_entry']['vaplev37_ERA5']['cell_methods'] = 'time: mean'
Amon['variable_entry']['vaplev37_ERA5']['comment'] = ''
Amon['variable_entry']['vaplev37_ERA5']['dimensions'] = 'longitude latitude plev37_ERA5 time'
Amon['variable_entry']['vaplev37_ERA5']['frequency'] = 'mon'
Amon['variable_entry']['vaplev37_ERA5']['long_name'] = 'Northward Wind'
Amon['variable_entry']['vaplev37_ERA5']['ok_max_mean_abs'] = ''
Amon['variable_entry']['vaplev37_ERA5']['ok_min_mean_abs'] = ''
Amon['variable_entry']['vaplev37_ERA5']['out_name'] = 'va'
Amon['variable_entry']['vaplev37_ERA5']['positive'] = ''
Amon['variable_entry']['vaplev37_ERA5']['standard_name'] = 'northward_wind'
Amon['variable_entry']['vaplev37_ERA5']['type'] = 'real'
Amon['variable_entry']['vaplev37_ERA5']['units'] = 'm s-1'
Amon['variable_entry']['vaplev37_ERA5']['valid_max'] = ''
Amon['variable_entry']['vaplev37_ERA5']['valid_min'] = ''


Amon['variable_entry']['zgplev37_ERA5'] = {}
Amon['variable_entry']['zgplev37_ERA5']['cell_measures'] = ''
Amon['variable_entry']['zgplev37_ERA5']['cell_methods'] = 'time: mean'
Amon['variable_entry']['zgplev37_ERA5']['comment'] = ''
Amon['variable_entry']['zgplev37_ERA5']['dimensions'] = 'longitude latitude plev37_ERA5 time'
Amon['variable_entry']['zgplev37_ERA5']['frequency'] = 'mon'
Amon['variable_entry']['zgplev37_ERA5']['long_name'] = 'Geopotential Height'
Amon['variable_entry']['zgplev37_ERA5']['ok_max_mean_abs'] = ''
Amon['variable_entry']['zgplev37_ERA5']['ok_min_mean_abs'] = ''
Amon['variable_entry']['zgplev37_ERA5']['out_name'] = 'zg'
Amon['variable_entry']['zgplev37_ERA5']['positive'] = ''
Amon['variable_entry']['zgplev37_ERA5']['standard_name'] = 'geopotential_height'
Amon['variable_entry']['zgplev37_ERA5']['type'] = 'real'
Amon['variable_entry']['zgplev37_ERA5']['units'] = 'm'
Amon['variable_entry']['zgplev37_ERA5']['valid_max'] = ''
Amon['variable_entry']['zgplev37_ERA5']['valid_min'] = ''

# Add new variables

Amon['variable_entry']['taplev37_ERA5'] = {}
Amon['variable_entry']['taplev37_ERA5']['cell_measures'] = ''
Amon['variable_entry']['taplev37_ERA5']['cell_methods'] = 'time: mean'
Amon['variable_entry']['taplev37_ERA5']['comment'] = ''
Amon['variable_entry']['taplev37_ERA5']['dimensions'] = 'longitude latitude plev37_ERA5 time'
Amon['variable_entry']['taplev37_ERA5']['frequency'] = 'mon'
Amon['variable_entry']['taplev37_ERA5']['long_name'] = 'Temperature'
Amon['variable_entry']['taplev37_ERA5']['ok_max_mean_abs'] = ''
Amon['variable_entry']['taplev37_ERA5']['ok_min_mean_abs'] = ''
Amon['variable_entry']['taplev37_ERA5']['out_name'] = 'ta'
Amon['variable_entry']['taplev37_ERA5']['positive'] = ''
Amon['variable_entry']['taplev37_ERA5']['standard_name'] = 'air_temperature'
Amon['variable_entry']['taplev37_ERA5']['type'] = 'real'
Amon['variable_entry']['taplev37_ERA5']['units'] = 'K'
Amon['variable_entry']['taplev37_ERA5']['valid_max'] = ''
Amon['variable_entry']['taplev37_ERA5']['valid_min'] = ''
'''

Amon['variable_entry'][u'rltcre'] = {}
Amon['variable_entry']['rltcre']['cell_measures'] = ''
Amon['variable_entry']['rltcre']['cell_methods'] = 'time: mean'
Amon['variable_entry']['rltcre']['comment'] = ''
Amon['variable_entry']['rltcre']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['rltcre']['frequency'] = 'mon'
Amon['variable_entry']['rltcre']['long_name'] = 'Top of Atmosphere Longwave CRE'
Amon['variable_entry']['rltcre']['ok_max_mean_abs'] = ''
Amon['variable_entry']['rltcre']['ok_min_mean_abs'] = ''
Amon['variable_entry']['rltcre']['out_name'] = 'rltcre'
Amon['variable_entry']['rltcre']['positive'] = 'up'
Amon['variable_entry']['rltcre']['standard_name'] = 'TOA_LW_cloud_forcing'
Amon['variable_entry']['rltcre']['type'] = 'real'
Amon['variable_entry']['rltcre']['units'] = 'W m-2'
Amon['variable_entry']['rltcre']['valid_max'] = ''
Amon['variable_entry']['rltcre']['valid_min'] = ''

# Add new variables

# Variable sponsor - RSS; Andy Manaster 
Amon['variable_entry'][u'tlt'] = {}
Amon['variable_entry']['tlt']['cell_measures'] = ''
Amon['variable_entry']['tlt']['cell_methods'] = 'time: mean'
Amon['variable_entry']['tlt']['comment'] = ''
Amon['variable_entry']['tlt']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['tlt']['frequency'] = 'mon'
Amon['variable_entry']['tlt']['long_name'] = 'MSU Temperature Lower Troposphere'
Amon['variable_entry']['tlt']['ok_max_mean_abs'] = ''
Amon['variable_entry']['tlt']['ok_min_mean_abs'] = ''
Amon['variable_entry']['tlt']['out_name'] = 'tlt'
Amon['variable_entry']['tlt']['positive'] = ''
Amon['variable_entry']['tlt']['standard_name'] = 'MSU_Temperature_Lower_Troposphere'
Amon['variable_entry']['tlt']['type'] = 'real'
Amon['variable_entry']['tlt']['units'] = 'K'
Amon['variable_entry']['tlt']['valid_max'] = ''
Amon['variable_entry']['tlt']['valid_min'] = ''

# Variable sponsor - RSS; Andy Manaster 
Amon['variable_entry'][u'tmt'] = {}
Amon['variable_entry']['tmt']['cell_measures'] = ''
Amon['variable_entry']['tmt']['cell_methods'] = 'time: mean'
Amon['variable_entry']['tmt']['comment'] = ''
Amon['variable_entry']['tmt']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['tmt']['frequency'] = 'mon'
Amon['variable_entry']['tmt']['long_name'] = 'MSU Temperature Mid Troposphere'
Amon['variable_entry']['tmt']['ok_max_mean_abs'] = ''
Amon['variable_entry']['tmt']['ok_min_mean_abs'] = ''
Amon['variable_entry']['tmt']['out_name'] = 'tmt'
Amon['variable_entry']['tmt']['positive'] = ''
Amon['variable_entry']['tmt']['standard_name'] = 'MSU_Temperature_Mid_Troposphere'
Amon['variable_entry']['tmt']['type'] = 'real'
Amon['variable_entry']['tmt']['units'] = 'K'
Amon['variable_entry']['tmt']['valid_max'] = ''
Amon['variable_entry']['tmt']['valid_min'] = ''

# Variable sponsor - RSS; Andy Manaster 
Amon['variable_entry'][u'tls'] = {}
Amon['variable_entry']['tls']['cell_measures'] = ''
Amon['variable_entry']['tls']['cell_methods'] = 'time: mean'
Amon['variable_entry']['tls']['comment'] = ''
Amon['variable_entry']['tls']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['tls']['frequency'] = 'mon'
Amon['variable_entry']['tls']['long_name'] = 'MSU Temperature Lower Stratosphere'
Amon['variable_entry']['tls']['ok_max_mean_abs'] = ''
Amon['variable_entry']['tls']['ok_min_mean_abs'] = ''
Amon['variable_entry']['tls']['out_name'] = 'tmt'
Amon['variable_entry']['tls']['positive'] = ''
Amon['variable_entry']['tls']['standard_name'] = 'MSU_Temperature_Lower_Stratosphere'
Amon['variable_entry']['tls']['type'] = 'real'
Amon['variable_entry']['tls']['units'] = 'K' 
Amon['variable_entry']['tls']['valid_max'] = ''
Amon['variable_entry']['tls']['valid_min'] = ''


# Variable sponsor - RSS; Andy Manaster 
Amon['variable_entry'][u'tlt'] = {}
Amon['variable_entry']['tlt']['cell_measures'] = ''
Amon['variable_entry']['tlt']['cell_methods'] = 'time: mean'
Amon['variable_entry']['tlt']['comment'] = ''
Amon['variable_entry']['tlt']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['tlt']['frequency'] = 'mon'
Amon['variable_entry']['tlt']['long_name'] = 'MSU Temperature Lower Troposphere'
Amon['variable_entry']['tlt']['ok_max_mean_abs'] = ''
Amon['variable_entry']['tlt']['ok_min_mean_abs'] = ''
Amon['variable_entry']['tlt']['out_name'] = 'tlt'
Amon['variable_entry']['tlt']['positive'] = ''
Amon['variable_entry']['tlt']['standard_name'] = 'MSU_Temperature_Lower_Troposphere'
Amon['variable_entry']['tlt']['type'] = 'real'
Amon['variable_entry']['tlt']['units'] = 'K'
Amon['variable_entry']['tlt']['valid_max'] = ''
Amon['variable_entry']['tlt']['valid_min'] = ''



# Variable sponsor - NOAA-NCEI; Jim Baird (JimBiardCics)
Amon['variable_entry'][u'rstcre'] = {}
Amon['variable_entry']['rstcre']['cell_measures'] = ''
Amon['variable_entry']['rstcre']['cell_methods'] = 'time: mean'
Amon['variable_entry']['rstcre']['comment'] = ''
Amon['variable_entry']['rstcre']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['rstcre']['frequency'] = 'mon'
Amon['variable_entry']['rstcre']['long_name'] = 'Top of Atmosphere Shortwave CRE'
Amon['variable_entry']['rstcre']['ok_max_mean_abs'] = ''
Amon['variable_entry']['rstcre']['ok_min_mean_abs'] = ''
Amon['variable_entry']['rstcre']['out_name'] = 'rstcre'
Amon['variable_entry']['rstcre']['positive'] = 'up'
Amon['variable_entry']['rstcre']['standard_name'] = 'TOA_SW_cloud_forcing'
Amon['variable_entry']['rstcre']['type'] = 'real'
Amon['variable_entry']['rstcre']['units'] = 'W m-2'
Amon['variable_entry']['rstcre']['valid_max'] = ''
Amon['variable_entry']['rstcre']['valid_min'] = ''

Amon['variable_entry'][u'rt'] = {}
Amon['variable_entry']['rt']['cell_measures'] = ''
Amon['variable_entry']['rt']['cell_methods'] = 'time: mean'
Amon['variable_entry']['rt']['comment'] = ''
Amon['variable_entry']['rt']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['rt']['frequency'] = 'mon'
Amon['variable_entry']['rt']['long_name'] = 'Top of Atmosphere Net Radation'
Amon['variable_entry']['rt']['ok_max_mean_abs'] = ''
Amon['variable_entry']['rt']['ok_min_mean_abs'] = ''
Amon['variable_entry']['rt']['out_name'] = 'rt'
Amon['variable_entry']['rt']['positive'] = ''
Amon['variable_entry']['rt']['standard_name'] = 'Net_TOA_Radiation'
Amon['variable_entry']['rt']['type'] = 'real'
Amon['variable_entry']['rt']['units'] = 'W m-2'
Amon['variable_entry']['rt']['valid_max'] = ''
Amon['variable_entry']['rt']['valid_min'] = ''

# Add new variables
# Variable sponsor - PCMDI; PjG 
Amon['variable_entry'][u'hfns'] = {}
Amon['variable_entry']['hfns']['cell_measures'] = ''
Amon['variable_entry']['hfns']['cell_methods'] = 'time: mean'
Amon['variable_entry']['hfns']['comment'] = ''
Amon['variable_entry']['hfns']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['hfns']['frequency'] = 'mon'
Amon['variable_entry']['hfns']['long_name'] = 'Net Surface Energy'
Amon['variable_entry']['hfns']['ok_max_mean_abs'] = ''
Amon['variable_entry']['hfns']['ok_min_mean_abs'] = ''
Amon['variable_entry']['hfns']['out_name'] = 'hfns'
Amon['variable_entry']['hfns']['positive'] = ''
Amon['variable_entry']['hfns']['standard_name'] = 'Net_Surface_Energy'
Amon['variable_entry']['hfns']['type'] = 'real'
Amon['variable_entry']['hfns']['units'] = 'W m-2'
Amon['variable_entry']['hfns']['valid_max'] = ''
Amon['variable_entry']['hfns']['valid_min'] = ''

# Add new variables
# Variable sponsor - PCMDI; PjG 
Amon['variable_entry'][u'hfns'] = {}
Amon['variable_entry']['hfns']['cell_measures'] = ''
Amon['variable_entry']['hfns']['cell_methods'] = 'time: mean'
Amon['variable_entry']['hfns']['comment'] = ''
Amon['variable_entry']['hfns']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['hfns']['frequency'] = 'mon'
Amon['variable_entry']['hfns']['long_name'] = 'Net Surface Energy'
Amon['variable_entry']['hfns']['ok_max_mean_abs'] = ''
Amon['variable_entry']['hfns']['ok_min_mean_abs'] = ''
Amon['variable_entry']['hfns']['out_name'] = 'hfns'
Amon['variable_entry']['hfns']['positive'] = ''
Amon['variable_entry']['hfns']['standard_name'] = 'Net_Surface_Energy'
Amon['variable_entry']['hfns']['type'] = 'real'
Amon['variable_entry']['hfns']['units'] = 'W m-2'
Amon['variable_entry']['hfns']['valid_max'] = ''
Amon['variable_entry']['hfns']['valid_min'] = ''

# Add new variables
# Variable sponsor - PCMDI; PjG 
Amon['variable_entry'][u'toz'] = {}
Amon['variable_entry']['toz']['cell_measures'] = "area: areacella" 
Amon['variable_entry']['toz']['cell_methods'] = "area: time: mean" 
Amon['variable_entry']['toz']['comment'] = 'Total ozone column calculated at 0 degrees C and 1 bar, such that 1m = 1e5 DU.'
Amon['variable_entry']['toz']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['toz']['frequency'] = 'mon'
Amon['variable_entry']['toz']['long_name'] = 'Total Column Ozone'
Amon['variable_entry']['toz']['ok_max_mean_abs'] = ''
Amon['variable_entry']['toz']['ok_min_mean_abs'] = ''
Amon['variable_entry']['toz']['out_name'] = 'toz'
Amon['variable_entry']['toz']['positive'] = ''
Amon['variable_entry']['toz']['standard_name'] = 'equivalent_thickness_at_stp_of_atmosphere_ozone_content'
Amon['variable_entry']['toz']['type'] = 'real'
Amon['variable_entry']['toz']['units'] = 'm'
Amon['variable_entry']['toz']['valid_max'] = ''
Amon['variable_entry']['toz']['valid_min'] = ''



# monNobs
#--------
# Example new monNobs entry
#monNobs['variable_entry'][u'ndviNobs']['comment'] = ''
#monNobs['variable_entry'][u'ndviNobs']['dimensions'] = 'longitude latitude time'
#monNobs['variable_entry'][u'ndviNobs']['frequency'] = 'mon'
#monNobs['variable_entry'][u'ndviNobs']['long_name'] = 'NDVI number of observations'
#monNobs['variable_entry'][u'ndviNobs']['modeling_realm'] = 'atmos' ; # Overwrites table realm entry (CMOR will fail if multiple realms are set in the header and this field is missing)
#monNobs['variable_entry'][u'ndviNobs']['out_name'] = 'ndviNobs'
#monNobs['variable_entry'][u'ndviNobs']['standard_name'] = 'number_of_observations'
#monNobs['variable_entry'][u'ndviNobs']['type'] = ''
#monNobs['variable_entry'][u'ndviNobs']['units'] = '1'

# monStderr
#--------
# Example new monStderr entry
#monStderr['variable_entry'][u'ndviStderr'] = {}
#monStderr['variable_entry'][u'ndviStderr']['comment'] = ''
#monStderr['variable_entry'][u'ndviStderr']['dimensions'] = 'longitude latitude time'
#monStderr['variable_entry'][u'ndviStderr']['frequency'] = 'mon'
#monStderr['variable_entry'][u'ndviStderr']['long_name'] = 'NDVI standard error'
#monStderr['variable_entry'][u'ndviStderr']['modeling_realm'] = 'atmos' ; # Overwrites table realm entry (CMOR will fail if multiple realms are set in the header and this field is missing)
#monStderr['variable_entry'][u'ndviStderr']['out_name'] = 'ndviStderr'
#monStderr['variable_entry'][u'ndviStderr']['standard_name'] = 'normalized_difference_vegetation_index standard_error'
#monStderr['variable_entry'][u'ndviStderr']['type'] = 'real'
#monStderr['variable_entry'][u'ndviStderr']['units'] = ''

#%% Coordinate
#%% Frequency
#%% Grid
#%% Grid label

#grid_label['grid_label']['gnNH'] = "data reported on a native grid in the Northern Hemisphere"
#grid_label['grid_label']['gnSH'] = "data reported on a native grid in the Southern Hemisphere"

#%% Institution
tmp = [['institution_id','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/obs4MIPs_institution_id.json']
      ] ;
institution_id = readJsonCreateDict(tmp)
institution_id = institution_id.get('institution_id')

exec(open("./institution_ids.py").read())

tmp = [['grid_label','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_grid_label.json'] ] 

# Fix issues
#==============================================================================
# Example new institution_id entry
#institution_id['institution_id']['NOAA-NCEI'] = 'NOAA\'s National Centers for Environmental Information, Asheville, NC 28801, USA'
#institution_id['institution_id']['RSS'] = 'Remote Sensing Systems, Santa Rosa, CA 95401, USA'
#institution_id['institution_id']['CNES'] = "Centre national d'etudes spatiales"
#institution_id['institution_id']['NASA-GSFC'] = "National Aeronautics and Space Administration, Goddard Space Flight Center"
'''
institution_id['institution_id']['ImperialCollege'] = "Imperial College, London, U.K."
institution_id['institution_id']['UReading'] = "University of Reading, Reading, U.K."
institution_id['institution_id']['UW'] = "University of Washington, USA"
'''
#%% License
license_ = ('Data in this file produced by <Your Centre Name> is licensed under'
            ' a Creative Commons Attribution-ShareAlike 4.0 International License'
            ' (https://creativecommons.org/licenses/). Use of the data must be'
            ' acknowledged following guidelines found at <a URL maintained by you>.'
            ' Further information about this data, including some limitations,'
            ' can be found via <some URL maintained by you>.')

#%% Nominal resolution
#%% Product

#%% Required global attributes - # indicates source
required_global_attributes = [
 'Conventions',
 'activity_id',
 'contact',
 'creation_date',
 'data_specs_version',
 'frequency',
 'grid',
 'grid_label',
 'institution',
 'institution_id',
 'license',
 'nominal_resolution',
 'product',
 'realm',
 'source_id',
 'table_id',
 'tracking_id',
 'variable_id',
 'variant_label'
] ;

#%% Source ID
'''
tmp = [['source_id','https://raw.githubusercontent.com/PCMDI/obs4mips-cmor-tables/master/obs4MIPs_source_id.json']
      ] ;
source_ida = readJsonCreateDict(tmp)
source_ida = source_ida.get('source_id')
print(type(source_ida))
'''
## LOAD EXISTING SOURCE_ID
source_id_orig = json.load(open('../obs4MIPs_source_id.json','r'))
print(source_id_orig.keys())

exec(open("./source_ids.py").read())
print('below exec')

#print(source_id['source_id']['GERB-HR-ED01-1-1'])
#w = sys.stdin.readline()

for s in source_id_orig['source_id'].keys():
  source_id['source_id'][s] = source_id_orig['source_id'][s] 

#print(source_id['source_id']['GERB-HR-ED01-1-1'])

source_id['source_id']['20CR-V2']['institution_id'] = 'NOAA-ESRL-PSD' 
source_id['source_id']['CERES-EBAF-4-0']['institution_id'] = 'NASA-LaRC'
source_id['source_id']['CERES-EBAF-4-1']['institution_id'] = 'NASA-LaRC'
#source_id['source_id']['CERES-EBAF-4-1']['institution_id'] = 'NASA-LaRC--PCMDI'
source_id['source_id']['TropFlux-1-0']['institution_id'] = 'ESSO'
#source_id['source_id']['REMSS-PRW-v07r01']['institution_id'] = 'RSS'
#source_id['source_id']['REMSS-PRW-v07r01']['institution'] = 'RSS data prepared by PCMDI for obs4MIPs'
source_id['source_id']['CMAP-V1902']['institution_id'] = 'NOAA-NCEI'
source_id['source_id']['GPCP-2-3']['institution_id'] = 'NOAA-NCEI'

#print(source_id['source_id']['GERB-HR-ED01-1-1'])
#w = sys.stdin.readline()

# Enter fixes or additions below
'''
source_id = {}
source_id['source_id'] = {}
'''

#####

#pdb.set_trace()
# Fix region non-list
for keyVal in source_id['source_id'].keys():
    print(source_id['source_id'][key]['region'])
    if type(source_id['source_id'][key]['region']) != list:
        source_id['source_id'][key]['region'] = list(source_id['source_id'][key]['region'])

#pdb.set_trace()
#==============================================================================
# Example new source_id entry
#key = 'CMSAF-SARAH-2-0'
#source_id['source_id'][key] = {}
#source_id['source_id'][key]['source_description'] = 'Surface solAr RAdiation data set - Heliosat, based on MVIRI/SEVIRI aboard METEOSAT'
#source_id['source_id'][key]['institution_id'] = 'DWD'
#source_id['source_id'][key]['release_year'] = '2017'
#source_id['source_id'][key]['source_id'] = key
#source_id['source_id'][key]['source_label'] = 'CMSAF-SARAH'
#source_id['source_id'][key]['source_name'] = 'CMSAF SARAH'
#source_id['source_id'][key]['source_type'] = 'satellite_retrieval'
#source_id['source_id'][key]['region'] = list('africa','atlantic_ocean','europe')
#source_id['source_id'][key]['source_variables'] = list('rsds')
#source_id['source_id'][key]['source_version_number'] = '2.0'

# Example rename source_id entry
#key = 'CMSAF-SARAH-2-0'
#source_id['source_id'][key] = {}
#source_id['source_id'][key] = source_id['source_id'].pop('CMSAF-SARAH-2.0')

# Example remove source_id entry
#key = 'CMSAF-SARAH-2.0'
#source_id['source_id'].pop(key)

#key = 'REMSS-PRW-v07r01'
#source_id['source_id'].pop(key)
#key = 'REMSS-PRW-6-6-0'
#source_id['source_id'].pop(key)


# Test invalid chars
#key = 'CMSAF-SARAH-2 0' ; # Tested ".", “_”, “(“, “)”, “/”, and " "
#source_id['source_id'][key] = {}
#source_id['source_id'][key] = source_id['source_id'].pop('CMSAF-SARAH-2-0')

## ADDING obs4MIPs1.0
###################################################################################
'''
coordinate['plev37_ERA5'] = {}
coordinate['plev37_ERA5']['axis'] = 'Z'
coordinate['plev37_ERA5']['out_name'] = 'plev'
coordinate['plev37_ERA5']['standard_name']='air_pressure'
coordinate['plev37_ERA5']['long_name']='pressure'
coordinate['plev37_ERA5']['stored_direction']='decreasing'
coordinate['plev37_ERA5']['positive']='down'
coordinate['plev37_ERA5']['units']='Pa'
coordinate['plev37_ERA5']['bounds_values']= ''
coordinate['plev37_ERA5']['climatology']= ''
coordinate['plev37_ERA5']['generic_level_name']= ''
coordinate['plev37_ERA5']['must_have_bounds']= 'no'
coordinate['plev37_ERA5']['forumula']= ''
coordinate['plev37_ERA5']["requested_bounds"]=""
coordinate['plev37_ERA5']["standard_name"]="air_pressure"
coordinate['plev37_ERA5']["stored_direction"]="decreasing"
coordinate['plev37_ERA5']["tolerance"]=""
coordinate['plev37_ERA5']["type"]="double"
coordinate['plev37_ERA5']["units"]="Pa"
coordinate['plev37_ERA5']["valid_max"]=""
coordinate['plev37_ERA5']["valid_min"]=""
coordinate['plev37_ERA5']["value"]=""
coordinate['plev37_ERA5']["z_bounds_factors"]=""
coordinate['plev37_ERA5']["z_factors"]=""
coordinate['plev37_ERA5']['requested'] = [ "100000.", "97500.", "95000.", "92500.", "90000.", "87500.", "85000.", "82500.", "80000.", "77500.", "75000.", "70000.", "65000.", "60000.", "55000.", "50000.", "45000.", "40000.", "35000.", "30000.", "25000.", "22500.", "20000.", "17500.", "15000.", "12500.", "10000.", "7000.", "5000.", "3000.", "2000.", "1000.", "700.", "500.", "300.", "200.", "100."]
'''

#%% Source type
source_type = {}
source_type['gridded_insitu'] = 'gridded product based on measurements collected from in-situ instruments'
source_type['reanalysis'] = 'gridded product generated from a model reanalysis based on in-situ instruments and possibly satellite measurements'
source_type['satellite_blended'] = 'gridded product based on both in-situ instruments and satellite measurements'
source_type['satellite_retrieval'] = 'gridded product based on satellite measurements'

#%% Table ID
table_id = [
  'obs4MIPs_Amon',
  'obs4MIPs_Aday',
  'obs4MIPs_A3hr',
  'obs4MIPs_Lmon',
  'obs4MIPs_Omon',
  'obs4MIPs_SImon',
  'obs4MIPs_fx'
] ;

#%% Validate entries
def entryCheck(entry,search=re.compile(r'[^a-zA-Z0-9-]').search):
    return not bool(search(entry))

# source_id
for key in source_id['source_id'].keys():
    # Validate source_id format
    if not entryCheck(key):
        print('Invalid source_id format for entry:',key,'- aborting')
        sys.exit()
    # Sort variable entries
    vals = source_id['source_id'][key]['source_variables']
    if not isinstance(vals,list):
        vals = list(vals); vals.sort()
    else:
        vals.sort()
    # Validate source_label format
    val = source_id['source_id'][key]['source_label']
    if not entryCheck(key):
        print('Invalid source_label format for entry:',key,'- aborting')
        sys.exit()
    # Validate source_type
    val = source_id['source_id'][key]['source_type']
    if val not in source_type:
        print('Invalid source_type for entry:',key,'- aborting')
        sys.exit()
    # Validate region
    vals = source_id['source_id'][key]['region']
#   for val in vals:
#       if val not in eval(region)['region']['region']:  # region:
#           print('Invalid region for entry:',key,'- aborting')
#           sys.exit()



    # Validate product   
#   vals = source_id['source_id'][key]['product']
#   for val in vals:
#       if val not in product:
#           print('Invalid product for entry:',key,'- aborting')
#           sys.exit()


#%% Write variables to files
for jsonName in masterTargets:
    # Clean experiment formats
    if jsonName in []:   #['coordinate','grids']: #,'Amon','Lmon','Omon','SImon']:
        dictToClean = eval(jsonName)
        for key, value1 in dictToClean.iteritems():
            for value2 in value1.iteritems():
                string = dictToClean[key][value2[0]]
                if not isinstance(string, list) and not isinstance(string, dict):
                    string = string.strip() ; # Remove trailing whitespace
                    string = string.strip(',.') ; # Remove trailing characters
                    string = string.replace(' + ',' and ')  ; # Replace +
                    string = string.replace(' & ',' and ')  ; # Replace +
                    string = string.replace('   ',' ') ; # Replace '  ', '   '
                    string = string.replace('  ',' ') ; # Replace '  ', '   '
                    string = string.replace('anthro ','anthropogenic ') ; # Replace anthro
                    string = string.replace('decidous','deciduous') ; # Replace decidous
                dictToClean[key][value2[0]] = string
        vars()[jsonName] = dictToClean
    # Write file
    if jsonName in ['Aday','A3hr','A6hr','Oday','SIday','Amon','Lmon','Omon','SImon',
                    'coordinate','formula_terms','fx','grids','monNobs',
                    'monStderr']:
        outFile = ''.join(['../Tables/obs4MIPs_',jsonName,'.json'])
    elif jsonName == 'license_':
        outFile = ''.join(['../obs4MIPs_license.json'])
    else:
        outFile = ''.join(['../obs4MIPs_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print('File existing, purging:',outFile)
        os.remove(outFile)
    if not os.path.exists('../Tables'):
        os.mkdir('../Tables')
    # Create host dictionary
    if jsonName == 'license_':
        jsonDict = {}
        jsonDict[jsonName.replace('_','')] = eval(jsonName)

    elif jsonName not in ['coordinate','formula_terms','fx','grids',
                          'institution_id','source_id','Aday','Amon','A3hr','Lmon',
                          'Omon','SImon']: #,'product','realm','region']:
        jsonDict = {}
        jsonDict[jsonName] = eval(jsonName)

    else:
        jsonDict = eval(jsonName)

    fH = open(outFile,'w')
    if jsonName in ['formula_terms','grids','coordinate']: jsonDict = eval(jsonDict)
    if jsonName in ['frequency']: jsonDict['frequency']  = eval(jsonDict['frequency'])
    if jsonName in ['grid_label']: jsonDict['grid_label']  = eval(jsonDict['grid_label'])
    if jsonName in ['nominal_resolution']: jsonDict['nominal_resolution']  = eval(jsonDict['nominal_resolution'])
    if jsonName in ['product']: jsonDict['product']  = eval(jsonDict['product'])

    if jsonName in ['product']: 
      if isinstance(jsonDict[jsonName][jsonName],list):
       try:
        jsonDict[jsonName] = jsonDict[jsonName][jsonName]
       except:
        pass

    if jsonName in ['realm','region']: 
      jsonDict[jsonName]  = eval(jsonDict[jsonName])
      try:
       if isinstance(jsonDict[jsonName][jsonName],list):
        jsonDict[jsonName] = jsonDict[jsonName][jsonName]  
      except:
       pass
      try:
       if isinstance(jsonDict[jsonName][jsonName][jsonName],list):
        jsonDict[jsonName] = jsonDict[jsonName][jsonName][jsonName]   
      except:
       pass
      print(jsonName,' ---------------- ', jsonDict[jsonName])

      if jsonName in ['yyyycoordznate']:
        jsonDict['coordinate']['plev37_ERA5'] = {}
        jsonDict['coordinate']['plev37_ERA5']['axis'] = 'Z'
        jsonDict['coordinate']['plev37_ERA5']['out_name'] = 'plev'
        jsonDict['coordinate']['plev37_ERA5']['standard_name']='air_pressure'
        jsonDict['coordinate']['plev37_ERA5']['long_name']='pressure'
        jsonDict['coordinate']['plev37_ERA5']['stored_direction']='decreasing'
        jsonDict['coordinate']['plev37_ERA5']['positive']='down'
        jsonDict['coordinate']['plev37_ERA5']['units']='Pa'
        jsonDict['coordinate']['plev37_ERA5']['bounds_values']= ''
        jsonDict['coordinate']['plev37_ERA5']['climatology']= ''
        jsonDict['coordinate']['plev37_ERA5']['generic_level_name']= ''
        jsonDict['coordinate']['plev37_ERA5']['must_have_bounds']= 'no'
        jsonDict['coordinate']['plev37_ERA5']['forumula']= ''
        jsonDict['coordinate']['plev37_ERA5']["requested_bounds"]=""
        jsonDict['coordinate']['plev37_ERA5']["standard_name"]="air_pressure"
        jsonDict['coordinate']['plev37_ERA5']["stored_direction"]="decreasing"
        jsonDict['coordinate']['plev37_ERA5']["tolerance"]=""
        jsonDict['coordinate']['plev37_ERA5']["type"]="double"
        jsonDict['coordinate']['plev37_ERA5']["units"]="Pa"
        jsonDict['coordinate']['plev37_ERA5']["valid_max"]=""
        jsonDict['coordinate']['plev37_ERA5']["valid_min"]=""
        jsonDict['coordinate']['plev37_ERA5']["value"]=""
        jsonDict['coordinate']['plev37_ERA5']["z_bounds_factors"]=""
        jsonDict['coordinate']['plev37_ERA5']["z_factors"]=""
        jsonDict['coordinate']['plev37_ERA5']['requested'] = [ "100000.", "97500.", "95000.", "92500.", "90000.", "87500.", "85000.", "82500.", "80000.", "77500.", "75000.", "70000.", "65000.", "60000.", "55000.", "50000.", "45000.", "40000.", "35000.", "30000.", "25000.", "22500.", "20000.", "17500.", "15000.", "12500.", "10000.", "7000.", "5000.", "3000.", "2000.", "1000.", "700.", "500.", "300.", "200.", "100."]
        print('coord dic is '), jsonDict.keys()


#   if jsonName in ['region']: jsonDict['region']  = eval(jsonDict['region'])
#   print('starting ', fH,' ', jsonDict.keys(),' ' ,type(jsonDict))
    print('starting ', fH,' ', type(jsonDict))   #,jsonDict)
#   json.dump(jsonDict,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    json.dump(jsonDict,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'))

#   print(fH,' ','DONE------------------')

    fH.close()

del(jsonName,outFile) ; gc.collect()

# Validate - only necessary if files are not written by json module

#%% Generate files for download and use
demoPath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-2]),'demo')
outPath = os.path.join(demoPath,'Tables')
if os.path.exists(outPath):
    shutil.rmtree(outPath) ; # Purge all existing
    os.makedirs(outPath)
else:
    os.makedirs(outPath)
os.chdir(demoPath)

# Integrate all controlled vocabularies (CVs) into master file - create obs4MIPs_CV.json
# List all local files
inputJson = ['frequency','grid_label','institution_id','license',
             'nominal_resolution','product','realm','region',
             'required_global_attributes','source_id','source_type','table_id', # These are controlled vocabs
             'coordinate','grids','formula_terms', # These are not controlled vocabs - rather lookup tables for CMOR
             'Aday','Amon','Lmon','Omon','SImon','fx' # Update/add if new tables are generated
            ]
tableList = ['Aday','A3hr','A6hr','Oday','SIday','Amon','Lmon','Omon','SImon','coordinate',
             'formula_terms','fx','grids','monNobs','monStderr']

# Load dictionaries from local files
CVJsonList = copy.deepcopy(inputJson)
#CVJsonList.remove('coordinate')
CVJsonList.remove('grids')
CVJsonList.remove('formula_terms')
CVJsonList.remove('Aday')
CVJsonList.remove('Amon')
CVJsonList.remove('Lmon')
CVJsonList.remove('Omon')
CVJsonList.remove('SImon')
CVJsonList.remove('fx')
for count,CV in enumerate(inputJson):
    if CV in tableList:
        path = '../Tables/'
    else:
        path = '../'
    vars()[CV] = json.load(open(''.join([path,'obs4MIPs_',CV,'.json'])))

#       vars()[table[0]] = json.load(open('tmp.json','r'))


# Build CV master dictionary


obs4MIPs_CV = {}
obs4MIPs_CV['CV'] = {}
for count,CV in enumerate(CVJsonList):
#   if CV == 'institution':
#      obs4MIPs_CV['CV']['institution'] = source_id['institude_id']

    # Create source entry from source_id
    if CV == 'source_idd': 
      obs4MIPs_CV['CV']['source_id'] = source_id['source_id'] 

      for s in obs4MIPs_CV['CV']['source_id'].keys():
        obs4MIPs_CV['CV']['source_id'][s]['source'] = obs4MIPs_CV['CV']['source_id'][s]['source_description'] 

    if CV == 'source_id':
        source_id_ = source_id['source_id']
        obs4MIPs_CV['CV']['source_id'] = {}
        for key,values in source_id_.items():
            obs4MIPs_CV['CV']['source_id'][key] = {}
            string = ''.join([source_id_[key]['source_label'],' ',
                              source_id_[key]['source_version_number'],' (',
                              source_id_[key]['release_year'],'): ',
                              source_id_[key]['source_description']])
            obs4MIPs_CV['CV']['source_id'][key]['source_label'] = values['source_label']
            obs4MIPs_CV['CV']['source_id'][key]['source_type'] = values['source_type']
            obs4MIPs_CV['CV']['source_id'][key]['source_version_number'] = values['source_version_number']
            obs4MIPs_CV['CV']['source_id'][key]['region'] = ', '.join(str(a) for a in values['region'])
            obs4MIPs_CV['CV']['source_id'][key]['source'] = string
            obs4MIPs_CV['CV']['source_id'][key].pop('source_label',None)

    # Rewrite table names
    elif CV == 'table_id':
        obs4MIPs_CV['CV']['table_id'] = []
        for value in table_id['table_id']:
            obs4MIPs_CV['CV']['table_id'].append(value)
    # Else all other CVs
    elif CV not in tableList:
        print('CV line 725 is ', CV)
        obs4MIPs_CV['CV'].update(eval(CV))
# Add static entries to obs4MIPs_CV.json
obs4MIPs_CV['CV']['activity_id'] = 'obs4MIPs'

# Dynamically update "data_specs_version": "2.0.0", in rssSsmiPrw-input.json
#print os.getcwd()
#versionInfo = getGitInfo('../demo/rssSsmiPrw-input.json')
#tagTxt = versionInfo[2]
#tagInd = tagTxt.find('(')
#tagTxt = tagTxt[0:tagInd].replace('latest_tagPoint: ','').strip()

# Write demo obs4MIPs_CV.json
if os.path.exists('Tables/obs4MIPs_CV.json'):
    print('File existing, purging:','obs4MIPs_CV.json')
    os.remove('Tables/obs4MIPs_CV.json')
fH = open('Tables/obs4MIPs_CV.json','w')
#json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'))

fH.close()

# Write ../Tables obs4MIPs_CV.json
if os.path.exists('../Tables/obs4MIPs_CV.json'):
    print('File existing, purging:','obs4MIPs_CV.json')
    os.remove('../Tables/obs4MIPs_CV.json')
fH = open('../Tables/obs4MIPs_CV.json','w')
#json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'))
fH.close()


''' NOT SURE THE THIS IS NEEDED 
# Loop and write all other files
os.chdir('Tables')
#tableList.extend(lookupList)
for count,CV in enumerate(tableList):
    outFile = ''.join(['obs4MIPs_',CV,'.json'])
    if os.path.exists(outFile):
        print('File existing, purging:',outFile)
        os.remove(outFile)
    fH = open(outFile,'w')
#   json.dump(eval(CV),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    json.dump(eval(CV),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'))
    fH.close()
'''
# Cleanup

del(coordinate,count,formula_terms,frequency,grid_label,homePath,institution_id, nominal_resolution,obs4MIPs_CV,product,realm,inputJson,tableList, required_global_attributes,table_id) 

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 16:11:44 2016

Paul J. Durack 12th July 2016

This script generates all json files residing this this subdirectory

PJD 12 Jul 2016     - Started
PJD 13 Jul 2016     - Updated to download existing tables
PJD 14 Jul 2016     - Successfully loaded dictionaries
PJD 15 Jul 2016     - Tables successfully created, coordinates from CMIP6_CVs
PJD 18 Jul 2016     - Generate CVs and tables from CMIP6_CVs and CMIP6-cmor-tables
PJD 19 Jul 2016     - Remove activity_id - no longer in A/O/etc tables
PJD 20 Jul 2016     - Removed target_mip from required_global_attributes
PJD 20 Jul 2016     - Removed source_id
PJD 20 Jul 2016     - Added fx table_id
PJD 20 Jul 2016     - Added readJsonCreateDict function
PJD 20 Jul 2016     - Removed modeling_realm from all variable_entry entries
PJD 27 Sep 2016     - Updated to deal with new upstream data formats
PJD 27 Sep 2016     - Updated tables to "01.beta.30" -> "01.beta.32"
PJD 27 Sep 2016     - Update jsons to include 'identifier' dictionary name (following CMIP6_CVs)
PJD 27 Sep 2016     - Add NOAA-NCEI to institution_id https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/8
PJD 27 Sep 2016     - Correct RSS zip
PJD 28 Sep 2016     - Correct missing 'generic_levels' in Amon table
PJD 29 Sep 2016     - Added ttbr (NOAA-NCEI; Jim Baird [JimBiardCics]) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/14
PJD 30 Jan 2017     - Updated to latest cmip6-cmor-tables and CMIP6_CVs
PJD 30 Jan 2017     - Remove header from coordinate
PJD  3 Mar 2017     - Fixed issue with 'grids' subdict in obs4MIPs_grids.json https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/22
PJD  3 Mar 2017     - Add ndvi to LMon table https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/16
PJD  3 Mar 2017     - Add fapar to LMon table https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/15
PJD 29 Mar 2017     - Correct required_global_attribute grids -> grid
PJG 05 Apr 2017     - Added daily atm table
                    - TODO:

@author: durack1
"""

#%% Import statements
import gc,json,os,ssl,time
from durolib import readJsonCreateDict

#%% Determine path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/' ; # Linux
#homePath = '/sync/git/obs4MIPs-cmor-tables/src' ; # OS-X
os.chdir(homePath)

#%% Create urllib2 context to deal with lab/LLNL web certificates
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% List target tables
masterTargets = [
 'Amon',
 'Lmon',
 'Omon',
 'SImon',
 'fx',
 'Aday',
 'coordinate',
 'frequency',
 'grid_label',
 'grids',
 'institution_id',
 'mip_era',
 'nominal_resolution',
 'product',
 'realm',
 'region',
 'required_global_attributes',
 'table_id'
 ] ;

#%% Tables
tableSource = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_coordinate.json'],
 ['frequency','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_frequency.json'],
 ['fx','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_fx.json'],
 ['grid_label','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_grid_label.json'],
 ['grids','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_grids.json'],
 ['nominal_resolution','https://raw.githubusercontent.com/WCRP-CMIP/CMIP6_CVs/master/CMIP6_nominal_resolution.json'],
 ['Amon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Amon.json'],
 ['Lmon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Lmon.json'],
 ['Omon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_Omon.json'],
 ['SImon','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_SImon.json'],
 ['Aday','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_day.json'],
 ] ;

#%% Loop through tables and create in-memory objects
# Loop through tableSource and create output tables
tmp = readJsonCreateDict(tableSource)
for count,table in enumerate(tmp.keys()):
    print 'table:', table
    if table in ['frequency','grid_label','nominal_resolution']:
        vars()[table] = tmp[table].get(table)
    else:
        vars()[table] = tmp[table]
del(tmp,count,table) ; gc.collect()

# Cleanup by extracting only variable lists
for count2,table in enumerate(tableSource):
    tableName = table[0]
    print 'tableName:',tableName
    #print eval(tableName)
    if tableName in ['coordinate','frequency','grid_label','nominal_resolution']:
        continue
    else:
        eval(tableName)['Header']['table_date'] = time.strftime('%d %B %Y')
        if 'baseURL' in eval(tableName)['Header'].keys():
            del(eval(tableName)['Header']['baseURL']) ; # Remove spurious entry

# Cleanup realms
Amon['Header']['realm']     = 'atmos'
Lmon['Header']['realm']     = 'land'
Omon['Header']['realm']     = 'ocean'
SImon['Header']['realm']    = 'seaIce'
fx['Header']['realm']       = 'fx'
#Aday['Header']['realm']     = 'atmos'

# Clean out modeling_realm
for jsonName in ['Amon','Lmon','Omon','SImon']:  #,'Aday']:
    dictToClean = eval(jsonName)
    for key, value in dictToClean.iteritems():
        if key == 'Header':
            continue
        for key1,value1 in value.iteritems():
            if 'modeling_realm' in dictToClean[key][key1].keys():
                dictToClean[key][key1].pop('modeling_realm')

# Add new variables
# Variable sponsor - NOAA-NCEI; Jim Baird (JimBiardCics)
Amon['variable_entry'][u'ttbr'] = {}
Amon['variable_entry']['ttbr']['cell_measures'] = 'time: mean'
Amon['variable_entry']['ttbr']['cell_methods'] = 'area: areacella'
Amon['variable_entry']['ttbr']['comment'] = ''
Amon['variable_entry']['ttbr']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['ttbr']['long_name'] = 'Top of Atmosphere Brightness Temperature'
Amon['variable_entry']['ttbr']['ok_max_mean_abs'] = ''
Amon['variable_entry']['ttbr']['ok_min_mean_abs'] = ''
Amon['variable_entry']['ttbr']['out_name'] = 'ttbr'
Amon['variable_entry']['ttbr']['positive'] = 'time: mean'
Amon['variable_entry']['ttbr']['standard_name'] = 'toa_brightness_temperature'
Amon['variable_entry']['ttbr']['type'] = 'real'
Amon['variable_entry']['ttbr']['units'] = 'K'
Amon['variable_entry']['ttbr']['valid_max'] = '375.0'
Amon['variable_entry']['ttbr']['valid_min'] = '140.0'
# Variable sponsor - NOAA-NCEI; Jim Baird (JimBiardCics) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/16
Lmon['variable_entry'][u'ndvi'] = {}
Lmon['variable_entry']['ndvi']['cell_measures'] = 'time: mean area: mean where land'
Lmon['variable_entry']['ndvi']['cell_methods'] = 'area: areacella'
Lmon['variable_entry']['ndvi']['comment'] = ''
Lmon['variable_entry']['ndvi']['dimensions'] = 'longitude latitude time'
Lmon['variable_entry']['ndvi']['long_name'] = 'Normalized Difference Vegetation Index'
Lmon['variable_entry']['ndvi']['ok_max_mean_abs'] = ''
Lmon['variable_entry']['ndvi']['ok_min_mean_abs'] = ''
Lmon['variable_entry']['ndvi']['out_name'] = 'ndvi'
Lmon['variable_entry']['ndvi']['positive'] = ''
Lmon['variable_entry']['ndvi']['standard_name'] = 'normalized_difference_vegetation_index'
Lmon['variable_entry']['ndvi']['type'] = 'real'
Lmon['variable_entry']['ndvi']['units'] = '1'
Lmon['variable_entry']['ndvi']['valid_max'] = '1.0'
Lmon['variable_entry']['ndvi']['valid_min'] = '-0.1'
# Variable sponsor - NOAA-NCEI; Jim Baird (JimBiardCics) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/15
Lmon['variable_entry'][u'fapar'] = {}
Lmon['variable_entry']['fapar']['cell_measures'] = 'time: mean area: mean where land'
Lmon['variable_entry']['fapar']['cell_methods'] = 'area: areacella'
Lmon['variable_entry']['fapar']['comment'] = 'The fraction of incoming solar radiation in the photosynthetically active radiation spectral region that is absorbed by a vegetation canopy.'
Lmon['variable_entry']['fapar']['dimensions'] = 'longitude latitude time'
Lmon['variable_entry']['fapar']['long_name'] = 'Fraction of Absorbed Photosynthetically Active Radiation'
Lmon['variable_entry']['fapar']['ok_max_mean_abs'] = ''
Lmon['variable_entry']['fapar']['ok_min_mean_abs'] = ''
Lmon['variable_entry']['fapar']['out_name'] = 'fapar'
Lmon['variable_entry']['fapar']['positive'] = ''
Lmon['variable_entry']['fapar']['standard_name'] = 'fraction_of_surface_downwelling_photosynthetic_radiative_flux_absorbed_by_vegetation'
Lmon['variable_entry']['fapar']['type'] = 'real'
Lmon['variable_entry']['fapar']['units'] = '1'
Lmon['variable_entry']['fapar']['valid_max'] = '1.0'
Lmon['variable_entry']['fapar']['valid_min'] = '0.0'

#%% Coordinate

#%% Frequencies

#%% Grid

#%% Grid labels

#%% Institutions
tmp = [['institution_id','https://raw.githubusercontent.com/PCMDI/obs4mips-cmor-tables/master/obs4MIPs_institution_id.json']
      ] ;
institution_id = readJsonCreateDict(tmp)
institution_id = institution_id.get('institution_id')

# Fix issues
#==============================================================================
# Example new experiment_id entry
#institution_id['institution_id']['NOAA-NCEI'] = 'NOAA\'s National Centers for Environmental Information, Asheville, NC 28801, USA'
#institution_id['institution_id']['RSS'] = 'Remote Sensing Systems, Santa Rosa, CA 95401, USA'

#%% Mip era
mip_era = ['CMIP6'] ;

#%% Nominal resolution

#%% Product
product = [
 'composite',
 'remote-sensed',
 'satellite',
 'surface-gridded-insitu',
 'surface-radar'
 ] ;

#%% Realms
realm = [
 'aerosol',
 'atmos',
 'atmosChem',
 'land',
 'landIce',
 'ocean',
 'ocnBgchem',
 'seaIce'
 ] ;

#%% Regions (taken from http://cfconventions.org/Data/cf-standard-names/docs/standardized-region-names.html) 
region = ['africa', 'antarctica', 'arabian_sea', 'aral_sea', 'arctic_ocean', 'asia', 'atlantic_ocean', 'australia', 'baltic_sea', 'barents_opening', 'barents_sea', 'beaufort_sea', 'bellingshausen_sea', 'bering_sea', 'bering_strait', 'black_sea', 'canadian_archipelago', 'caribbean_sea', 'caspian_sea', 'central_america', 'chukchi_sea', 'contiguous_united_states', 'denmark_strait', 'drake_passage', 'east_china_sea', 'english_channel', 'eurasia', 'europe', 'faroe_scotland_channel', 'florida_bahamas_strait', 'fram_strait', 'global', 'global_land', 'global_ocean', 'great_lakes', 'greenland', 'gulf_of_alaska', 'gulf_of_mexico', 'hudson_bay', 'iceland_faroe_channel', 'indian_ocean', 'indonesian_throughflow', 'indo_pacific_ocean', 'irish_sea', 'lake_baykal', 'lake_chad', 'lake_malawi', 'lake_tanganyika', 'lake_victoria', 'mediterranean_sea', 'mozambique_channel', 'north_america', 'north_sea', 'norwegian_sea', 'pacific_equatorial_undercurrent', 'pacific_ocean', 'persian_gulf', 'red_sea', 'ross_sea', 'sea_of_japan', 'sea_of_okhotsk', 'south_america', 'south_china_sea', 'southern_ocean', 'taiwan_luzon_straits', 'weddell_sea', 'windward_passage', 'yellow_sea']


#%% Required global attributes
required_global_attributes = [
 'activity_id',
 'Conventions',
 'creation_date',
 'dataset_version_number',
 'further_info_url',
 'frequency',
 'grid',
 'grid_label',
 'institution_id',
 'license',
 'mip_era',
 'nominal_resolution',
 'product',
 'realm',
 'region',
 'source_id',
 'table_id',
 'tracking_id',
 'variable_id'
 ];

#%% Table IDs
table_id = ['Amon', 'Lmon', 'Omon', 'SImon', 'fx','Aday'] ;

#%% Write variables to files
for jsonName in masterTargets:
    # Clean experiment formats
    if jsonName in ['coordinate','grid']: #,'Amon','Lmon','Omon','SImon']:
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
                    string = string.replace('anthro ','anthropogenic ') ; # Replace anthro
                    string = string.replace('decidous','deciduous') ; # Replace decidous
                    string = string.replace('  ',' ') ; # Replace '  ', '   '
                dictToClean[key][value2[0]] = string
        vars()[jsonName] = dictToClean
    # Write file
    if jsonName in ['Amon','Lmon','Omon','SImon','fx','Aday']:
        outFile = ''.join(['../Tables/obs4MIPs_',jsonName,'.json'])
    else:
        outFile = ''.join(['../obs4MIPs_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    if not os.path.exists('../Tables'):
        os.mkdir('../Tables')
    # Create host dictionary
    if jsonName not in ['coordinate','fx','grids','institution_id','Amon','Lmon','Omon','SImon','Aday']:
        jsonDict = {}
        jsonDict[jsonName] = eval(jsonName)
    else:
        jsonDict = eval(jsonName)
    fH = open(outFile,'w')
    json.dump(jsonDict,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

del(jsonName,outFile) ; gc.collect()

# Validate - only necessary if files are not written by json module

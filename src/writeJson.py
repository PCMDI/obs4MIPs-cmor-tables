#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 16:11:44 2016

Paul J. Durack 12th July 2016

This script generates all json files residing in this subdirectory

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
PJD 11 May 2017     - Added formula_terms; Updated upstream; corrected product to 'observations'
PJD 19 Jun 2017     - Update to deal with CMOR 3.2.4 and tables v01.00.11
PJD 21 Jun 2017     - Updated PR #46 by Funkensieper/DWD to add new Amon variables https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
PJD 28 Jun 2017     - Rerun to fix formula_terms to work with CMOR 3.2.4 https://github.com/PCMDI/cmor/issues/198
PJD 17 Jul 2017     - Implement new CVs in obs4MIPs Data Specifications (ODS) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/40
PJD 17 Jul 2017     - Updated tableNames to deal with 3.2.5 hard codings
                    - TODO: Create demo3 which simplifies user experience to downloading pre-packaged json zip archive,
                            unzipping contents, tweaking user input json and running cmor

@author: durack1
"""

#%% Import statements
import gc,json,os,shutil,ssl,subprocess,time
from durolib import readJsonCreateDict

#%% Determine path
homePath = os.path.join('/','/'.join(os.path.realpath(__file__).split('/')[0:-1]))
#homePath = '/export/durack1/git/obs4MIPs-cmor-tables/' ; # Linux
#homePath = '/sync/git/obs4MIPs-cmor-tables/src' ; # OS-X
#os.chdir(homePath)

#%% Create urllib2 context to deal with lab/LLNL web certificates
ctx                 = ssl.create_default_context()
ctx.check_hostname  = False
ctx.verify_mode     = ssl.CERT_NONE

#%% List target tables
masterTargets = [
 'Aday',
 'Amon',
 'Lmon',
 'Omon',
 'SImon',
 'fx',
 'coordinate',
 'formula_terms',
 'frequency',
 'grid_label',
 'grids',
 'institution_id',
 'license_',
 'mip_era',
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
tableSource = [
 ['coordinate','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_coordinate.json'],
 ['formula_terms','https://raw.githubusercontent.com/PCMDI/cmip6-cmor-tables/master/Tables/CMIP6_formula_terms.json'],
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
    if tableName in ['coordinate','formula_terms','frequency','grid_label','nominal_resolution']:
        continue
    else:
        eval(tableName)['Header']['Conventions'] = 'CF-1.7 ODS-2.0' ; # Update "Conventions": "CF-1.7 CMIP-6.0"
        eval(tableName)['Header']['table_date'] = time.strftime('%d %B %Y')
        eval(tableName)['Header']['product'] = 'observations'
        #eval(tableName)['Header']['table_id'] = ''.join(['Table obs4MIPs_',tableName])
        eval(tableName)['Header']['table_id'] = tableName ; # Added as kludge for CMOR3.2.5
#            ! Valid values must match the regular expression:
#            ! 	["^Aday$" "^Amon$" "^Lmon$" "^Omon$" "^SImon$" "^fx$"  ...]
        if 'baseURL' in eval(tableName)['Header'].keys():
            del(eval(tableName)['Header']['baseURL']) ; # Remove spurious entry

# Cleanup realms
Amon['Header']['realm']     = 'atmos'
Lmon['Header']['realm']     = 'land'
Omon['Header']['realm']     = 'ocean'
SImon['Header']['realm']    = 'seaIce'
fx['Header']['realm']       = 'fx'
#Aday['Header']['table_id']  = 'Table obs4MIPs_Aday' ; # Cleanup from upstream
Aday['Header']['table_id']  = 'Aday' ; # Added as kludge for CMOR3.2.5

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
Amon['variable_entry']['ttbr']['frequency'] = 'mon'
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
Lmon['variable_entry']['ndvi']['frequency'] = 'mon'
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
Lmon['variable_entry']['fapar']['frequency'] = 'mon'
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
# DWD cloud variables (CM SAF CLARA & ESA Cloud_CCI) ...
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clCCI'] = {}
Amon['variable_entry']['clCCI']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clCCI']['cell_methods'] = 'area: time: mean'
Amon['variable_entry']['clCCI']['comment'] = 'Percentage cloud cover in optical depth categories.'
Amon['variable_entry']['clCCI']['dimensions'] = 'longitude latitude plev7c tau time'
Amon['variable_entry']['clCCI']['frequency'] = 'mon'
Amon['variable_entry']['clCCI']['long_name'] = 'CCI Cloud Area Fraction'
Amon['variable_entry']['clCCI']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clCCI']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clCCI']['out_name'] = 'clCCI'
Amon['variable_entry']['clCCI']['positive'] = ''
Amon['variable_entry']['clCCI']['standard_name'] = 'cloud_area_fraction_in_atmosphere_layer'
Amon['variable_entry']['clCCI']['type'] = 'real'
Amon['variable_entry']['clCCI']['units'] = '%'
Amon['variable_entry']['clCCI']['valid_max'] = ''
Amon['variable_entry']['clCCI']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clCLARA'] = {}
Amon['variable_entry']['clCLARA']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clCLARA']['cell_methods'] = 'area: mean time: mean'
Amon['variable_entry']['clCLARA']['comment'] = 'Percentage cloud cover in optical depth categories.'
Amon['variable_entry']['clCLARA']['dimensions'] = 'longitude latitude plev7c tau time'
Amon['variable_entry']['clCLARA']['frequency'] = 'mon'
Amon['variable_entry']['clCLARA']['long_name'] = 'CLARA Cloud Area Fraction'
Amon['variable_entry']['clCLARA']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clCLARA']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clCLARA']['out_name'] = 'clCLARA'
Amon['variable_entry']['clCLARA']['positive'] = ''
Amon['variable_entry']['clCLARA']['standard_name'] = 'cloud_area_fraction_in_atmosphere_layer'
Amon['variable_entry']['clCLARA']['type'] = 'real'
Amon['variable_entry']['clCLARA']['units'] = '%'
Amon['variable_entry']['clCLARA']['valid_max'] = ''
Amon['variable_entry']['clCLARA']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'cltCCI'] = {}
Amon['variable_entry']['cltCCI']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['cltCCI']['cell_methods'] = 'area: time: mean'
Amon['variable_entry']['cltCCI']['comment'] = 'Total cloud area fraction for the whole atmospheric column, as seen from the surface or the top of the atmosphere. Includes both large-scale and convective cloud.'
Amon['variable_entry']['cltCCI']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['cltCCI']['frequency'] = 'mon'
Amon['variable_entry']['cltCCI']['long_name'] = 'CCI Total Cloud Fraction'
Amon['variable_entry']['cltCCI']['ok_max_mean_abs'] = ''
Amon['variable_entry']['cltCCI']['ok_min_mean_abs'] = ''
Amon['variable_entry']['cltCCI']['out_name'] = 'cltCCI'
Amon['variable_entry']['cltCCI']['positive'] = ''
Amon['variable_entry']['cltCCI']['standard_name'] = 'cloud_area_fraction'
Amon['variable_entry']['cltCCI']['type'] = 'real'
Amon['variable_entry']['cltCCI']['units'] = '%'
Amon['variable_entry']['cltCCI']['valid_max'] = ''
Amon['variable_entry']['cltCCI']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'cltCLARA'] = {}
Amon['variable_entry']['cltCLARA']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['cltCLARA']['cell_methods'] = 'area: mean time: mean'
Amon['variable_entry']['cltCLARA']['comment'] = 'Total cloud area fraction for the whole atmospheric column, as seen from the surface or the top of the atmosphere. Includes both large-scale and convective cloud.'
Amon['variable_entry']['cltCLARA']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['cltCLARA']['frequency'] = 'mon'
Amon['variable_entry']['cltCLARA']['long_name'] = 'CLARA Total Cloud Fraction'
Amon['variable_entry']['cltCLARA']['ok_max_mean_abs'] = ''
Amon['variable_entry']['cltCLARA']['ok_min_mean_abs'] = ''
Amon['variable_entry']['cltCLARA']['out_name'] = 'cltCLARA'
Amon['variable_entry']['cltCLARA']['positive'] = ''
Amon['variable_entry']['cltCLARA']['standard_name'] = 'cloud_area_fraction'
Amon['variable_entry']['cltCLARA']['type'] = 'real'
Amon['variable_entry']['cltCLARA']['units'] = '%'
Amon['variable_entry']['cltCLARA']['valid_max'] = ''
Amon['variable_entry']['cltCLARA']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clwCCI'] = {}
Amon['variable_entry']['clwCCI']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clwCCI']['cell_methods'] = 'area: time: mean'
Amon['variable_entry']['clwCCI']['comment'] = 'Percentage liquid cloud cover in optical depth categories.'
Amon['variable_entry']['clwCCI']['dimensions'] = 'longitude latitude plev7c tau time'
Amon['variable_entry']['clwCCI']['frequency'] = 'mon'
Amon['variable_entry']['clwCCI']['long_name'] = 'CCI Liquid Cloud Area Fraction'
Amon['variable_entry']['clwCCI']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clwCCI']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clwCCI']['out_name'] = 'clwCCI'
Amon['variable_entry']['clwCCI']['positive'] = ''
Amon['variable_entry']['clwCCI']['standard_name'] = 'liquid_water_cloud_area_fraction_in_atmosphere_layer'
Amon['variable_entry']['clwCCI']['type'] = 'real'
Amon['variable_entry']['clwCCI']['units'] = '%'
Amon['variable_entry']['clwCCI']['valid_max'] = ''
Amon['variable_entry']['clwCCI']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clwCLARA'] = {}
Amon['variable_entry']['clwCLARA']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clwCLARA']['cell_methods'] = 'area: mean time: mean'
Amon['variable_entry']['clwCLARA']['comment'] = 'Percentage liquid cloud cover in optical depth categories.'
Amon['variable_entry']['clwCLARA']['dimensions'] = 'longitude latitude plev7c tau time'
Amon['variable_entry']['clwCLARA']['frequency'] = 'mon'
Amon['variable_entry']['clwCLARA']['long_name'] = 'CLARA Liquid Cloud Area Fraction'
Amon['variable_entry']['clwCLARA']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clwCLARA']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clwCLARA']['out_name'] = 'clwCLARA'
Amon['variable_entry']['clwCLARA']['positive'] = ''
Amon['variable_entry']['clwCLARA']['standard_name'] = 'liquid_water_cloud_area_fraction_in_atmosphere_layer'
Amon['variable_entry']['clwCLARA']['type'] = 'real'
Amon['variable_entry']['clwCLARA']['units'] = '%'
Amon['variable_entry']['clwCLARA']['valid_max'] = ''
Amon['variable_entry']['clwCLARA']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clwtCCI'] = {}
Amon['variable_entry']['clwtCCI']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clwtCCI']['cell_methods'] = 'area: time: mean'
Amon['variable_entry']['clwtCCI']['comment'] = ''
Amon['variable_entry']['clwtCCI']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['clwtCCI']['frequency'] = 'mon'
Amon['variable_entry']['clwtCCI']['long_name'] = 'CCI Total Liquid Cloud Area Fraction'
Amon['variable_entry']['clwtCCI']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clwtCCI']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clwtCCI']['out_name'] = 'clwtCCI'
Amon['variable_entry']['clwtCCI']['positive'] = ''
Amon['variable_entry']['clwtCCI']['standard_name'] = 'liquid_water_cloud_area_fraction'
Amon['variable_entry']['clwtCCI']['type'] = 'real'
Amon['variable_entry']['clwtCCI']['units'] = '%'
Amon['variable_entry']['clwtCCI']['valid_max'] = ''
Amon['variable_entry']['clwtCCI']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'clwtCLARA'] = {}
Amon['variable_entry']['clwtCLARA']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['clwtCLARA']['cell_methods'] = 'area: mean time: mean'
Amon['variable_entry']['clwtCLARA']['comment'] = ''
Amon['variable_entry']['clwtCLARA']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['clwtCLARA']['frequency'] = 'mon'
Amon['variable_entry']['clwtCLARA']['long_name'] = 'CLARA Total Liquid Cloud Area Fraction'
Amon['variable_entry']['clwtCLARA']['ok_max_mean_abs'] = ''
Amon['variable_entry']['clwtCLARA']['ok_min_mean_abs'] = ''
Amon['variable_entry']['clwtCLARA']['out_name'] = 'clwtCLARA'
Amon['variable_entry']['clwtCLARA']['positive'] = ''
Amon['variable_entry']['clwtCLARA']['standard_name'] = 'liquid_water_cloud_area_fraction'
Amon['variable_entry']['clwtCLARA']['type'] = 'real'
Amon['variable_entry']['clwtCLARA']['units'] = '%'
Amon['variable_entry']['clwtCLARA']['valid_max'] = ''
Amon['variable_entry']['clwtCLARA']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'pctCCI'] = {}
Amon['variable_entry']['pctCCI']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['pctCCI']['cell_methods'] = 'area: time: mean'
Amon['variable_entry']['pctCCI']['comment'] = ''
Amon['variable_entry']['pctCCI']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['pctCCI']['frequency'] = 'mon'
Amon['variable_entry']['pctCCI']['long_name'] = 'CCI Mean Cloud Top Pressure'
Amon['variable_entry']['pctCCI']['ok_max_mean_abs'] = ''
Amon['variable_entry']['pctCCI']['ok_min_mean_abs'] = ''
Amon['variable_entry']['pctCCI']['out_name'] = 'pctCCI'
Amon['variable_entry']['pctCCI']['positive'] = ''
Amon['variable_entry']['pctCCI']['standard_name'] = 'air_pressure_at_cloud_top'
Amon['variable_entry']['pctCCI']['type'] = 'real'
Amon['variable_entry']['pctCCI']['units'] = 'Pa'
Amon['variable_entry']['pctCCI']['valid_max'] = ''
Amon['variable_entry']['pctCCI']['valid_min'] = ''
# Variable sponsor - DWD; Stephan Finkensieper (Funkensieper) https://github.com/PCMDI/obs4MIPs-cmor-tables/issues/48
Amon['variable_entry'][u'pctCLARA'] = {}
Amon['variable_entry']['pctCLARA']['cell_measures'] = 'area: areacella'
Amon['variable_entry']['pctCLARA']['cell_methods'] = 'area: mean time: mean'
Amon['variable_entry']['pctCLARA']['comment'] = ''
Amon['variable_entry']['pctCLARA']['dimensions'] = 'longitude latitude time'
Amon['variable_entry']['pctCLARA']['frequency'] = 'mon'
Amon['variable_entry']['pctCLARA']['long_name'] = 'CLARA Mean Cloud Top Pressure'
Amon['variable_entry']['pctCLARA']['ok_max_mean_abs'] = ''
Amon['variable_entry']['pctCLARA']['ok_min_mean_abs'] = ''
Amon['variable_entry']['pctCLARA']['out_name'] = 'pctCLARA'
Amon['variable_entry']['pctCLARA']['positive'] = ''
Amon['variable_entry']['pctCLARA']['standard_name'] = 'air_pressure_at_cloud_top'
Amon['variable_entry']['pctCLARA']['type'] = 'real'
Amon['variable_entry']['pctCLARA']['units'] = 'Pa'
Amon['variable_entry']['pctCLARA']['valid_max'] = ''
Amon['variable_entry']['pctCLARA']['valid_min'] = ''

#%% Activity ID
product = [
 'obs4MIPs'
 ] ;

#%% Coordinate

#%% Frequency

#%% Grid

#%% Grid label

#%% Institution
tmp = [['institution_id','https://raw.githubusercontent.com/PCMDI/obs4mips-cmor-tables/master/obs4MIPs_institution_id.json']
      ] ;
institution_id = readJsonCreateDict(tmp)
institution_id = institution_id.get('institution_id')

# Fix issues
#==============================================================================
# Example new experiment_id entry
#institution_id['institution_id']['NOAA-NCEI'] = 'NOAA\'s National Centers for Environmental Information, Asheville, NC 28801, USA'
#institution_id['institution_id']['RSS'] = 'Remote Sensing Systems, Santa Rosa, CA 95401, USA'

#%% License
license_ = ('Data in this file produced by <Your Centre Name> is licensed under'
            ' a Creative Commons Attribution-ShareAlike 4.0 International License'
            ' (https://creativecommons.org/licenses/). Use of the data must be'
            ' acknowledged following guidelines found at <a URL maintained by you>.'
            ' Further information about this data, including some limitations,'
            ' can be found via <some URL maintained by you>.)')

#%% Mip era
mip_era = [
 'CMIP5',
 'CMIP6'
] ;

#%% Nominal resolution

#%% Product
product = [
 'observations'
 ] ;

#%% Realm
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

#%% Region (taken from http://cfconventions.org/Data/cf-standard-names/docs/standardized-region-names.html)
region = [
 'africa',
 'antarctica',
 'arabian_sea',
 'aral_sea',
 'arctic_ocean',
 'asia',
 'atlantic_ocean',
 'australia',
 'baltic_sea',
 'barents_opening',
 'barents_sea',
 'beaufort_sea',
 'bellingshausen_sea',
 'bering_sea',
 'bering_strait',
 'black_sea',
 'canadian_archipelago',
 'caribbean_sea',
 'caspian_sea',
 'central_america',
 'chukchi_sea',
 'contiguous_united_states',
 'denmark_strait',
 'drake_passage',
 'east_china_sea',
 'english_channel',
 'eurasia',
 'europe',
 'faroe_scotland_channel',
 'florida_bahamas_strait',
 'fram_strait',
 'global',
 'global_land',
 'global_ocean',
 'great_lakes',
 'greenland',
 'gulf_of_alaska',
 'gulf_of_mexico',
 'hudson_bay',
 'iceland_faroe_channel',
 'indian_ocean',
 'indo_pacific_ocean',
 'indonesian_throughflow',
 'irish_sea',
 'lake_baykal',
 'lake_chad',
 'lake_malawi',
 'lake_tanganyika',
 'lake_victoria',
 'mediterranean_sea',
 'mozambique_channel',
 'north_america',
 'north_sea',
 'norwegian_sea',
 'pacific_equatorial_undercurrent',
 'pacific_ocean',
 'persian_gulf',
 'red_sea',
 'ross_sea',
 'sea_of_japan',
 'sea_of_okhotsk',
 'south_america',
 'south_china_sea',
 'southern_ocean',
 'taiwan_luzon_straits',
 'weddell_sea',
 'windward_passage',
 'yellow_sea'
 ] ;

#%% Required global attributes - # indicates source
required_global_attributes = [
 'Conventions', #obs4MIPs table
 'activity_id', #CV
 'contact', #user provided
 'creation_date', #cmor
 'data_specs_version', #obs4MIPs table
 'frequency', #CV
 'further_info_url', #cmor
 'grid', #user provided
 'grid_label', #CV
 'institution_id', #CV
 'license', #CV
 'mip_era', #CV
 'nominal_resolution', #CV
 'product', #CV
 'realm', #CV
 'source_id', #CV - will require spec so source can be extracted
 'source_type', #CV (renamed from product)
 'source_version_number', #user provided
 'table_id', #obs4MIPs table
 'tracking_id', #cmor
 'variable_id' #cmip6
] ;

#%% Source ID
source_id = {}
key = 'GPCP' # Attempting to scratch something together from https://github.com/WCRP-CMIP/CMIP6_CVs/blob/master/CMIP6_source_id.json#L3-L51
source_id[key] = {}
source_id[key]['label'] = key
source_id[key]['label_extended'] = 'Global Precipitation Climatology Project'
source_id[key]['release_year'] = '2017'
source_id[key]['source_id'] = key

# Fix issues
#==============================================================================
# Example new source_id entry
#key = 'GPCP'
#source_id['source_id'][key] = 'Global Precipitation Climatology Project'

#%% Source type
source_type = [
 'gridded_insitu',
 'reanalysis',
 'satellite_blended',
 'satellite_retrieval'
] ;

#%% Table ID
table_id = ['Aday', 'Amon', 'Lmon', 'Omon', 'SImon', 'fx'] ;

#%% Write variables to files
for jsonName in masterTargets:
    # Clean experiment formats
    if jsonName in ['coordinate','grids']: #,'Amon','Lmon','Omon','SImon']:
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
    if jsonName in ['Aday', 'Amon', 'Lmon', 'Omon', 'SImon', 'fx']:
        outFile = ''.join(['../Tables/obs4MIPs_',jsonName,'.json'])
    elif jsonName == 'license_':
        outFile = ''.join(['../obs4MIPs_license.json'])
    else:
        outFile = ''.join(['../obs4MIPs_',jsonName,'.json'])
    # Check file exists
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    if not os.path.exists('../Tables'):
        os.mkdir('../Tables')
    # Create host dictionary
    if jsonName == 'license_':
        jsonDict = {}
        jsonDict[jsonName.replace('_','')] = eval(jsonName)
    elif jsonName not in ['coordinate','formula_terms','fx','grids',
                        'institution_id','Aday','Amon','Lmon','Omon','SImon']:
        jsonDict = {}
        jsonDict[jsonName] = eval(jsonName)
    else:
        jsonDict = eval(jsonName)
    fH = open(outFile,'w')
    json.dump(jsonDict,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
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
inputJson = ['frequency','grid_label','institution_id','license','mip_era',
             'nominal_resolution','product','realm','region',
             'required_global_attributes','source_id','source_type','table_id', # These are controlled vocabs
             'coordinate','grids','formula_terms', # These are not controlled vocabs - rather lookup tables for CMOR
             'Aday','Amon','Lmon','Omon','SImon','fx' # Update/add if new tables are generated
            ]
lookupList = ['coordinate','grids','formula_terms']
tableList = ['Aday','Amon','Lmon','Omon','SImon','fx']

# Load dictionaries from local files
for count,CV in enumerate(inputJson):
    if CV in tableList:
        path = '../Tables/'
    else:
        path = '../'
    vars()[CV] = json.load(open(''.join([path,'obs4MIPs_',CV,'.json'])))

# Build CV master dictionary
obs4MIPs_CV = {}
obs4MIPs_CV['CV'] = {}
for count,CV in enumerate(inputJson):
    #CVName1 = CV[0]
    if CV not in tableList:
        obs4MIPs_CV['CV'][CV] = eval(CV)

# Write obs4MIPs_CV.json
if os.path.exists('obs4MIPs_CV.json'):
    print 'File existing, purging:','obs4MIPs_CV.json'
    os.remove('obs4MIPs_CV.json')
fH = open('obs4MIPs_CV.json','w')
json.dump(obs4MIPs_CV,fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
fH.close()

# Loop and write all other files
os.chdir('Tables')
tableList.extend(lookupList)
for count,CV in enumerate(tableList):
    outFile = ''.join(['obs4MIPs_',CV,'.json'])
    if os.path.exists(outFile):
        print 'File existing, purging:',outFile
        os.remove(outFile)
    fH = open(outFile,'w')
    json.dump(eval(CV),fH,ensure_ascii=True,sort_keys=True,indent=4,separators=(',',':'),encoding="utf-8")
    fH.close()

# Cleanup
del(coordinate,count,formula_terms,frequency,grid_label,homePath,institution_id,
    mip_era,nominal_resolution,obs4MIPs_CV,product,realm,inputJson,lookupList,
    tableList,required_global_attributes,table_id)

#%% Generate zip archive
# Cleanup rogue files
os.chdir(demoPath)
if os.path.exists('.DS_Store'):
    os.remove('.DS_Store')
if os.path.exists('demo.zip'):
    os.remove('demo.zip')
if os.path.exists('demo/demo.zip'):
    os.remove('demo/demo.zip')
# Jump up one directory
os.chdir(demoPath.replace('/demo',''))
# Zip demo dir
p = subprocess.Popen(['7za','a','demo.zip','demo','tzip'],
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                         cwd=os.getcwd())
stdout = p.stdout.read() ; # Use persistent variables for tests below
stderr = p.stderr.read()
# Move to demo dir
shutil.move('demo.zip', 'demo/demo.zip')
import cmor
import xcdat as xc
import xarray as xr
import cftime
import numpy as np
import sys, os, glob
from datetime import datetime

# TEST CASE OF USING CMOR WITH MODIFIED CORDEX SPECIFICATIONS WITH LOCA2 DATA @NERSC PERLMUTTER
# PJG  10092024
# PJG  10142024 Generalized to all CMIP mods

cmorTable = 'Downscaling_Aday.json'
inputJson = 'LOCA2_CMIP6_input.json'
inputFilePath = '/global/cfs/projectdirs/m3522/cmip6/LOCA2/*/0p0625deg/r1i1p1f1/historical/pr/pr.*.historical.r1i1p1f1.1950-2014.LOCA_16thdeg_v20220519.nc'

# TRAP CMIP6 MODS AND RUNS
lst = glob.glob(inputFilePath)
mods = []
for l in lst:
    mod = l.split('/')[7]
    if mod not in mods: mods.append(mod)
mod_runs = {}
for mod in mods:
    infile = inputFilePath.replace('*',mod)
    infile = infile.replace('r1i1p1f1','r*i1p1f1')
    lst1 = glob.glob(infile)
    rn = []
    for l in lst1:
       rni = l.split('.')[3]
       if rni not in rn: rn.append(rni)
    rn.sort()
    mod_runs[mod] = rn
    print(mod,mod_runs[mod])

#w =sys.stdin.readline()

inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

yrs = list(range(1950,2014))  #end is 2014  ###
yrs = [('1950','1954'),('1955','1959'),('1960','1964'),('1965','1969'),('1970','1974'),('1975','1979'),('1980','1984'),('1985','1989'),('1990','1994'),('1995','1999'),('2000','2004'),('2005','2009'),('2010','2014')]
#yrs = [yrs[0]]     ###


mods = [mods[0]]   ###
for mod in mods:
 rns = mod_runs[mod]
#rns = [rns[0]]    ###
 for ri in rns: 
  infile = inputFilePath.replace('*',mod)
  infile = infile.replace('r1i1p1f1',ri)
  for yr in yrs:
   start_time = datetime.now()
   fc = xc.open_dataset(infile,decode_times=True,use_cftime=True)   #,preprocess=extract_date)
   f = fc
   f = fc.sel(time=slice(yr[0],yr[1]))
   d = f[inputVarName]

   lat = f.lat.values  #f.getLatitude()
   lon = f.lon.values  #d.getLongitude()
   time = f.time.values   #d.get
   tunits = "days since 1900-01-01"

# f = f.drop_vars(["lat_bounds","lon_bounds"])
   f = f.bounds.add_bounds("X") 
   f = f.bounds.add_bounds("Y")
   f = f.bounds.add_bounds("T")

#####time.setBounds() #####time_bounds)
   cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
   cmor.dataset_json(inputJson)
   cmor.load_table(cmorTable)

# SET CMIP MODEL SPECIFIC ATTRIBUTES 
   cmor.set_cur_dataset_attribute("source_id","LOCA2--" + mod)
   cmor.set_cur_dataset_attribute("driving_source_id",mod)
   cmor.set_cur_dataset_attribute("driving_variant_label",ri)

# Create CMOR axes
   cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.lat_bnds.values, units="degrees_north")
   cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.lon_bnds.values, units="degrees_east")
   cmorTime = cmor.axis("time", coord_vals=cftime.date2num(time,tunits), cell_bounds=cftime.date2num(f.time_bnds.values,tunits), units= tunits)
   cmoraxes = [cmorTime,cmorLat, cmorLon]

# Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
   varid   = cmor.variable(outputVarName,outputUnits,cmoraxes,missing_value=1.e20)
   values  = np.array(d[:],np.float32)

   cmor.set_variable_attribute(varid,'valid_min','f',2.0)
   cmor.set_variable_attribute(varid,'valid_max','f',3.0)

   cmor.set_deflate(varid,1,1,1) ; # shuffle=1,deflate=1,deflate_level=1 - Deflate options compress file data
   cmor.write(varid,values,len(time)) ; # Write variable with time axis
   cmor.close()
   f.close()
   fc.close()
   end_time = datetime.now()
   print('done cmorizing ',mod,' ', ri,' ', yr[0],'-',yr[1],' time: {}'.format(end_time-start_time))
                                                          
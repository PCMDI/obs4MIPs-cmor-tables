import cmor
import xcdat as xc
import xarray as xr
import cftime
import numpy as np
import sys, os, glob


cmorTable = '../Tables/obs4MIPs_Aday.json'
inputJson = 'STAR-ESDM_ACCESS-CM2_input.json'

inputFilePath = '/global/cfs/projectdirs/m3522/cmip6/STAR-ESDM/ssp245/downscaled.ACCESS-CM2.r1i1p1f1.pr.ssp245.gn.nclimgrid.star.1950.2100.tllc.nc'
inputVarName = 'pr'
outputVarName = 'pr'
outputUnits = 'kg m-2 s-1'

exps = ['historical','ssp245', 'ssp585']
mods = ['MPI-ESM1-2-HR', 'TaiESM1', 'CMCC-ESM2', 'ACCESS-ESM1-5', 'MRI-ESM2-0', 'FGOALS-g3', 'NorESM2-MM', 'CanESM5', 'MIROC6', 'ACCESS-CM2', 'NorESM2-LM', 'MPI-ESM1-2-LR', 'BCC-CSM2-MR', 'NESM3']

tmp0 = inputFilePath.split('.')
print(tmp[0])

yrs_hist = [('1950','1954'),('1955','1959'),('1960','1964'),('1965','1969'),('1970','1974'),('1975','1979'),('1980','1984'),('1985','1989'),('1990','1994'),('1995','1999'),('2000','2004'),('2005','2009'),('2010','2014')]
yrs_scen = [('2015', '2019'), ('2020', '2024'), ('2025', '2029'), ('2030', '2034'), ('2035', '2039'), ('2040', '2044'), ('2045', '2049'), ('2050', '2054'), ('2055', '2059'), ('2060', '2064'), ('2065', '2069'), ('2070', '2074'), ('2075', '2079'), ('2080', '2084'), ('2085', '2089'), ('2090', '2094'), ('2095', '2099')]


#yrs = [yrs[0]]

for mod in mods:
 for exp in exps:    
    if exp == 'historical': yrs = yrs_hist
    if exp in ['ssp245', 'ssp585']: yrs = yrs_scen
    fi = inputFilePath
    fc = xc.open_dataset(fi,decode_times=False,use_cftime=False)
    fc.time.attrs['calendar'] = '365_day'
    fd = fc
    fd.coords['time'] = cftime.num2date(fc.time.values, 'days since 1950-01-01', calendar='365_day')

    for yr in yrs:
     f = fd.sel(time=slice(yr[0],yr[1]))
     d = f[inputVarName]
     lat = f.latitude.values  
     lon = f.longitude.values  
     time = f.time.values  
     tunits = "days since 1950-01-01"

     f = f.bounds.add_bounds("X")  #, width=0.5)
     f = f.bounds.add_bounds("Y")
     f = f.bounds.add_bounds("T")

# SET CMIP MODEL SPECIFIC ATTRIBUTES 
     cmor.set_cur_dataset_attribute("source_id","STAR-ESDM-v0--" + mod)
     cmor.set_cur_dataset_attribute("driving_source_id",mod)
     cmor.set_cur_dataset_attribute("driving_variant_label",ri)
     cmor.set_cur_dataset_attribute("driving_experiment_id",exp)

# For more information see https://cmor.llnl.gov/mydoc_cmor3_api/
     cmor.setup(inpath='./',netcdf_file_action=cmor.CMOR_REPLACE_4,logfile='cmorLog.txt')
     cmor.dataset_json(inputJson)
     cmor.load_table(cmorTable)

     time_np = cftime.date2num(time,tunits)
     time_np = np.array(time_np[:],np.float32)  #time_np.astype(np.float32)  
     tbds_np = cell_bounds=cftime.date2num(f.time_bnds.values,tunits)
     tbds_np = np.array(tbds_np[:],np.float32)  #tbds_np.astype(np.float32)

# Create CMOR axes
     cmorLat = cmor.axis("latitude", coord_vals=lat[:], cell_bounds=f.latitude_bnds.values, units="degrees_north")
     cmorLon = cmor.axis("longitude", coord_vals=lon[:], cell_bounds=f.longitude_bnds.values, units="degrees_east")
     cmorTime = cmor.axis("time", coord_vals=time_np, cell_bounds=tbds_np, units= tunits)
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
     print('done cmorizing ',mod, ri, yr[0] + ' - ' + yr[1])
                                                          
#writes out ancillary data files for the ozone obs4mips data
#
#import xcdat
import xarray
import glob
import numpy as np
import matplotlib.pyplot as plt
import uuid
from datetime import datetime

#output directory
outdir='~/obs4mips/obs4MIPs/DLR-BIRA/C3S-GTO-ECV-9-0/mon/toz/gn/v20231115_ancillary/'

#read in toz obs4mips files
obs4mips_file = '~/obs4mips/obs4MIPs/DLR-BIRA/C3S-GTO-ECV-9-0/mon/toz/gn/v20231115/toz_mon_C3S-GTO-ECV-9-0_BE_gn_199507-202204.nc'

#read in with xarray
data = xarray.open_dataset(obs4mips_file)

#---------------
#read the individual data files
#inputs  (initially just start with a single file)
input_dir = '/gws/nopw/j04/esacci_portal/obs4mips/ozone/toc/files_for_obs4mips_v9/'
input_path = input_dir+'*'

#get filelist
filelist = glob.glob(input_path)

#create an array for the uncertainty values the same size as for the obs4mips fill
toc_n_obs = np.full_like(data.toz,-999)
toc_sd= np.full_like(data.toz,-999)
toc_serr = np.full_like(data.toz,-999)

index=0
for filename in filelist:
    ds = xarray.open_dataset(filename)  #was previously xcdat

     #check that time and lat/lon grids match  
    if not np.array_equal(ds['longitude'].values,data['lon'].values):
        print('longitudes do not match')
    if not np.array_equal(ds['latitude'].values,data['lat'].values):
        print('latitudes do not match')
    
    #check time...

    #extract data into arrays
    toc_n_obs[index,:,:] = ds.total_ozone_column_number_of_observations.values  # number of observations
    toc_sd[index,:,:] = ds.total_ozone_column_standard_deviation.values * 2241.399 / 1e5
    toc_serr[index,:,:] = ds.total_ozone_column_standard_error.values * 2241.399 / 1e5

    index+=1

#----------
#create dataarrays for no of observations, standard_error and standard_deviation
darray_toc_n_obs = xarray.DataArray(toc_n_obs,dims=['time','lat','lon'],
    coords=[data.time,data.lat,data.lon],
    attrs=dict(units=ds.total_ozone_column_number_of_observations.units, long_name=ds.total_ozone_column_number_of_observations.long_name,standard_name='number_of_observations'))
darray_toc_sd = xarray.DataArray(toc_sd,dims=['time','lat','lon'],
    coords=[data.time,data.lat,data.lon],
    attrs = dict(units='m',long_name=ds.total_ozone_column_standard_deviation.long_name))
darray_toc_serr = xarray.DataArray(toc_serr,dims=['time','lat','lon'],
    coords=[data.time,data.lat,data.lon],
    attrs = dict(units='m',long_name=ds.total_ozone_column_standard_error.long_name,standard_name=data.toz.standard_name + ' standard_error'))

#create datasets

creation_time=datetime.now().isoformat()

common_attrs = dict( 
        Conventions='CF-1.7',
        activity_id = "obs4MIPs",
        contact = data.contact,
        creation_date = creation_time,
        external_variables=data.external_variables,
        frequency=data.frequency,
        further_info_url=data.further_info_url,
        grid=data.grid,
        grid_label=data.grid_label,
        history=creation_time+'reformatted data to be consistent with obs4MIPs, and CF-1.7 ODS-2.1 standards',
        institution=data.institution,
        institution_id = data.institution_id,
        mip_era=data.mip_era,
        nominal_resolution=data.nominal_resolution,
        originData_URL=data.originData_URL,
        originData_notes=data.originData_notes,
        originData_retrieved=data.originData_retrieved,
        product=data.product,
        realm=data.realm,
        references=data.references,
        region=data.region,
        release_year=data.release_year,
        source = data.source,
        source_description=data.source_description,
        source_id = data.source_id,
        source_label=data.source_label,
        source_name=data.source_name,
        source_type=data.source_type,
        source_version_number = data.source_version_number,
        variant_info = data.variant_info,
        variant_label=data.variant_label,
        license=data.license)




#number of observations

dataset_toc_n_obs = xarray.Dataset(
    data_vars = dict(toz_number_of_observations=darray_toc_n_obs.fillna(value=0.0),time_bnds=data.time_bnds,lat_bnds=data.lat_bnds,lon_bnds=data.lon_bnds),
    coords=dict(
        lon=data.lon,
        lat=data.lat,
        time=data.time
    ),
    attrs=dict(
        common_attrs,
        comment=data.comment + 'This file contains the number of measurements used to derive the mean total ozone column (available in a separate file)',
        title='L3 total_ozone_satellite observations v9.0: number of measurements used to derive the mean total ozone',
        variable_id='toz_number_of_observations',
        tracking_id = str(uuid.uuid4())
    )
)

#set encoding so doesn't write fill_values to lat/lon/time etc
encoding = dict(time={'_FillValue':None,'units':"days since '1970-01-01'"},lat={'_FillValue':None},lon={'_FillValue':None},lat_bnds={'_FillValue':None},lon_bnds={'_FillValue':None},time_bnds={'_FillValue':None,'dtype':'double'},toz_number_of_observations={'_FillValue':0})
#write out data
dataset_toc_n_obs.to_netcdf(outdir+'n_obs-toz_mon_C3S-GTO-ECV-9-0_BE_gn_199507-202204.nc','w',format='NETCDF4_CLASSIC',encoding=encoding,unlimited_dims='time')

#standard deviation
dataset_toc_sd = xarray.Dataset(
    data_vars = dict(toz_standard_deviation=darray_toc_sd.fillna(value=1.e20),time_bnds=data.time_bnds,lat_bnds=data.lat_bnds,lon_bnds=data.lon_bnds),
    coords=dict(
        lon=data.lon,
        lat=data.lat,
        time=data.time
    ),
    attrs=dict(
        common_attrs,
        comment=data.comment + 'This file contains the standard deviation of the Mean Total Ozone Column (available in a separate file)',
        title='L3 total_ozone_satellite observations v9.0: standard deviation of the mean total ozone',
        variable_id='toz_standard_deviation',
        tracking_id = str(uuid.uuid4())
    )
)
encoding = dict(time={'_FillValue':None,'units':"days since '1970-01-01'"},lat={'_FillValue':None},lon={'_FillValue':None},lat_bnds={'_FillValue':None},lon_bnds={'_FillValue':None},time_bnds={'_FillValue':None,'dtype':'double'},toz_standard_deviation={'_FillValue':1.e20})
dataset_toc_sd.to_netcdf(outdir+'sd-toz_mon_C3S-GTO-ECV-9-0_BE_gn_199507-202204.nc','w',format='NETCDF4_CLASSIC',encoding=encoding,unlimited_dims='time')

#standard_error
dataset_toc_serr = xarray.Dataset(
    data_vars = dict(toz_standard_error=darray_toc_serr.fillna(value=1.e20),time_bnds=data.time_bnds,lat_bnds=data.lat_bnds,lon_bnds=data.lon_bnds),
    coords=dict(
        lon=data.lon,
        lat=data.lat,
        time=data.time
    ),
    attrs=dict(
        common_attrs,
        comment=data.comment + 'This file contains the standard error of the Mean Total Ozone Column (available in a separate file)',
        title='L3 total_ozone_satellite observations v9.0: standard deviation of the mean total ozone',
        variable_id='toz_standard_deviation',
        tracking_id = str(uuid.uuid4())
    )
)
encoding = dict(time={'_FillValue':None,'units':"days since '1970-01-01'"},lat={'_FillValue':None},lon={'_FillValue':None},lat_bnds={'_FillValue':None},lon_bnds={'_FillValue':None},time_bnds={'_FillValue':None,'dtype':'double'},toz_standard_error={'_FillValue':1.e20})
dataset_toc_serr.to_netcdf(outdir+'sderr-toz_mon_C3S-GTO-ECV-9-0_BE_gn_199507-202204.nc','w',format='NETCDF4_CLASSIC',encoding=encoding,unlimited_dims='time')








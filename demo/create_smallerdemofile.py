import xarray as xr
import xcdat as xc

data_in = 'precip.mon.mean.nc'
f = xr.open_dataset(data_in,decode_times=False)
d = f['precip']

d.to_netcdf('test.nc')

print('done')

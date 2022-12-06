import xarray as xr
import xcdat as xc


f = xr.open_dataset(data_in,decode_times=False)
d = f['precip']

#for att in f.attrs:
# d.attrs['global attr'][att] = f.attrs[att]

d.to_netcdf('test.nc')

print('done')

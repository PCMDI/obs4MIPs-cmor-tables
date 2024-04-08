import xcdat as xc
import xarray as xr
import numpy as np
import glob
import os
import sys

def avg_3hr_imerg(basedir, yr1, yr2, mo1, mo2, ext='RT-H5'):
    """
        Function takes IMERG files and averages them to 3-hourly, 0.1 degree
        data.
    """
    
    files_list = sorted(glob.glob(os.path.join(basedir,f'*.{ext}')))
    print(f'Averaging from {yr1}-{mo1} to {yr2}-{mo2}')
    for iyr in range(yr1,yr2+1):
        for imo in range(mo1,mo2+1):
            imon=str(imo).zfill(2)
            print(iyr,imon)

            sidx=[]
            output_array = []
            for i, file in enumerate(files_list):
                tmp = file.split('/')[-1]
                yyyymmdd = tmp.split('.')[4][:8]
                year = yyyymmdd[:4]
                mon = yyyymmdd[4:6]
                minute = tmp.split('.')[5]

                if (year==str(iyr) and mon==imon):
                    print(file)
                    print(iyr,imon,i,yyyymmdd,minute)
                    if (ext == 'nc') or (ext == 'nc4'):
                        f = xc.open_dataset(file)
                    else:
                        f = xc.open_dataset(file, group='Grid').as_numpy()
                    d = f['precipitationCal']
                    d = d[0].transpose() # axis (lon,lat) to (lat,lon)
                    output_array.append(d)
                    sidx.append(i)
                    f.close()

            # For average with centered time (e.g., 00h -> 22:30:00 – 01:29:59)
            del output_array[-3:]   # fails if no data in the previous day (or less than 3 files)
            ist=0
            for i, file in enumerate(files_list):
                tmp = file.split('/')[-1]
                yyyymmdd = tmp.split('.')[4][:8]
                minute = tmp.split('.')[5]
                if (i>=sidx[0]-3 and i<sidx[0]):
                    print(iyr,imon,i,yyyymmdd,minute)
                    if (ext == 'nc') or (ext == 'nc4'):
                        f = xc.open_dataset(file)
                    else:
                        f = xc.open_dataset(file, group='Grid').as_numpy()
                    d = f['precipitationCal']
                    d = d[0].transpose() # axis (lon,lat) to (lat,lon)
                    output_array.insert(ist,d)
                    ist=ist+1
                    f.close()

            output_array = np.array(output_array)
            nt30mn=output_array.shape[0]
            nt3hr=int(nt30mn/6)
            nt1dy=int(nt3hr/8)

            d3hr=np.zeros((nt3hr, output_array.shape[1], output_array.shape[2]), float)

            i3hr=0
            for it in range(0,nt30mn,6):
                d3hr[i3hr]=np.ma.average(output_array[it:it+6],axis=0)
                i3hr+=1

            t = xr.DataArray(np.arange(0,nt1dy,1/8), dims=("time"))
            d3hr = np.asarray(d3hr)

            latitude = f['lat']
            longitude = f['lon']

            data = xr.Dataset({"pr": (["time","lat","lon"], d3hr, {'units':'mm/hr', 'missing_value':1.0E20, '_FillValue':1.0E20})},
                coords={
                    "time": (['time'], t.values, {'units':'days since '+str(iyr)+'-'+imon+'-01 00:00:00'}),
                    "lat" : (['lat'], latitude.values, {'units':'degrees_north'}),
                    "lon" : (['lon'], longitude.values, {'units':'degrees_east'}),
                },
            )

            data.lat.attrs['axis'] = 'Y'
            data.lat.attrs['standard_name'] = 'latitude'

            data.lon.attrs['axis'] = 'X'
            data.lon.attrs['standard_name'] = 'longitude'

            data.time.attrs['calendar'] = 'gregorian'
            data.time.attrs['axis'] = 'T'
            data.time.attrs['standard_name'] = 'time'

            print(f"3-hourly averaging complete")
    return data
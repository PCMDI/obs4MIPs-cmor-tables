import cdms2 as cdms
import numpy as np
import MV2 as MV
import glob
import os

basedir = '/work/ahn6/obs/IMERG/IMERG_Final.Run_V06B/0.5hr/gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGHH.06/*/*'
ncfiles_list = sorted(glob.glob(os.path.join(basedir,'*.nc4')))

#print(ncfiles_list)
#print(len(ncfiles_list))

for iyr in range(2001,2020):
#for iyr in range(2014,2020):
#for iyr in range(2018,2020):
    for imo in range(1,13):
        imon=str(imo).zfill(2)
        print(iyr,imon)

        sidx=[]
        output_array = []
        for i, ncfile in enumerate(ncfiles_list):
            tmp = ncfile.split('/')[-1]
            yyyymmdd = tmp.split('.')[4][:8]
            year = yyyymmdd[:4]
            mon = yyyymmdd[4:6]
            if (year==str(iyr) and mon==imon):
                print(iyr,imon,i,yyyymmdd)
                f = cdms.open(ncfile)
                d = f('precipitationCal')
                d = MV.transpose(d[0])  # axis (lon,lat) to (lat,lon)
                output_array.append(d)
                sidx.append(i)
                f.close()

        # For average with centered time (e.g., 00h -> 22:30:00 – 01:29:59)
        print(len(output_array))
        del output_array[-3:]
        print(len(output_array))
        ist=0
        for i, ncfile in enumerate(ncfiles_list):
            tmp = ncfile.split('/')[-1]
            yyyymmdd = tmp.split('.')[4][:8]
            minute = tmp.split('.')[5]
            if (i>=sidx[0]-3 and i<sidx[0]):
                print(iyr,imon,i,yyyymmdd,minute)
                f = cdms.open(ncfile)
                d = f('precipitationCal')
                d = MV.transpose(d[0])  # axis (lon,lat) to (lat,lon)
                output_array.insert(ist,d)
                ist=ist+1
                f.close()

        output_array = MV.array(output_array)
        print(output_array.shape)
        nt30mn=output_array.shape[0]
        nt3hr=int(nt30mn/6)
        nt1dy=int(nt3hr/8)
    
        d3hr=MV.zeros((nt3hr, output_array.shape[1], output_array.shape[2]), MV.float)
        i3hr=0
        for it in range(0,nt30mn,6):
            print(i3hr,it,it+6-1)
            d3hr[i3hr]=MV.average(output_array[it:it+6],axis=0)
            i3hr+=1
    
        time = cdms.createAxis(np.arange(0,nt1dy,1/8),id='time')
        time.calendar = 'gregorian'
        time.units = 'days since '+str(iyr)+'-'+imon+'-01 00:00:00'
    
        lat = d.getLatitude()
        lon = d.getLongitude()
        lat.id = 'latitude'
        lon.id = 'longitude'
    
        d3hr.setAxisList((time,lat,lon))
        d3hr.id = 'pr'
        d3hr.units = 'mm/hr'
    
        fout = cdms.open('./IMERG_Final.Run.V06B_0.1deg_3hr_'+str(iyr)+imon+'.nc','w')
        fout.write(d3hr)
        fout.close()




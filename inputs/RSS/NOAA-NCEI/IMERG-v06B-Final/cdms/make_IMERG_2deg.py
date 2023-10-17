import cdms2 as cdms
import MV2 as MV
import numpy as np
from regrid2 import Regridder
import glob

#==================================================================================
def Regrid2deg(d):
    """
    Regrid to 2deg (180lon*90lat) horizontal resolution
    Input
    - d: cdms variable
    Output
    - drg: cdms variable with 2deg horizontal resolution
    """
    # Regridding
    tgrid = cdms.createUniformGrid(-89, 90, 2.0, 0, 180, 2.0, order='yx')
    orig_grid = d.getGrid()
    regridFunc = Regridder(orig_grid,tgrid)
    drg=MV.zeros((d.shape[0], tgrid.shape[0], tgrid.shape[1]), MV.float)
    for it in range(d.shape[0]):
        drg[it] = regridFunc(d[it])

    # Dimension information
    time = d.getTime()
    lat = tgrid.getLatitude()
    lon = tgrid.getLongitude()
    drg.setAxisList((time,lat,lon))

    # Missing value (In case, missing value is changed after regridding)
    drg[drg>=d.missing_value]=d.missing_value
    mask=np.array(drg==d.missing_value)
    drg.mask = mask

    print('Complete regridding from', d.shape, 'to', drg.shape)
    return drg
#==================================================================================


lst = glob.glob('/work/ahn6/obs/IMERG/IMERG_Final.Run_V06B/3hr.center/IMERG_Final.Run.V06B_0.1deg_3hr_*.nc')
lst.sort()

for l in lst:
    print(l)
    f = cdms.open(l)
    d = f['pr']
    drg = Regrid2deg(d)
    
    file=l.split('/')[-1]
    newfile=file.replace('0.1deg','2deg')
    out = cdms.open('./'+newfile,'w')
    out.write(drg, id='pr')
    out.close()


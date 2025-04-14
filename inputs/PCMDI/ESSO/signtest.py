import xcdat
import glob

pin = '/p/user_pub/PCMDIobs/obs4MIPs/ESSO/TropFlux-1-0/mon/*/gn/v20250414/*.nc'

lst = glob.glob(pin)

for l in lst:
    ds = xcdat.open_dataset(l)
    vr = l.split('/')[8]
    ds_avg = float(ds.isel(time=0).spatial.average(vr)[vr])
    print(vr,' ', str(ds_avg))
    ds.close()

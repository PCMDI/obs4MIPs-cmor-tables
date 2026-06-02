import numpy as np
import xarray as xr
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import glob, os

def clean_gsmap(p):
    fill = p.encoding.get("_FillValue", None) or p.attrs.get("missing_value", None)

    if fill is not None:
        p = p.where(p != fill)

    return p.where(np.isfinite(p))

def process_day(day, dirroot, inroot, outroot, year, mon):

    files = sorted(glob.glob(
        f"{dirroot}/{inroot}/GPMMRG_MAP_{day}??00_H_L3S_MC?_05?.??"
    ))
#   print(day, len(files),[os.path.basename(f) for f in files])

    if len(files) != 24:
        print(f"skip {day}: {len(files)} files")
        return

    s = None
    cnt = None

    for f in files:
        if f.endswith(".h5"):
            ds = xr.open_dataset(f, group="Grid")
        else:
            ds = xr.open_dataset(f)

        p = clean_gsmap(ds["hourlyPrecipRate"]).T

        if s is None:
            s = p.fillna(0)
            cnt = xr.where(p.notnull(), 1, 0)
            lon = ds["Longitude"][:, 0].values
            lat = ds["Latitude"][0, :].values

        else:
            s += p.fillna(0)
            cnt += xr.where(p.notnull(), 1, 0)

        ds.close()

    daily = s.where(cnt == 24)

    time = np.datetime64(f"{year}-{mon}-{day[4:6]}")

    outdir = f"{dirroot}/{outroot}"
    os.makedirs(outdir, exist_ok=True)

    outfile = f"{outdir}/{year}{mon}{day[4:6]}.nc"

    out = xr.Dataset(
        {
            "precip": (
                ("time", "lat", "lon"),
                daily.values[np.newaxis, :, :].astype(np.float32)
            )
        },
        coords={
            "time": [time],
            "lat": lat,
            "lon": lon,
        }
    )
    
    out["precip"].attrs["units"] = "mm/day"
    
    out.to_netcdf(
        outfile,
        encoding={
            "precip": {
                "zlib": True,
                "complevel": 4,
                "_FillValue": -9999.9,
                "dtype": "float32"
            }
        }
    )
    print("wrote", outfile)

def run_month(year, mon, nproc=16):

    dirroot = "/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/JAXA-20260422/GSMaP"
    inroot  = f"hourly/{year}"
#   outroot = f"daily/{year}"
    outroot = f"daily"

    pattern = f"{dirroot}/{inroot}/GPMMRG_MAP_{year[2:4]}{mon}??0000_H_L3S_MC?_05?.??"

    days = sorted([
        os.path.basename(f)[11:17]
        for f in glob.glob(pattern)
    ])

    print("days:", len(days))
    worker = partial(
        process_day,
        dirroot=dirroot,
        inroot=inroot,
        outroot=outroot,
        year=year,
        mon=mon
    )

    with ProcessPoolExecutor(max_workers=nproc) as ex:
        list(ex.map(worker, days))

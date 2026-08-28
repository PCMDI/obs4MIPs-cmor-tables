import cmor
import xcdat as xc
import numpy as np
import glob
import os
import sys
import cftime
from datetime import datetime, timedelta
sys.path.append("../../../../inputs/misc/")  # Path to obs4MIPsLib and obs4mips_utils
import obs4MIPsLib
import obs4mips_utils as ou


def has_bounds(ds, names):
    return any(n in ds.variables or n in ds.coords for n in names)


def load_orbit(files):
    """Open+concat one orbit's daily files along time."""
    files = sorted(files)
    return xc.open_mfdataset(files, mask_and_scale=True, decode_times=True,
                              use_cftime=True, combine='nested', concat_dim='time')


def clean_values(d, cmor_missing):
    """`d` was opened with mask_and_scale=True, so scale_factor/add_offset are
    already applied and _FillValue is already NaN -- xarray moves those attrs
    to `.encoding` during decode, they're not meant to be re-applied here.
    Just swap NaN (missing) for CMOR's missing value."""
    v = np.array(d.values, dtype=np.float32)
    return np.where(np.isfinite(v), v, cmor_missing)


#%% User provided input
cmorTable = '../../../../Tables/obs4MIPs_Aday.json'
inputJson = 'LST-SSMI-v6.04.json'
inputFilePath = '/global/cfs/projectdirs/m4581/obs4MIPs/obs4MIPs_input/CEDA/ESACCI-LST-L3C/v6-0-4'
inputVarName = ['lst', 'lst_uncertainty']
outputVarName = ['ts', 'tsuind']
outputUnits = ['K', 'K']

run_version = "v" + datetime.now().strftime("%Y%m%d")  # fixed for entire run
cmor_missing = np.float32(1.0e20)

for year in range(2010, 2011):  # put the years you want to process here
    for month in range(1, 2):
        files_asc = sorted(glob.glob(
            f"{inputFilePath}/ESACCI-LST-L3C-LST-SSMI17-0.125deg_1DAILY_ASC-{year}{month:02}??000000-fv6.04.nc"))
        files_des = sorted(glob.glob(
            f"{inputFilePath}/ESACCI-LST-L3C-LST-SSMI17-0.125deg_1DAILY_DES-{year}{month:02}??000000-fv6.04.nc"))
        if not files_asc or not files_des:
            continue

        f_asc = load_orbit(files_asc)
        f_des = load_orbit(files_des)

        # Both orbits must cover exactly the same set of CALENDAR DAYS, in the
        # same order, since 'time' will be shared and 'orbit' distinguishes
        # them. Compare dates only, not exact reference-time equality --
        # ASC and DES legitimately have different `time` reference values
        # even on a matching day (e.g. 00:25:36 vs 00:14:56).
        asc_dates = [(d.year, d.month, d.day) for d in f_asc.time.values]
        des_dates = [(d.year, d.month, d.day) for d in f_des.time.values]
        if asc_dates != des_dates:
            raise ValueError(
                f"{year}-{month:02}: ASC/DES day mismatch -- "
                f"{asc_dates} vs {des_dates}. "
                "Check for a missing overpass file on one side."
            )

        # Horizontal grid is identical in ASC and DES files -- use ASC for
        # lat/lon/bounds.
        f = f_asc
        if not has_bounds(f, ["lat_bnds", "lat_bounds"]):
            f = f.bounds.add_bounds("Y")
        if not has_bounds(f, ["lon_bnds", "lon_bounds"]):
            f = f.bounds.add_bounds("X")

        lat = f.lat.values
        lon = f.lon.values
        lat_bnds = f.get("lat_bnds", f.get("lat_bounds")).values
        lon_bnds = f.get("lon_bnds", f.get("lon_bounds")).values

        t_units = f.time.attrs.get("units") or f.time.encoding.get("units")
        calendar = f.time.attrs.get("calendar") or f.time.encoding.get("calendar", "standard")

        # IMPORTANT: the source `time(time)` value is a per-file reference
        # timestamp close to file/day start (e.g. 00:25:36Z) -- it is NOT a
        # nominal representative value for the day, and time_bnds derived
        # from it would not span a clean calendar day. So the CMOR-facing
        # `time`/`time_bnds` are built manually here from the calendar date
        # alone (noon UTC nominal value, full [00:00, 24:00) day bounds),
        # independent of the source file's raw reference time. The raw
        # reference time is still used below, added to `dtime`, to get the
        # *true* per-pixel acquisition time -- that's a separate quantity
        # from this nominal per-day axis value.
        file_dates = f_asc.time.values  # one cftime object per input file/day
        nominal_time_dt = [cftime.datetime(d.year, d.month, d.day, 12, 0, 0, calendar=calendar)
                            for d in file_dates]
        day_starts = [cftime.datetime(d.year, d.month, d.day, 0, 0, 0, calendar=calendar)
                      for d in file_dates]
        day_ends = [s + timedelta(days=1) for s in day_starts]

        time = cftime.date2num(nominal_time_dt, units=t_units, calendar=calendar).astype("float64")
        time_bnds = np.stack([
            cftime.date2num(day_starts, units=t_units, calendar=calendar),
            cftime.date2num(day_ends, units=t_units, calendar=calendar),
        ], axis=1).astype("float64")  # shape (ntime, 2)

        orbit_vals = np.array([0, 1], dtype="int32")  # 0=ascending, 1=descending

        # ---- true per-pixel acquisition time = time + dtime, stacked to match `values` ----
        obstime_asc = ou.obstime_from_time_dtime(f_asc)  # (ntime, nlat, nlon)
        obstime_des = ou.obstime_from_time_dtime(f_des)
        obstime = np.stack([obstime_asc, obstime_des], axis=1)  # -> (ntime, orbit, nlat, nlon)

        for fi in range(len(inputVarName)):  # looping over variables
            #%% Initialize and run CMOR
            cmor.setup(inpath='./', netcdf_file_action=cmor.CMOR_REPLACE_4) #,logfile='cmorLog.txt')
            cmor.dataset_json(inputJson)
            cmor.set_cur_dataset_attribute("version", run_version)
            cmor.load_table(cmorTable)

            axes = [
                {"table_entry": "time", "units": t_units},
                {"table_entry": "orbit", "units": "1", "coord_vals": orbit_vals},
                {"table_entry": "latitude", "units": "degrees_north",
                 "coord_vals": lat, "cell_bounds": lat_bnds},
                {"table_entry": "longitude", "units": "degrees_east",
                 "coord_vals": lon, "cell_bounds": lon_bnds},
            ]
            axisIds = [cmor.axis(**ax) for ax in axes]

            # Setup units and create variable to write using cmor - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
            varid = cmor.variable(outputVarName[fi] + '-orbit', outputUnits[fi],
                                   axisIds, missing_value=cmor_missing)

            d_asc = f_asc[inputVarName[fi]]
            d_des = f_des[inputVarName[fi]]
            v_asc = clean_values(d_asc, cmor_missing)
            v_des = clean_values(d_des, cmor_missing)
            values = np.stack([v_asc, v_des], axis=1)  # (ntime, orbit, nlat, nlon)

            sf = d_asc.encoding.get('scale_factor', 1.0)
            ao = d_asc.encoding.get('add_offset', 0.0)
            cmor.set_variable_attribute(varid, 'valid_min', 'f',
                float(d_asc.valid_min * sf + ao))
            cmor.set_variable_attribute(varid, 'valid_max', 'f',
                float(d_asc.valid_max * sf + ao))

            # Provenance info
            git_commit_number = obs4MIPsLib.get_git_revision_hash()
            path_to_code = os.getcwd().split('obs4MIPs-cmor-tables')[1]
            full_git_path = f"https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/{git_commit_number}/{path_to_code.lstrip('/')}"
            cmor.set_cur_dataset_attribute("processing_code_location", f"{full_git_path}")

            # Prepare variable for writing, then write and close file - see https://cmor.llnl.gov/mydoc_cmor3_api/#cmor_set_variable_attribute
            cmor.set_deflate(varid, 1, 1, 1)  # shuffle=1, deflate=1, deflate_level=1 - Deflate options compress file data
            cmor.write(varid, values, time_vals=time, time_bnds=time_bnds) # Write variable with time axis
            filename = cmor.close(varid, file_name=True)  # capture the path CMOR wrote
            cmor.close()
            print(f"File written for {year}-{month:02}: {filename}")

            # ---- post-process: add per-pixel time_of_observation + orbit flags ----
            ou.add_pixel_time(filename, outputVarName[fi], obstime, in_place=True,
                               orig_lat=lat, orig_lon=lon)
            ou.set_orbit_flags(filename)

        f_asc.close()
        f_des.close()

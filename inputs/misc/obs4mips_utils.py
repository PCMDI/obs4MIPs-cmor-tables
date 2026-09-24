"""
obs4mips_utils.py
------------------
Shared post-processing helpers for datasets whose sampling structure CMOR's
table-driven model doesn't natively support -- e.g. LEO satellite products
where each grid cell has its own true UTC acquisition time. Meant to be
called right after cmor.close() in a dataset's processing script, once per
CMOR-written file.
"""
from datetime import datetime, timezone

import numpy as np
import cftime
from netCDF4 import Dataset

AUX_TIME_NAME = "time_of_observation"
AUX_TIME_UNITS = "seconds since 1970-01-01 00:00:00"
AUX_TIME_CALENDAR = "standard"


def build_permutation(orig_coord, disk_coord, wrap=None, tol=1e-4):
    """
    Find `perm` such that disk_coord[perm[i]] ~= orig_coord[i] -- i.e. how to
    reorder data that's currently indexed by `orig_coord` so it lands in
    `disk_coord`'s actual index order. Handles a straight match, a reversal,
    or (wrap=360) a -180..180 vs 0..360 convention difference. Returns None
    if no consistent 1-to-1 match exists.
    """
    orig_coord = np.asarray(orig_coord, dtype="float64")
    disk_coord = np.asarray(disk_coord, dtype="float64")
    if orig_coord.shape != disk_coord.shape:
        return None

    def normalize(x):
        return np.mod(x, wrap) if wrap else x

    orig_n, disk_n = normalize(orig_coord), normalize(disk_coord)
    perm = np.empty(len(orig_n), dtype=int)
    used = np.zeros(len(disk_n), dtype=bool)
    for i, val in enumerate(orig_n):
        diffs = np.abs(disk_n - val)
        if wrap:
            diffs = np.minimum(diffs, wrap - diffs)
        j = int(np.argmin(diffs))
        if diffs[j] > tol or used[j]:
            return None
        perm[i] = j
        used[j] = True
    return perm


def get_axis_alignment(name, orig_vals, disk_vals):
    """Return (perm, note) mapping orig_vals' index order onto disk_vals'
    actual on-disk order, trying an exact match, then a reversal/reorder,
    then (for longitude) a 0..360 vs -180..180 wraparound."""
    perm = build_permutation(orig_vals, disk_vals)
    if perm is not None and np.array_equal(perm, np.arange(len(orig_vals))):
        return perm, "identity"
    if perm is not None:
        return perm, "REORDERED (e.g. CMOR enforcing stored_direction)"
    if name == "lon":
        perm = build_permutation(orig_vals, disk_vals, wrap=360.0)
        if perm is not None:
            return perm, "0..360 vs -180..180 WRAPAROUND"
    raise RuntimeError(
        f"Could not align '{name}': no consistent permutation found between "
        f"the values used to build obstime ({np.asarray(orig_vals)[:5]}...) and "
        f"the file's actual on-disk '{name}' ({np.asarray(disk_vals)[:5]}...)."
    )


def align_to_disk_order(array, lat_perm, lon_perm, lat_axis, lon_axis):
    """
    Reorder `array`'s lat/lon axes (at positions lat_axis/lon_axis) from the
    order they were built in into the file's actual on-disk order: result at
    [..., lat_perm[i], lon_perm[j], ...] = array[..., i, j, ...].
    Any leading dims (time, orbit, ...) are carried through unchanged.
    """
    moved = np.moveaxis(array, [lat_axis, lon_axis], [-2, -1])  # -> (..., lat, lon)
    out_moved = np.empty_like(moved)
    out_moved[..., lat_perm[:, None], lon_perm[None, :]] = moved
    return np.moveaxis(out_moved, [-2, -1], [lat_axis, lon_axis])


def obstime_from_time_dtime(ds, time_name="time", dtime_name="dtime"):
    """
    Many L2/L3 satellite products (e.g. ESACCI LST) don't give a
    per-pixel timestamp directly. Instead they give:
      - `time(time)`      a scalar reference time per file (commonly close
                           to file/day start, NOT a nominal noon/day value)
      - `dtime(time,lat,lon)`  per-pixel offset in seconds from that reference

    True per-pixel acquisition time = time + dtime. This returns that sum as
    float64 seconds since 1970-01-01, shape (ntime, nlat, nlon). Pixels where
    dtime is missing/invalid are returned as NaN -- add_pixel_time() below
    converts those to the aux variable's _FillValue.
    """
    t_var = ds[time_name]
    t_units = t_var.attrs.get("units") or t_var.encoding.get("units")
    calendar = t_var.attrs.get("calendar") or t_var.encoding.get("calendar", "standard")

    ref_vals = t_var.values
    if ref_vals.dtype == object or np.issubdtype(ref_vals.dtype, np.datetime64):
        # already decoded by xarray/xcdat (use_cftime=True -> cftime objects)
        ref_epoch = cftime.date2num(ref_vals, units=AUX_TIME_UNITS, calendar=AUX_TIME_CALENDAR)
    else:
        dates = cftime.num2date(ref_vals, units=t_units, calendar=calendar)
        ref_epoch = cftime.date2num(dates, units=AUX_TIME_UNITS, calendar=AUX_TIME_CALENDAR)

    dtime_da = ds[dtime_name]
    dtime_vals = np.array(dtime_da.values, dtype="float64")  # (ntime, nlat, nlon), seconds
    fill = getattr(dtime_da, "_FillValue", None)
    valid = np.isfinite(dtime_vals)
    if fill is not None:
        valid &= (dtime_vals != fill)

    obstime = ref_epoch[:, None, None] + dtime_vals
    return np.where(valid, obstime, np.nan)


def add_pixel_time(filepath, varname, obstime, in_place=True, fill_value=1.0e20,
                    orig_lat=None, orig_lon=None):
    """
    Add a per-pixel acquisition-time auxiliary coordinate to a CMOR-written
    file, and point `varname` at it via the CF `coordinates` attribute
    (CF section 5.7).

    filepath   : path to the file CMOR just wrote, e.g. from
                 cmor.close(varid, file_name=True)
    varname    : the CMOR out_name of the data variable, e.g. "ts"
    obstime    : numpy array of float64 seconds-since-1970-01-01, same shape
                 and dimension order as the data variable in the file. NaN
                 entries (e.g. from obstime_from_time_dtime's invalid pixels)
                 are written as `fill_value`.
    in_place   : True (default) patches the file directly -- safe to use
                 right after cmor.close(), since CMOR has already fully
                 flushed and closed it. Pass False for standalone/backfill
                 use on a file you don't own yet; writes
                 filepath + ".with_obstime.nc" instead of touching the
                 original.
    fill_value : value written where `obstime` is NaN (no valid observation
                 for that pixel/timestep).
    orig_lat, orig_lon : the lat/lon arrays `obstime` was actually built
                 against (e.g. the source file's own lat/lon, in the order
                 used to compute obstime). IMPORTANT: CMOR can silently
                 reorder a coordinate axis (and the data written via
                 cmor.write()) to satisfy a table's required
                 stored_direction -- e.g. reversing latitude if the source
                 data runs north-to-south. Since obstime is written by THIS
                 function, bypassing cmor.write() entirely, it has no way to
                 pick up that reordering on its own. Passing orig_lat/
                 orig_lon lets this function compare them against the file's
                 actual on-disk lat/lon and reindex obstime to match before
                 writing -- keeping it consistent with ts/tsuind in the same
                 file. If omitted, obstime is written as-is (matches
                 pre-existing behavior; fine only if you've independently
                 confirmed CMOR did not reorder anything for this dataset).
    """
    if in_place:
        outfile = filepath
    else:
        import shutil
        outfile = filepath.replace(".nc", ".with_obstime.nc")
        shutil.copy2(filepath, outfile)

    with Dataset(outfile, "r+") as ds:
        data_var = ds.variables[varname]

        if obstime.shape != data_var.shape:
            raise ValueError(
                f"obstime shape {obstime.shape} != {varname} shape {data_var.shape}"
            )

        if orig_lat is not None or orig_lon is not None:
            dim_names = data_var.dimensions
            lat_axis = dim_names.index("lat") if "lat" in dim_names else dim_names.index("latitude")
            lon_axis = dim_names.index("lon") if "lon" in dim_names else dim_names.index("longitude")
            disk_lat = ds.variables[dim_names[lat_axis]][:]
            disk_lon = ds.variables[dim_names[lon_axis]][:]

            lat_perm, lat_note = get_axis_alignment("lat", orig_lat, disk_lat) \
                if orig_lat is not None else (np.arange(obstime.shape[lat_axis]), "not checked")
            lon_perm, lon_note = get_axis_alignment("lon", orig_lon, disk_lon) \
                if orig_lon is not None else (np.arange(obstime.shape[lon_axis]), "not checked")

            if lat_note != "identity" or lon_note != "identity":
                print(f"  add_pixel_time: realigning obstime to on-disk grid "
                      f"(lat: {lat_note}; lon: {lon_note})")
                obstime = align_to_disk_order(obstime, lat_perm, lon_perm, lat_axis, lon_axis)

        obstime_filled = np.where(np.isfinite(obstime), obstime, fill_value)

        if AUX_TIME_NAME in ds.variables:
            aux = ds.variables[AUX_TIME_NAME]
        else:
            aux = ds.createVariable(
                AUX_TIME_NAME, "f8", data_var.dimensions,
                fill_value=fill_value, zlib=True, complevel=4
            )
        aux[:] = obstime_filled
        aux.standard_name = "time"
        aux.long_name = "time of observation for each grid cell"
        aux.units = AUX_TIME_UNITS
        aux.calendar = AUX_TIME_CALENDAR
        aux.comment = (
            "Per-pixel UTC acquisition time from the LEO overpass; varies "
            "smoothly across the swath. See CF conventions section 5.7."
        )

        existing = getattr(data_var, "coordinates", "").split()
        if AUX_TIME_NAME not in existing:
            data_var.coordinates = " ".join(existing + [AUX_TIME_NAME])

        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        note = (
            f"{stamp}: added '{AUX_TIME_NAME}' auxiliary coordinate "
            f"via obs4mips_utils.add_pixel_time()"
        )
        ds.history = f"{note}\n{ds.history}" if hasattr(ds, "history") else note

    return outfile


def set_orbit_flags(filepath, orbit_varname="orbit",
                     flag_values=(0, 1), flag_meanings="ascending descending"):
    """
    Attach CF flag_values/flag_meanings to the orbit coordinate variable.
    Needed because cmor.set_variable_attribute() only supports character-type
    attributes today, so a numeric flag_values array has to be patched on
    after cmor.close() rather than set through CMOR's own API.
    """
    with Dataset(filepath, "r+") as ds:
        orbit_var = ds.variables[orbit_varname]
        orbit_var.flag_values = np.array(flag_values, dtype=orbit_var.dtype)
        orbit_var.flag_meanings = flag_meanings

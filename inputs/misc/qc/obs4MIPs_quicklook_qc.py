import argparse
import numpy as np
import xarray as xr
import sys
import matplotlib.pyplot as plt

def qc_var_basic(ds, varname):
    if varname not in ds.variables:
        print(f"[FAIL] Variable '{varname}' not found in file")
        sys.exit(1)

    v = ds[varname]

    print(f"[PASS] Variable '{varname}' found")
    print(f"       dimensions : {v.dims}")
    print(f"       shape      : {v.shape}")

    units = v.attrs.get("units", "MISSING")
    print(f"       units      : {units}")

    fill = v.attrs.get("_FillValue", v.encoding.get("_FillValue", None))
    print(f"       _FillValue : {fill}")

    miss = v.attrs.get("missing_value", v.encoding.get("missing_value", None))
    print(f"       missing_value : {miss}")

    if fill is not None and miss is not None and fill != miss:
        print("[WARN] _FillValue != missing_value")

    # ---- valid_min / valid_max sanity ----
    vmin_attr = v.attrs.get("valid_min", v.encoding.get("valid_min", None))
    vmax_attr = v.attrs.get("valid_max", v.encoding.get("valid_max", None))
    print(f"       valid_min: {vmin_attr}")
    print(f"       valid_max: {vmax_attr}")

    time = ds["time"]
    time_bnds = ds["time_bnds"]

    tunit=time.attrs.get("units", time.encoding.get("units",None))
    print(f"Time units      : {tunit}")
    print(f"Time min/max    : {time.min().values}, {time.max().values}")
#   print(f"Time : {time.values}")
    tbunit=time_bnds.attrs.get("units", time_bnds.encoding.get("units",None))
    print(f"Time bounds units : {tbunit}")
    print(f"Time_bnds min/max : {time_bnds.min().values}, {time_bnds.max().values}")
#   print(f"Time_bnds : {time_bnds.values}")

    # ---- t = 0 slice ----
    try:
        data0 = v.isel(time=0).values
    except Exception as e:
        print(f"[FAIL] Could not extract time=0 slice: {e}")
        sys.exit(1)

    print(f"[PASS] Extracted t=0 slice with shape {data0.shape}")

    mask = ~np.isfinite(data0) | (data0 == fill)
    nan_count = np.isnan(data0).sum()
    print(f"       NaN count  : {nan_count}")
    fill_count = np.sum(mask)
    print(f"       Fill count : {fill_count}")

    valid = data0[~mask]

    if valid.size == 0:
        print("[FAIL] All values are missing at t=0")
        return

    vmin = valid.min()
    vmax = valid.max()
    vmean = valid.mean()

    print(f"[PASS] t=0 stats (excluding fill)")
    print(f"       min  = {vmin}")
    print(f"       max  = {vmax}")
    print(f"       mean = {vmean}")

    # ---- quicklook plot: t=0 ----
    try:
        lat = ds["lat"].values
        lon = ds["lon"].values
    except KeyError:
        print("[WARN] lat/lon not found, skipping plot")
        return

    plt.figure(figsize=(8, 4))

    # Mask missing for plotting
    if varname.lower() in ("pr", "precip", "precipitation"):
        plot_data = np.ma.masked_where((mask) | (data0 <= 0), data0)
    else:
        plot_data = np.ma.masked_where(mask, data0)


    plt.pcolormesh(lon, lat, plot_data, shading="auto")
    plt.colorbar(label=units)
    plt.title(f"{varname} (t=0)")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.tight_layout()
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="obs4MIPs quick-look QC (v0: basic variable checks)"
    )
    parser.add_argument("-var", required=True, help="Variable name (e.g., pr, rsut)")
    parser.add_argument("-dataset", required=True, help="Path to NetCDF file")

    args = parser.parse_args()

    print(f"\nOpening file: {args.dataset}")
#   ds = xr.open_dataset(args.dataset, mask_and_scale=False, decode_times=False)
    ds = xr.open_dataset(args.dataset, decode_times=True)

    qc_var_basic(ds, args.var)

    print("\nQC completed.\n")


if __name__ == "__main__":
    main()


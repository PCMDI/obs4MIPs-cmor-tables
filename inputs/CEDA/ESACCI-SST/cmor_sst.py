import os

import cmor
import glob
import numpy as np
import xarray as xr
import pandas as pd
import logging
import argparse

# ESACCI-SST v3.0.1 sea surface temperature input files are obtained from the surftemp.net service (https://surftemp.net/regridding/index.html)
# this service can be used to regrid daily SST data at 0.05 degrees to 0.25 degrees at daily and monthly temporal resolution

# this utility can then be used to convert these input files to obs4MIPs compliant files using CMOR
# to run this script, a miniforge python environment can be set up using the commands

# mamba create -n CMOR -c conda-forge cmor==3.10 xarray netcdf4
# mamba activate CMOR

# this utiity has been run with CMOR 3.10

class CMORConverter:

    def __init__(self,output_folder, cmor_home='../../..', monthly=False):
        input_table_path = os.path.join(cmor_home,"Tables")
        self.logger = logging.getLogger("CMORDailyConverter")
        self.output_folder = output_folder
        self.input_table_path = input_table_path
        self.cmor_sst = None

        cmor.setup(inpath=self.input_table_path,
                   set_verbosity=cmor.CMOR_NORMAL,
                   netcdf_file_action=cmor.CMOR_REPLACE)

        if monthly:
            cmor.dataset_json("CMOR_sst_input_monthly.json")
            cmor.load_table("obs4MIPs_Omon.json")
        else:
            cmor.dataset_json("CMOR_sst_input_daily.json")
            cmor.load_table("obs4MIPs_Oday.json")

        self.oldcwd = os.getcwd()
        os.chdir(self.output_folder)


    def convert(self, input_path):

        ds = xr.open_dataset(input_path)

        da = ds["sst"]

        (ntime, nlat, nlon) = da.shape

        # convert the data from Kelvin to degrees Centigrade
        sst_data = da.data - 273.15

        if self.cmor_sst is None:
            # on the input file, set up the CMOR  variable
            lat = ds.lat.data
            lat_bnds = np.zeros(shape=(1 + nlat,))

            lat_bnds[0:nlat] = ds.lat_bnds[:, 0].data.flatten()
            lat_bnds[nlat] = ds.lat_bnds[-1, 1].data

            lon = ds.lon.data
            lon_bnds = np.zeros(shape=(1 + nlon,))

            lon_bnds[0:nlon] = ds.lon_bnds[:, 0].data.flatten()
            lon_bnds[nlon] = ds.lon_bnds[-1, 1].data

            cmorLat = cmor.axis("latitude",
                                coord_vals=lat,
                                cell_bounds=lat_bnds,
                                units="degrees_north")

            cmorLon = cmor.axis("longitude",
                                coord_vals=lon,
                                cell_bounds=lon_bnds,
                                units="degrees_east")

            cmorTime = cmor.axis("time",
                                 units="days since 1980")

            axes = [cmorTime, cmorLat, cmorLon]
            self.cmor_sst = cmor.variable("tos", "degC", axes)
            cmor.set_deflate(self.cmor_sst, 1, 1,
                            5);  # shuffle=1,deflate=1,deflate_level=5 - Deflate options compress file data

        time = ds.time.data
        time_bnds = ds.time_bnds.data.flatten()

        converter = np.vectorize(
            lambda dt64: (pd.to_datetime(dt64) - pd.Timestamp(1980, 1, 1, 0, 0, 0)).total_seconds() / 86400)

        time = converter(time)
        time_bnds = converter(time_bnds)

        cmor.write(self.cmor_sst, sst_data, time_vals=time, time_bnds=time_bnds)


    def close(self):
        filename = cmor.close(self.cmor_sst, file_name=True)
        self.logger.info(f"Written: {filename}")
        os.chdir(self.oldcwd)

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--cmor-home", default='../../..', help="Path to the obs4MIPS-cmor-tables repo")
    parser.add_argument("--input-paths", default="????????_regridded_sst.nc", help="Path to the input fils to process")
    parser.add_argument("--monthly", action="store_true", help="Indicate that the input files contain monthly rather than daily data")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    converter = CMORConverter(".", cmor_home=args.cmor_home, monthly=args.monthly)

    for input_path in sorted(glob.glob(args.input_paths)):
        print(f"Processing {input_path}")
        converter.convert(input_path)
    converter.close()

if __name__ == '__main__':
    main()


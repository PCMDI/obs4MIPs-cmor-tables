
This code must be run with CMOR 3.2.6 or a more recent version.

CMOR can be obtained via Anaconda at https://anaconda.org/conda-forge/cmor once the user has installed Anaconda (https://continuum.io)

More information about CMOR is available at: https://cmor.llnl.gov

If you have any difficulties, please contact us at obs4MIPs-admin@llnl.gov

The code in this directory entitled `runCMOR-RSS-xcdat-monthly-netcdf.py` uses XCDAT to read RSS SMAP V5 SSS data before sending it to CMOR.  XCDAT is available via conda-forge at: //anaconda.org/conda-forge/xcdat.  More specific information on this demo is given below.

## XCDAT Monthly netCDF4 Code
The code entitled `runCMOR-RSS-xcdat-monthly-netcdf.py` requires external data files which need to be downloaded from the Remote Sensing Systems (RSS) FTP.  Specifically, this code uses the 12 netCDF4 monthly averaged RSS SMAP salinity files from 2018 on ftp.remss.com/smap/SSS/V05.0/FINAL/L3/monthly/2018/.  Users must first register for a free account on the RSS website to access these data.  This can be done using the following link: register.remss.com.

Once downloaded, these data can be placed in a folder of the user's choosing.  This folder path must be changed in the appropriate line of `runCMOR-RSS-xcdat-monthly-netcdf.py`.

Note that this particular code is useable for cases in which a user has **multiple netCDF4 files comprising a dataset** they wish to make obs4MIPs compliant (e.g., SMAP salinity) and there is **only one time value associated with each file** (i.e., the variable representing the `T` coordinate in each file is a single-valued array).  For example, each of the SMAP salinity files used in this code contain a `time` variable, which is a single-valued array corresponding to the time associated with the monthly averaged SMAP salinity measurement (in this case, the `time` value is the center of the month that the data have been averaged over with units of `seconds since 2000-01-01T00:00:00Z`).  

If the netCDF4 file or files that the user wishes to make obs4MIPs compliant contain `time` arrays with more than one value, then the `runCMOR-RSS-xcdat-monthly-netcdf.py` code will need to be appropriately altered to fit the user's needs.

## Further Information
[More details on the process of preparing obs4MIPs compliant data are available](https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/README.md)


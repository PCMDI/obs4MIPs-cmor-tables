
The software and utilites used in this demo are available via Anaconda (https://continuum.io) and include: <br>
<br>
**CMOR** <br>
https://cmor.llnl.gov <br>
https://anaconda.org/conda-forge/cmor <br>
<br>
**xarray** <br>
https://docs.xarray.dev/en/stable <br>
https://anaconda.org/conda-forge/xarray <br> 
<br>
**xcdat** <br>
https://xcdat.readthedocs.io/en/stable <br>
https://anaconda.org/conda-forge/xcdat <br>
<br>
Running the demo python code reads in the sample data via xarray, generates grid bounds via xcdat, and outputs a demo file using CMOR.  The demo must be run with CMOR 3.2.6 or a more recent version.  To run the demo file, all contents of this directory (including the /Tables subdirectory) must be saved locally, and a conda envirnment must be created including CMOR, xarray and xcdat. If python needs to be installed, it too is available via anaconda (https://anaconda.org/conda-forge/python). Once that is done, execute the following: <br>
    
python runCMORdemo_CMAP-V1902.py

If you have any difficulties, please contact the obs4MIPs team at obs4MIPs-admin@llnl.gov

[More details on the process of preparing obs4MIPs compliant data are available in /inputs of this repo.](https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/README.md)





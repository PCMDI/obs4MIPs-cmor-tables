
The software and utilites used in this demo are available via Anaconda (https://continuum.io) and include: 

**Python**\
https://www.python.org \
https://anaconda.org/conda-forge/python 
\
\
**CMOR**\
https://cmor.llnl.gov 
\  
https://anaconda.org/conda-forge/cmor 
\
\
**xarray**\
https://docs.xarray.dev/en/stable 
\
https://anaconda.org/conda-forge/xarray 
\   
\
**xcdat**\
https://xcdat.readthedocs.io/en/stable 
\
https://anaconda.org/conda-forge/xcdat 
\
\
Running the demo python code reads in the sample data via xarray, generates grid bounds via xcdat, and outputs a demo file using CMOR.  The demo must be run with CMOR 3.2.6 or a more recent version.  To run the demo file, all contents of this directory (including the /Tables subdirectory) must be saved locally. Before executing the code, a conda envirnment must be created including python, CMOR, xarray and xcdat.  Once that is done, execute the following: 
\    
python runCMORdemo_CMAP-V1902.py

If you have any difficulties, please contact the obs4MIPs team at obs4MIPs-admin@llnl.gov

[More details on the process of preparing obs4MIPs compliant data are available](https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/README.md)





This file describes basic contents and use of files to run a demo1 of how to use CMOR3 for obs4MIPs.
It builds on the original demo directory set up by PD
PjG  Last update 09202016

Using a build of CMOR or UV-CDAT the following should be possible:

>python generate_cmor3_tables.py

#This script downloads downloads from github the latest tables which continue to be modified slightly as the CMIP6 specifications are finalized.  It is currently set up to generate one table at a time.

>python update_obs4mips_CMOR3_CV.py

# This script puts the "Controlled Vocabulary" necessary to run CMOR in a json file.

> python rss_prw_run_cmor_demo.py

# User may need to change paths as desired, but this should produce some test data. 

 




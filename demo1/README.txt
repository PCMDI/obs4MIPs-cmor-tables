This file describes basic how to run demo1 which uses CMOR3 to produce a sample obs4MIPs dataset.  It builds on the original demo directory set up by PJD.

PjG  Last update 05012017

Follow these steps to run demo1:

1) Downloads:  https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/demo1/update_obs4mips_CMOR3_CV.py
   by clicking on the link and then selecting the "raw" tab.
   Repeat the process for: https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/demo1/generate_cmor3_tables.py

2) Make sure you are in a conda envirnment that includes CMOR3, then execute the following:

   >python generate_cmor3_tables.py
   
This script downloads downloads from github the latest tables which continue to be modified slightly as the CMIP6 specifications are finalized.  It is currently set up to generate one table at a time.

3) Next, execute the following:

   >python update_obs4mips_CMOR3_CV.py

   This script retrieves the lastest obs4MIPs "Controlled Vocabulary" necessary to run CMOR in a single json file.

4) With the obs4MIPs CMOR3 tables and CV's updated, execute demo1: 

   > python rss_prw_run_cmor_demo.py


The user may need to change paths as desired, but this should produce some test data. 

 





## Preparation of obs4MIPs compliant data at PCMDI

PCMDI prepares some datasets to be made obs4MIPs compliant in support of PCMDI's research needs. Because PCMDI does not curate climate observations, it prepares obs4MIPs compliant data as a 3rd party.  PCMDI uses the following utilites:

[Climate Model Output Rewriter (CMOR)](https://cmor.llnl.gov) (Currently, all obs4MIPs data needs to be prepared with CMOR)

[Community Data Analysis Tools (CDAT)](https://cdat.llnl.gov/) (other options are possible)

Both CMOR and CDAT can be obtained via Conda-forge.  Efforts are currently underway to modernize the essential capabilities of CDAT with [XCDAT](https://xcdat.readthedocs.io/en/latest), and xarray based utility.  


**Recipie:**

1) Retrieve desired data
2) Submit a proposal for a new source_id on this repo (template provided when creating an issue)
3) Create download Readme.txt from which text will be extracted when preparing data
4) Prepare input table for running CMOR
5) Prepare python script for reading in data an writing with CMOR.

**Example**

Sample README (txt), input table (json) and script using CDAT and CMOR (python):
https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/pcmdi/RSS

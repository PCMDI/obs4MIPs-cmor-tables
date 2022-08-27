## Recipie for preparation of obs4MIPs compliant data (work in progress)

Currently, all obs4MIPs compliant data products need to be prepared with [Climate Model Output Rewriter (CMOR)](https://cmor.llnl.gov) 

CMOR can be obtained via conda-forge.  


**Recipie overview**

1) Retrieve desired data.
2) Submit a proposal for a new source_id on this repo (a template is provided when creating an issue)
3) When a new source_id is provided, use "download-source_id.json" to document how data was downloaded. 
4) Prepare input table for running CMOR
5) Prepare python script for reading in data an writing with CMOR.
6) Execute script

**Example**

Sample README (txt), input table (json) and script using CDAT and CMOR (python):

https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/pcmdi/RSS

**Recipie**

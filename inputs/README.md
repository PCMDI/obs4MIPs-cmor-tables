## Recipie for preparation of obs4MIPs compliant data (work in progress)

Currently, all obs4MIPs compliant data products need to be prepared with [Climate Model Output Rewriter (CMOR)](https://cmor.llnl.gov).  CMOR can be obtained [via conda-forge](https://cmor.llnl.gov/mydoc_cmor3_conda/).  


**Recipie overview**

1) Retrieve data desired to be made obs4MIPs compliant.
2) Register a new source_id on this repo (a template is provided when creating an issue)
3) When a new source_id is provided, use "download-source_id.json" to document how data was downloaded. 
4) Prepare input table for running CMOR
5) Prepare python script for reading in data an writing with CMOR.
6) Execute script

**Example**

Sample README (txt), input table (json) and script using CDAT and CMOR (python):

https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/pcmdi/RSS

**Recipie**

1) Retrieve data desired to be made obs4MIPs compliant.  Through the process outlined here, data already publically available can be made obs4MIPs compliant. Typically, somebody will retrieve the data from the internet before beginning this process. 

2) Register a new source_id. Once data has been downloaded, an issue can be submited on this repo with a proposal for a new "source_id".  The source_id is used for to identify the product/version and generally closely resembles an existing identifier but is slightly modified to be consistent with CMIP/obs4MIPs conventions.  For example:  A compliant source_id for "GPCP 2.4" is "GPCP-2-4".  More information on the source_id is available in [Table 1 of the obs4MIPs data specifications](https://docs.google.com/document/d/1FXXBhUh71Hjus557ZTD3EKPi_2zxeLvi1aICXOjVYPc/edit#heading=h.7zmnv8xlfe08). 
  

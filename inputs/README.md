## Recipie for preparation of obs4MIPs compliant data (work in progress)

Currently, all obs4MIPs compliant data products need to be prepared with [Climate Model Output Rewriter (CMOR)](https://cmor.llnl.gov).  CMOR can be obtained [via conda-forge](https://cmor.llnl.gov/mydoc_cmor3_conda/).  The recipie and demos below describe the process of making a copy of an observational data product that is obs4MIPs compliant.  This is in support of, but independent of the process of "publishing" obs4MIPs compliant data to ESGF.  


**Recipie overview** (detailed below)

1) Identify datset to prepare as obs4MIPs compliant.
2) Retrieve data desired to be made obs4MIPs compliant.
3) Register a new source_id on this repo (a template is provided when creating an issue)
4) When a new source_id is provided, use "download-source_id.json" to document how data was downloaded. 
5) Prepare input table for running CMOR
6) Prepare python script for reading in data an writing with CMOR.
7) Execute script

**Example**

Sample README (txt), input table (json) and script using CDAT and CMOR (python):

https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/inputs/pcmdi/RSS

**Recipie**

1) _*Identify datset to prepare as obs4MIPs compliant.*_ Before a particular version of a data product is prepared to be made obs4MIPs compliant, one should confirm if it is already available as an obs4MIPs product on [ESGF](https://esgf-node.llnl.gov/search/obs4mips/).  How the precise version of a dataset is identified is still being improved but ultimately it is hoped that this can be identified from the obs4MIPs source_id. The source_id is intended to identify the product/version and generally closely resembles an existing identifier but is slightly modified to be consistent with CMIP/obs4MIPs conventions.  For example:  A compliant source_id for "GPCP 2.4" is "GPCP-2-4".  More information on the guidelines for constructing a source_id is available in [Table 1 of the obs4MIPs data specifications](https://docs.google.com/document/d/1FXXBhUh71Hjus557ZTD3EKPi_2zxeLvi1aICXOjVYPc/edit#heading=h.7zmnv8xlfe08).  Not all obs4MIPs products currently meet this criteria but if the precise product/version is not evident from the source_id there may be sufficient information in the history attribute of the netCDF file to determine the original product/version.  Note, even if there is a particular data product/version available on ESGF via obs4MIPs there are may be reasons why somebody may wish to prepare another obs4MIPs compliant copy, e.g., to provide the data and a different horizontal resolution.  

2) _*Retrieve data desired to be made obs4MIPs compliant*_.  Through the process outlined below, publically available data can be downloaded and processed to be made obs4MIPs compliant. To accomplish this, typically a dataset is downloaded from the internet before beginning the process.  The examples on this repo assume the data downloaded is in netCDF format, but it does not have to be.  The next step is to determine if this version of the dataset already has a registered obs4MIPs "source_id".  

3) _*Register a new source_id*_, if it does not already exists. Once data has been downloaded, an issue can be submited on this repo with a proposal for a new "source_id".   
  

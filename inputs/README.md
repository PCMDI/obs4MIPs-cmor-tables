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

1) _*Identify datset to prepare as obs4MIPs compliant.*_ Before a particular version of a data product is prepared to be made obs4MIPs compliant, one should confirm if it is already available as an obs4MIPs product on [ESGF](https://esgf-node.llnl.gov/search/obs4mips/).  How the precise version of a dataset is identified is still being improved but ultimately it is hoped that this can be identified from the obs4MIPs source_id. The source_id is intended to identify the product/version and generally closely resembles an existing identifier but is slightly modified to be consistent with CMIP/obs4MIPs conventions.  For example:  A compliant source_id for "GPCP 2.4" is "GPCP-2-4".  More information on the guidelines for constructing a source_id is available in [Table 1 of the obs4MIPs data specifications](https://docs.google.com/document/d/1FXXBhUh71Hjus557ZTD3EKPi_2zxeLvi1aICXOjVYPc/edit#heading=h.7zmnv8xlfe08).  Not all obs4MIPs products currently meet this criteria but if the precise product/version is not evident from the source_id there may be sufficient information in the history attribute of the netCDF file to determine the original product/version.  Note, even if there is a particular data product/version available on ESGF via obs4MIPs there are may be reasons why somebody may wish to prepare another obs4MIPs compliant copy, e.g., to provide the data at a different horizontal resolution.  

2) _*Retrieve data desired to be made obs4MIPs compliant*_.  To accomplish this, typically the "original" version of a dataset is downloaded from the internet before beginning the process.  The examples on this repo assume the data downloaded is in netCDF format, but it does not have to be.  In general, obs4MIPs data products are prepared from publically available data (but not obs4MIPs compliant) via the official curators of the data or a recognized data center such as the [U.S. National Center for Environmental Information](https://www.nesdis.noaa.gov/data-research-services/data-collections).     

3) _*Register a new source_id*_, if it does not already exist. Once data has been downloaded, an issue can be submited on this GitHub repo with a proposed "source_id".  Somebody from the obs4MIPs team will quickly review this information and enter it into the obs4MIPs database of source_id's or propose an alternative if it does not conform to the obs4MIPs data specifications for the source_id.  When opening the an Issue the template below shows up and one simply needs to replace the information with the GPCP example with their own proposed source_id.

***

If you are *registering content* (RC) for obs4MIPs, please fill out the requested information below.   If you want to create an issue about something else, please delete the text below and title your issue as appropriate.  

To register (or edit) some or all of the obs4MIPs RC, please title this github issue as follows:  
"RC for " + your source_name (as you define below), and indicate if you are modifying your input from an earlier issue

________________________________________________________________________________________________________
The following are required registered content (with example content for each item in **bold**). Please replace the example text below with your information to the right of the equal sign (DO NOT MAKE ANY CHANGES TO THE LEFT HAND SIDE OF THE EQUAL SIGN):
1) source_id['source_id'][key][**'source_name'**] = 'GPCP'
2) source_id['source_id'][key][**'release_year'**] = '2011'
3) source_id['source_id'][key][**'source_description'**] = 'Global Precipitation Climatology Project'
4) source_id['source_id'][key][**'source_version_number'**] = '2.3'
5) source_id['source_id'][key][**'institution_id'**] = 'UofMD'
6) source_id['source_id'][key][**'region'**] = 'global'
7) source_id['source_id'][key][**'source_type'**] = 'satellite_merged'
8) A list of CMIP variable_ids that the above information refers to.  In most cases it will only be for one variable_id.  If it is for more than one, please make sure your source_description is sufficiently general to apply to all relevant variable_ids.

________________________________________________________________________________________________________

See note 14 and Appendix II of the obs4MIPs data specifications (https://goo.gl/jVZsQl) for more information regarding registered content, and feel free to ask questions!

***



4) _*Prepare a "download_source_id"*_.  Ultimately we strive in obs4MIPs to have a clear indication of the origins of the data was processed to produce an obs4MIPs compliant dataset.  The way this is currently done is to prepare   
  

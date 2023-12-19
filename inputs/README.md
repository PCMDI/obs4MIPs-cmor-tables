## Recipe for the preparation of obs4MIPs compliant data (work in progress)

The recipe below describes the process of preparing an obs4MIPs-compliant dataset. This typically involves copying information from the provided demo and modifying it as necessary to prepare a new obs4MIPs-compliant dataset.  **If you are interested to contribute an obs4MIPs-compliant dataset, please alert the obs4MIPs data preparation team (obs4MIPs-admin@llnl.gov) so that we can advise you on how to proceed.** Note the process of preparing obs4MIPs-compliant data is in support of, but independent of the process of "publishing" obs4MIPs-compliant data to ESGF.   

## Key resources (utilities, formats, and conventions)

Currently, all obs4MIPs-compliant data products must be prepared with the [Climate Model Output Rewriter (CMOR)](https://cmor.llnl.gov).  **CMOR** is used by most CMIP modeling groups to prepare their model output before publishing it to ESGF.  CMOR can be obtained [via conda-forge](https://cmor.llnl.gov/mydoc_cmor3_conda/), a community-led collection of recipes, build infrastructure and distributions for the [conda package manager](https://docs.conda.io/projects/conda/en/latest).  By preparing a simple [python](https://python.org) script (example discussed in demo identified below) and an input [**JSON**](https://json.org) file, CMOR is used to prepare an obs4MIPs-compliant dataset.      

The [obs4MIPs data specifications (**ODS**)](https://pcmdi.github.io/obs4MIPs/dataStandards.html) are technically aligned with the preparation of climate model output prepared for the Coupled Model Intercomparison Project (CMIP), with all metadata managed in JSON files.

---

**Recipe overview** (detailed below)

1) Identify public dataset to be made obs4MIPs-compliant and retrieve for processing locally.
2) Fill out the dataset proposal form.
3) Register a new source_id via this Github repo and fill out data submission form.
4) Prepare input table and python script for reading data and writing with CMOR.
5) Execute script
6) Create a GitHub issue or branch to include the input JSON and processing code in this repository. 


**Example**

Input table (json) and script using CDAT and CMOR (python):  https://github.com/PCMDI/obs4MIPs-cmor-tables/tree/master/demo

**Recipe**

1) _*Identify datset to prepare as obs4MIPs compliant.*_ Before a particular version of a data product is prepared to be made obs4MIPs compliant, one should confirm if it is already available as an obs4MIPs product on [ESGF](https://aims2.llnl.gov/search) - just ask us if you are unsure. Typically the "original" version of a dataset is downloaded locally before beginning the process of preparing an obs4MIPs-compliant version.  The examples on this repo assume the data downloaded is in netCDF format, but it does not have to be.  In general, obs4MIPs data products are prepared from publically available data (that is not yet obs4MIPs-compliant) via the official curators of the data, or a recognized data center such as the [U.S. National Center for Environmental Information](https://www.nesdis.noaa.gov/data-research-services/data-collections).     

2) [Fill out the data proposal form](https://bit.ly/obs4MIPs-submit).  Please ask us if you have any questions about the requested information.

3) _*Register a new source_id*_, if it does not already exist. Once the data has been obtained, an issue can be submitted on this GitHub repo with a proposed "source_id".  Somebody from the obs4MIPs team will quickly review this information and enter it into the obs4MIPs database of source_id's or propose an alternative if it does not conform to the obs4MIPs data specifications for the source_id.  When opening an issue, the template below is included, so one needs to replace the information with the example (GPCP) with their own proposed source_id.  The source_id is intended to identify the product/version and generally closely resembles an existing identifier but may be slightly modified to be consistent with CMIP/obs4MIPs conventions.  For example: A compliant source_id for "GPCP 2.4" is "GPCP-2-4".  More information on the guidelines for constructing a source_id is available in [Table 1 of the obs4MIPs data specifications](https://docs.google.com/document/d/1FXXBhUh71Hjus557ZTD3EKPi_2zxeLvi1aICXOjVYPc/edit#heading=h.7zmnv8xlfe08).  (Not all obs4MIPs products currently published on ESGF meet these criteria but if the precise product/version is not evident from the source_id there may be sufficient information in the history attribute of the netCDF file to determine the original product/version).  As of 1 January 2024 for a dataset to be obs4MIPs-compliant its source_id must adhere to the ODS specifications.  

________________________________________________________________________________________________________
**Template provided when submitting a new issue on the GH repository**

If you are *registering content* (RC) for obs4MIPs, please fill out the requested information below.   If you want to create an issue about something else, please delete the text below and title your issue as appropriate.  

To register (or edit) some or all of the obs4MIPs RC, please title this GitHub issue as follows:  
"RC for " + your source_name (as you define below), and indicate if you are modifying your input from an earlier issue


The following are required registered content (with example content for each item in **bold**). Please replace the example text below with your information to the right of the equal sign (DO NOT MAKE ANY CHANGES TO THE LEFT-HAND SIDE OF THE EQUAL SIGN):
1) source_id['source_id'][key][**'source_name'**] = 'GPCP'
2) source_id['source_id'][key][**'release_year'**] = '2011'
3) source_id['source_id'][key][**'source_description'**] = 'Global Precipitation Climatology Project'
4) source_id['source_id'][key][**'source_version_number'**] = '2.3'
5) source_id['source_id'][key][**'institution_id'**] = 'UofMD'
6) source_id['source_id'][key][**'region'**] = 'global'
7) source_id['source_id'][key][**'source_type'**] = 'satellite_merged'
8) A list of CMIP variable_ids that the above information refers to.  In most cases, it will only be for one variable_id.  If it is for more than one, please make sure your source_description is sufficiently general to apply to all relevant variable_ids.

See note 14 and Appendix II of the obs4MIPs data specifications (https://goo.gl/jVZsQl) for more information regarding registered content, and feel free to ask questions!
________________________________________________________________________________________________________


4) _*Prepare input table for running CMOR*_.  [An example input table](https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/demo/CMAP-V1902.json).  The simplest thing to do is to save this file, rename it, and replace the demo content with the relevant information for a new source_id or dataset.  Typically, this involves only making changes to the following attributes:  "contact", "grid", "grid_label", "institution_id", "nominal_resolution", "references", "outpath", "source_id", "title", "variant_info" and "variant_label". We strive for all obs4MIPs products to clearly identify the origins of the data (i.e., where and when did the person preparing the obs4MIPs compliant product obtain the original data).  This information can be documented in the last three attributes of the example input table identified above via the following attributes: "originData_URL" , "originData_retrieved", and "originData_notes".

5)_*Prepare python script for reading in data an writing with CMOR._*  This is often the most time consuming aspect of preparing an obs4MIPs-compliant data set, but the examples provided on this repo are helping streamline the process.  It involves preparing a simple Python script to read the original data downloaded in advance.  As with the steps before, one can start by downloading a [demo python script](https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/demo/runCMORdemo_CMAP-V1902.py), renaming it accordingly, and modifying as needed. The examples provided illustrate how data already in netCDF can be processed to be obs4MIPs compliant, but in principle, input data in other formats can be used if the user can process the data using CMOR. 

6) _*Execute script.*_  The processed data will be located in a directory defined in the input_table: outpath + output_path_template, the former being the base directory (where the user wants to output the data). The latter being a directory template explicitly defined for obs4MIPs (<activity_id>/<institution_id>/<source_id>/<frequency>/<variable_id>/<grid_label>/<version>). 
  
7) _*Create an issue to include the processing code in this repository.*_  **Please note a dataset is not obs4MIPs-compliant unless the source_id is registered and the input json and python scripts used for processing are included in this repo.**  This ensures transparency in the obs4MIPs process. 
    

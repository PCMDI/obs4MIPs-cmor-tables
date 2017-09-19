<Please fill out the requested information and delete irrelevant information from the template below before submitting your issue.>  

To register (or edit) some or all of the obs4MIPs "registered content" (RC), please title this github issue as follows:  

"registration information for [acronym describing your dataset - see source_name below]"

The following are required registered content (with an example): 
1) source_name             = 'GPCP'
2) release_year            = 2011
3) source_description
4) source_version_number
5) Instituion_id
6) region 
7) source_type


'source_id' -- The same as the first part of source (before the release year), but with certain forbidden characters replaced by hyphens. The source_id (and source_label) must be constructed from the following limited character set: a-z, A-Z, 0-9 and the hyphen ("-").

'institution_id' -- Short acronym suitable for search interfaces and sub-directory names (should limit the characters used to the following set: a-z, A-Z, 0-9, and "-"), along with full name and address of institution, likely to include: laboratory/group name, hosting institution name, city, state/province and postal-code, country (no restriction on character set).
 


Example: institution_id registration [with issue titled "registration of PCMDI"]

"PCMDI":"Program for Climate Model Diagnosis and Intercomparison, Lawrence Livermore National Laboratory, Livermore, CA 94550, USA"

Example: source_id registration [with issue titled "registration of REMSS-PRW-6-6-0"]

  "description":"Precipitable Water",
  "institution_id":"RSS",
  "label":"REMSS PRW 6.6.0",
  "region":"global",
  "release_year":"2017",
  "source_id":"REMSS-PRW-6-6-0",
  "source_label":"REMSS-PRW", # The same as the source_id but without the version
  "source_type":"satellite_blended"

Please modify the examples above to include your registered content. Indicate in your issue title if you are modifying your input or not providing new registered content.

See note 14 of the obs4MIPs data specifications (https://goo.gl/jVZsQl) for more information regarding registered content

**Please delete example text above and provide your information below**

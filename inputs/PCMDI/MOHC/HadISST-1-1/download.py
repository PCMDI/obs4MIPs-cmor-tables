#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 25 10:09:44 2023

PJD 25 May 2023     - write script to be reused to download datasets and create json dictionary for data/file attributes

@author: durack1
"""

# %% imports
import datetime
import gzip
import json
import os
import shutil
import ssl
import sys
from socket import gethostname
from urllib.request import urlopen

# %% create ssl context to allow legacy TLS versions (lab web certs)
ctx = ssl.create_default_context()
# try using LLNL cert
# ctx.cafile = "cspca.crt" ; # https://www-csp.llnl.gov/content/assets/csoc/cspca.crt
# or disable verification
# ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

# %% create timestamps and download dir
timeNow = datetime.datetime.now()
timeFormat = timeNow.strftime("v%Y%m%d")  # "v%Y%m%dT%H%M%S") longer format
print("timeFormat:", timeFormat)
utcNow = datetime.datetime.utcnow()
histFormat = timeNow.strftime("%Y%m%dT%H%M%S UTC")
print("histFormat:", histFormat)

# create download dir
if os.path.exists(timeFormat):
    shutil.rmtree(timeFormat)
os.makedirs(timeFormat)
os.chdir(timeFormat)

# %% set URL (or if multiple files code to generate URLs)
urls = ["https://hadleyserver.metoffice.gov.uk/hadisst/data/HadISST_sst.nc.gz"]

# %% download urls
for count, url in enumerate(urls):
    filename = url.split("/")[-1]
    with urlopen(url, context=ctx) as blob, \
            open(filename, 'wb') as fh:
        fh.write(blob.read())
        # get file last modified time
        if count == 0:
            fileLastModified = blob.headers["Last-Modified"]
    # any cleanups? unzip, rename, etc?
    with open(filename, 'rb') as f:
        outFile = filename.replace(".gz", "").replace(
            "HadISST_", "HadISST.1.1.")
        with gzip.open(outFile, 'wb') as fo:
            shutil.copyfileobj(f, fo)

# %% create data info dictionary
dobJson = {}
# to be updated for each new dataset
dobJson["dataContact"] = "Paul J. Durack; pauldurack@llnl.gov; +1 925 422 5208"
dobJson["title"] = "HadISST 1.1 monthly average sea surface temperature"
dobJson["version"] = "1.1"
dobJson["reference"] = " ".join(["Rayner, N. A.; Parker, D. E.; Horton, E. B.; Folland, C. K.;",
                                 "Alexander, L. V.; Rowell, D. P.; Kent, E. C.; Kaplan, A. (2003)",
                                 "Global analyses of sea surface temperature, sea ice, and night",
                                 "marine air temperature since the late nineteenth century.",
                                 "J. Geophys. Res. Atmos., Vol. 108, No. D14, 4407"])
dobJson["referenceDOI"] = "https://doi.org/10.1029/2002JD002670"
dobJson["referenceWww"] = "https://hadleyserver.metoffice.gov.uk/hadisst/"
dobJson["sourceInstitution"] = "Met Office Hadley Centre"
dobJson["sourceInstitution_id"] = "MOHC"
# grabbed from running session - no need to edit
dobJson["institution"] = "Program for Climate Model Diagnosis and Intercomparison (LLNL), Livermore, CA, U.S.A."
dobJson["institution_id"] = "PCMDI"
dobJson["history"] = " ".join(
    ["File processed:", histFormat, "; San Francisco, CA, USA"])
dobJson["host"] = "".join(["@".join([os.getlogin(), gethostname()]), '; Python version: ',
                          sys.version.replace('\n', '; ').replace(') ;', ');')])
dobJson["sourcefile1"] = urls[0]
dobJson["sourcefile1Timestamp"] = fileLastModified

# write
os.chdir("../")  # jump out of timeFormat subdir
outJson = ".".join([timeFormat, "json"])
with open(outJson, 'w') as f:
    json.dump(
        dobJson,
        f,
        ensure_ascii=True,
        sort_keys=True,
        indent=4,
        separators=(
            ',',
            ':'))

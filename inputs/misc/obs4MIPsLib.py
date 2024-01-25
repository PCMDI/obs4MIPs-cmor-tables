#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 25 14:23:34 2023

PJD 25 May 2023     - creating a generic function library for use in obs4MIPs
PJD 26 May 2023     - hit authentication issues with LLNL cert, disabling
PJD 26 May 2023     - INCOMPLETE: added makePassMgr to deal with authentication
                      for https://urs.earthdata.nasa.gov
PJD  5 Jun 2023     - added readUrl
PJD  5 Jun 2023     - added downloadStatus
PJD  5 Jun 2023     - updated jsonDict with sourcefileCount
PJD  5 Jun 2023     - added downloadTime
PJD 14 Nov 2023     - added if os.path.exists for downloadStatus
PJD 16 Nov 2023     - added getGitInfo from durolib - https://github.com/durack1/durolib/blob/master/durolib/durolib.py#L381-L516

@author: Paul J. Durack (durack1)
"""

# %% imports

import datetime
import http
import json
import pdb
import os
import ssl
import subprocess
import sys
import time
import urllib
from http.cookiejar import CookieJar
from socket import gethostname

# %% function defs

def ProvenanceInfo(gitinfo):
    provenance = {}
    commit = gitinfo[0].split(':')[1].strip()
    input_path = os.getcwd().split('/inputs/misc')
    demo_path = os.getcwd().split('/demo') 
    provenance['commit_number'] = commit 
    provenance['demo_path'] = demo_path
    provenance['input_path'] = input_path
    return provenance 

def downloadStatus(done, timeStamp, urls):
    """
    Create statFile in download directory to note current processing status

    Parameters
    ----------
    done : boolean status
    timeStamp : timeFormat showing download subdir
    urls : list of target files for download

    Returns
    -------
    None.

    """
    statFile = "-".join(["../**DOWNLOAD", timeStamp, "INCOMPLETE**"])
    # if done = False, write statfile
    if done:
        # delete statFile if exists
        if os.path.exists(statFile):
            os.remove(statFile)
    else:
        # create statFile
        with open(statFile, "w") as f:
            f.write(" ".join(["Processing subdir:", timeStamp, "\n"]))
            f.write(" ".join(["Download file target:", str(len(urls))]))


def downloadTime(count, urls):
    """
    Generate timestamp for use in download printing

    Parameters
    -------
    count : file number
    urls : list of target files

    Returns
    -------
    downloadStr : count of len(urls); yymmddTHHMMSS formatted string

    """
    dateTimeStr = datetime.datetime.strftime(datetime.datetime.now(), "%y%m%dT%H%M%S")
    intLen = len(str(len(urls)))
    formatStr = "".join(["{:0", str(intLen), "d}"])
    downloadStr = " ".join(
        [formatStr.format(count + 1), "of", str(len(urls)), ";", dateTimeStr]
    )

    return downloadStr


def getGitInfo(filePath):
    """
    Documentation for getGitInfo():
    -------
    The getGitInfo() function retrieves latest commit info specified by filePath

    Author: Paul J. Durack : pauldurack@llnl.gov

    Inputs:
    -----

    |  **filePath** - a fully qualified file which is monitored by git

    Returns:
    -------

    |  **gitTag[0]** - commit hash
    |  **gitTag[1]** - commit note
    |  **gitTag[2]** - commit tag_point (if numeric: x.x.x)
    |  **gitTag[3]** - commit date and time
    |  **gitTag[4]** - commit author

    Usage:
    ------
        >>> from durolib import getGitInfo
        >>> gitTag = getGitInfo(filePath)

    Notes:
    -----
    * PJD 26 Aug 2016 - Showing tags, see http://stackoverflow.com/questions/4211604/show-all-tags-in-git-log
    * PJD 26 Aug 2016 - Added tag/release info
    * PJD 31 Aug 2016 - Convert tag info to use describe function
    * PJD  1 Sep 2016 - Upgrade test logic
    * PJD 15 Nov 2016 - Broadened error case if not a valid git-tracked file
    * PJD 28 Nov 2016 - Tweaks to get git tags registering
    * PJD 17 Jul 2017 - Further work required to deal with tags which include '-' characters
    * PJD 13 Nov 2020 - Updated for Py3
    * PJD 20 Jun 2023 - Updated getGitInfo to test gitTagErr.strip() == b'str' vs 'str' for py3
    ...
    """
    # Test current work dir
    if os.path.isfile(filePath) or os.path.isdir(filePath):
        currentWorkingDir = os.path.split(filePath)[0]
        # os.chdir(currentWorkingDir) ; # Add convert to local dir
    else:
        print("filePath invalid, exiting")
        return ""
    # Get hash, author, dates and notes
    p = subprocess.Popen(
        ["git", "log", "-n1", "--", filePath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=currentWorkingDir,
    )
    stdout = p.stdout.read()
    # Use persistent variables for tests below
    stderr = p.stderr.read()
    if stdout == "" and stderr == "":
        print("filePath not a valid git-tracked file")
        return
    # elif 'fatal: ' in stderr: # Py2
    elif b"fatal: " in stderr:  # Py3
        print("filePath not a valid git-tracked file")
        return
    # gitLogFull = stdout # git full log # Py2
    gitLogFull = stdout.decode("utf-8")  # git full log # Py3
    # print(gitLogFull)
    del p
    gitLog = []
    for count, gitStr in enumerate(gitLogFull.split("\n")):
        if gitStr == "":
            pass
        else:
            gitStr = gitStr.replace("   ", " ")
            # Trim excess whitespace in date
            gitStr = gitStr.replace("commit ", "commit: ")
            if count < 3:
                gitStr = gitStr.strip()
                gitStr = gitStr[:1].lower() + gitStr[1:]
                gitLog.extend([gitStr])
                continue
            gitLog.extend(["".join(["note: ", gitStr.strip()])])

    # Get tag info
    # p = subprocess.Popen(['git','log','-n1','--no-walk','--tags',
    #                      '--pretty="%h %d %s"','--decorate=full',filePath],
    p = subprocess.Popen(
        ["git", "describe", "--tags"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=currentWorkingDir,
    )
    # gitTag = p.stdout.read() # git tag log # Py2
    gitTag = p.stdout.read().decode("utf-8")  # git tag log # Py3
    # print 'gitTag',gitTag
    gitTagErr = p.stderr.read()
    # Catch tag-less error
    # print 'gitTagErr',gitTagErr
    del (filePath, p)

    if gitTagErr.strip() == b"fatal: No names found, cannot describe anything.":
        gitLog.extend(["latest_tagPoint: None"])
    elif gitTag != "":
        # Example gitTag='CMOR-3.2.5\n' https://github.com/WCRP-CMIP/CMIP6_CVs/releases/tag/CMOR-3.2.5
        # Example gitTag='CMOR-3.2.5-42-gb07f789\n'
        for count, gitStr in enumerate(gitTag.split("\n")):
            # print 'count,gitStr',count,gitStr
            if gitStr == "":
                continue
            # hyphInds = []; ind = 0
            # while ind < len(gitStr):
            #    hyphInds.append(gitStr.rfind('-',ind))
            #    ind = gitStr.find('-',ind)
            tagBits = gitStr.split("-")
            # print tagBits
            tag = tagBits[0]
            # Doesn't work with 'CMOR-3.2.5\n'
            # print tag,len(tag)
            if gitTag.count("-") == 1:  # Case tag point e.g. 'CMOR-3.2.5\n'
                tagPastCount = "0"
                tagHash = gitLog[0].replace("commit: ", "")[0:7]
                tag = gitTag.strip("\n")
                gitLog.extend(
                    [
                        "".join(
                            [
                                "latest_tagPoint: ",
                                tag,
                                " (",
                                tagPastCount,
                                "; ",
                                tagHash,
                                ")",
                            ]
                        )
                    ]
                )
            elif gitTag.count("-") == 2:  # Case beyond tag point
                tagPastCount = tagBits[1]
                tagHash = tagBits[2]
                tag = tagBits[0]
                gitLog.extend(
                    [
                        "".join(
                            [
                                "latest_tagPoint: ",
                                tag,
                                " (",
                                tagPastCount,
                                "; ",
                                tagHash,
                                ")",
                            ]
                        )
                    ]
                )
            elif gitTag.count("-") == 3:  # Case beyond tag point
                tagPastCount = tagBits[2]
                tagHash = tagBits[3]
                tag = gitTag.split("\n")[0]
                gitLog.extend(
                    [
                        "".join(
                            [
                                "latest_tagPoint: ",
                                tag,
                                " (",
                                tagPastCount,
                                "; ",
                                tagHash,
                                ")",
                            ]
                        )
                    ]
                )
            else:
                gitLog.extend(["latest_tagPoint: ", tag])
    else:
        print("Tag retrieval error, exiting")
        print("gitTag:", gitTag, len(gitTag))
        print("gitTagErr:", gitTagErr, len(gitTagErr))
        return ""

    # Order list
    # print('gitLog:',gitLog)
    gitLog = [gitLog[0], gitLog[3], gitLog[4], gitLog[2], gitLog[1]]

    return gitLog


def getTime():
    """
    Generate timestamps for use in directory, filename and json dob dictionary use

    Returns
    -------
    timeFormat following vYYYYMMDD, and histFormat including HMS notation

    """
    timeNow = datetime.datetime.now()
    timeFormat = timeNow.strftime("v%Y%m%d")  # "v%Y%m%dT%H%M%S") longer format
    print("timeFormat:", timeFormat)
    utcNow = datetime.datetime.utcnow()
    histFormat = utcNow.strftime("%Y%m%dT%H%M%S UTC")
    print("histFormat:", histFormat)

    return timeFormat, histFormat


def jsonDict(histFormat, urls, fileLastModified):
    """
    Prepopulate a dictionary with PCMDI institutional information

    Returns
    -------
    json dictionary containing institution, history, host and source file info

    """
    jsonDict = {}
    jsonDict[
        "institution"
    ] = "Program for Climate Model Diagnosis and Intercomparison, Lawrence Livermore National Laboratory, Livermore, CA 94550, USA"
    jsonDict["institution_id"] = "PCMDI"
    jsonDict["history"] = " ".join(
        ["File processed:", histFormat, "; San Francisco, CA, USA"]
    )
    jsonDict["host"] = "".join(
        [
            "@".join([os.getlogin(), gethostname()]),
            "; Python version: ",
            sys.version.replace("\n", "; ").replace(") ;", ");"),
        ]
    )
    jsonDict["sourcefile1"] = urls[0]
    jsonDict["sourcefile1Timestamp"] = fileLastModified
    jsonDict["sourcefileCount"] = len(urls)

    return jsonDict


def makePassMgr(user, passwd, url):
    """
    Create a urllib password manager, providing a valid user/pass combo
    See https://stackoverflow.com/questions/44239822/urllib-request-urlopenurl-with-authentication

    Returns
    -------
    None.

    """
    # Create a password manager to deal with the 401 reponse that is returned
    # from Earthdata Login

    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    # password_mgr = urllib.request.HTTPBasicAuthHandler()

    # Add the username and password
    # If we knew the realm, we could use it instead of None
    password_mgr.add_password(realm=None, uri=url, user=user, passwd=passwd)

    # Create a cookie jar for storing cookies. This is used to store and return
    # the session cookie given to use by the data server (otherwise it will just
    # keep sending us back to Earthdata Login to authenticate).  Ideally, we
    # should use a file based cookie jar to preserve cookies between runs. This
    # will make it much more efficient.

    cookie_jar = CookieJar()

    # Install all the handlers

    opener = urllib.request.build_opener(
        urllib.request.HTTPBasicAuthHandler(password_mgr),
        # Uncomment these two lines to see
        urllib.request.HTTPHandler(debuglevel=1),
        # details of the requests/responses
        urllib.request.HTTPSHandler(debuglevel=1),
        urllib.request.HTTPCookieProcessor(cookie_jar),
    )
    urllib.request.install_opener(opener)

    # Create and submit the request. There are a wide range of exceptions that
    # can be thrown here, including HTTPError and URLError. These should be
    # caught and handled.

    request = urllib.request.Request(url)
    response = urllib.request.urlopen(request)

    # Print out the result (not a good idea with binary data!)

    body = response.read()
    print(body)

    # handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

    # create "opener" (OpenerDirector instance)
    # opener = urllib.request.build_opener(handler)

    # use the opener to fetch a URL
    # opener.open("https://pcmdi.llnl.gov")

    # Install the opener
    # Now all calls to urllib.request.urlopen use our opener
    # urllib.request.install_opener(opener)


def readUrl(url):
    """
    Attempt to read url, and if this fails, try 3 times before failing

    Returns
    -------
    blob : downloaded file blob (type byte)
    fileLastModified : datestamp string for the source server last modification time

    Notes
    -------
    https://stackoverflow.com/questions/14442222/how-to-handle-incompleteread-in-python

    """
    ctx = sslCtx()  # initialize security context
    for attempt in range(0, 4):
        # try to read 3 times
        try:
            get = urllib.request.urlopen(url, context=ctx)
            blob = get.read()
            break  # if successful, return and exit
        except http.client.IncompleteRead:
            print("Attempt:", attempt + 1, " failed; Retrying", url)
            time.sleep(5)  # wait 5 seconds and retry
            if attempt == 2:
                pdb.set_trace()
            continue

    # get file last modified time
    fileLastModified = get.headers["Last-Modified"]

    return blob, fileLastModified


def sslCtx():
    """
    Create SSL context for urllib.request.urlopen using LLNL preconfigured certificate

    Returns
    -------
    ctx - SSL context

    Notes
    -------
    PJD 230526  - LLNL cert file works for https://hadleyserver.metoffice.gov.uk but
                  not on https://downloads.psl.noaa.gov - relaxing to disable verification

    """
    # try using LLNL cert
    # ctx = ssl.create_default_context(
    #    cafile="/p/user_pub/PCMDIobs/obs4MIPs_input/cspca.crt")
    # ctx.cafile = "cspca.crt" ; # https://www-csp.llnl.gov/content/assets/csoc/cspca.crt
    # or disable verification
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

    return ctx


def writeJson(dataDict, timeFormat):
    """
    Given a json dob dictionary, write this out with a filename that matches the vYYYYMMDD format

    Returns
    -------
    None.

    """
    outFilePath = os.path.join(
        "..", ".".join([timeFormat, "json"])
    )  # relative to timeFormat subdir
    with open(outFilePath, "w") as f:
        json.dump(
            dataDict,
            f,
            ensure_ascii=True,
            sort_keys=True,
            indent=4,
            separators=(",", ":"),
        )

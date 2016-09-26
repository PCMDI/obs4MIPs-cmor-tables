# Loop through input tables
def readJsonCreateDict(buildList):
    '''
    Documentation for readJsonCreateDict(buildList):
    -------
    The readJsonCreateDict() function reads web-based json files and writes
    their contents to a dictionary in memory

    Author: Paul J. Durack : pauldurack@llnl.gov

    Usage:
    ------
        >>> from runCMOR3 import readJsonCreateDict
        >>> readJsonCreateDict(['Omon','https://raw.githubusercontent.com/PCMDI/obs4MIPs-cmor-tables/master/Tables/obs4MIPs_Omon.json'])

    Notes:
    -----
        ...
    '''
    # Test for list input of length == 2
    if len(buildList[0]) != 2:
        print 'Invalid inputs, exiting..'
        sys.exit()
    # Create urllib2 context to deal with lab/LLNL web certificates
    ctx                 = ssl.create_default_context()
    ctx.check_hostname  = False
    ctx.verify_mode     = ssl.CERT_NONE
    # Iterate through buildList and write results to jsonDict
    jsonDict = {}       
    for count,table in enumerate(buildList):
        print 'Processing:',table[0]
        # Read web file
        jsonOutput = urllib2.urlopen(table[1], context=ctx)
        tmp = jsonOutput.read()
        vars()[table[0]] = tmp
        jsonOutput.close()
        # Write local json
        tmpFile = open('tmp.json','w')
        tmpFile.write(eval(table[0]))
        tmpFile.close()
        # Read local json
        vars()[table[0]] = json.load(open('tmp.json','r'))
        os.remove('tmp.json')
        jsonDict[table[0]] = eval(table[0]) ; # Write to dictionary
    
    return jsonDict




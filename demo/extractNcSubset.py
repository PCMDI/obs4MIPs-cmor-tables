# -*- coding: utf-8 -*-
"""
Created on Mon Jul 18 14:32:30 2016

@author: durack1
"""

import cdms2 as cdm

# Set nc classic as outputs
cdm.setCompressionWarnings(0) ; # Suppress warnings
cdm.setNetcdfShuffleFlag(0)
cdm.setNetcdfDeflateFlag(1) ; # was 0 130717
cdm.setNetcdfDeflateLevelFlag(9) ; # was 0 130717
cdm.setAutoBounds(1) ; # Ensure bounds on time and depth axes are generated

#%% Set input file and extract
f = '/work/durack1/Shared/150219_AMIPForcingData/360x180_v1.1.0_san/amipobs_tos_360x180_v1.1.0_187001-201512.nc'
fH = cdm.open(f)
d = fH('tos',time=('1870','1872'))
fo = '/export/durack1/git/obs4MIPs-cmor-tables/demo/amipobs_tos_360x180_v1.1.0_187001-187112.nc'
foH = cdm.open(fo,'w')
foH.write(d)
foH.close()
fH.close()
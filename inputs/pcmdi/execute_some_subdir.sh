# EXECUTE THE BELOW TO PRODUCE obs4MIPs CONTRIBUTIONS PREPARED BY PCMDI 
# REQUIRES CDMS2 and CMOR3 


# MONTHLY

#(cd RSS && runCmor_RSS_v07r01_2D.py)
#(cd NASA-LaRC && python runCmor_CERES4.1_2D.py)
#(cd NASA-LaRC && python runCmor_CERES4.1_SURFACE_2D.py)
#(cd NASA-LaRC && python runCmor_CERES4.0_2D.py)
#(cd NASA-LaRC && python runCmor_CERES4.0_SURFACE_2D.py)
#(cd NOAA-NCEI && python runCmor_OISST-L4-AVHRR-only-v2.py)
(cd MOHC/HadISST && python runCmor_HadISSTv1.1.py)
#(cd ESSO && python runCmor_TropFlux.py) 
#(cd CNRS && python runCmor_AVISO-1-0.py)
#(cd MRI && python runCmor_JRA25_2D.py)  
#(cd MRI && python runCmor_JRA25_3D.py)
#(cd ECMWF && python runCmor_ERA5_2d_CREATEIP.py)

# LONGER TIME SCALE MONTHLY 
#(cd ECMWF && python runCmor_ERA20C_2D.py)
#(cd NOAA-ESRL-PSD && python runCmor_20CR_2D.py)

# LONGER TIME SCALE MONTHLY 
#python runCmor_20CR_2D.py
#python runCmor_ERA20C_2D.py
#python runCmor_HadISSTv1.1.py

# DAILY

# runCmor_GPCP_v1.3_da.py

# 3HR Data

#python runCmor_TRMM_3B43v.7_3hr.py





chmod -R 755 /p/user_pub/pmp/PCMDIobs/obs4MIPs

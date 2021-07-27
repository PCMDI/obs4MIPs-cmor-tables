# EXECUTE THE BELOW TO PRODUCE obs4MIPs CONTRIBUTIONS PREPARED BY PCMDI 
# REQUIRES CDMS2 and CMOR3 


# MONTHLY

python runCmor_CERES4.1_SURFACE_2D.py
python runCmor_CERES4.1_2D.py
python runCmor_CERES4.0_SURFACE_2D.py
python runCmor_CERES4.0_2D.py
python runCmor_RSS_v07r01_2D.py
python runCmor_TropFlux.py
python runCmor_AVISO-1-0.py
python runCmor_CMAP-V1902.py
python runCmor_GPCP2.3.py
python runCmor_ERA40_2D.py

# LONGER TIME SCALE MONTHLY 
python runCmor_20CR_2D.py
python runCmor_ERA20C_2D.py
python runCmor_HadISSTv1.1.py

# DAILY

# runCmor_GPCP_v1.3_da.py

# 3HR Data

python runCmor_TRMM_3B43v.7_3hr.py





chmod -R 755 /p/user_pub/pmp/PCMDIobs/obs4MIPs

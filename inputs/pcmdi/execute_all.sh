# EXECUTE THE BELOW TO PRODUCE PMPOBS 
# REQUIRES CDMS and CMOR3 
# CURRETNLY REQUIRES DUROLIB AND THEREFORE PY2.7

# MONTHLY

python runCmor_CERES4.1_2D.py
python runCmor_CERES4.1_SURFACE_2D.py
python runCmor_CERES4.0_2D.py
python runCmor_CERES4.0_SURFACE_2D.py
python runCmor_CMAP-V1902.py
python runCmor_GPCP2.3.py
python runCmor_RSS_v07r01_2D.py 
python runCmor_TRMM_3B43v.7.py
python runCmor_AVISO-1-0.py
python runCmor_TropFlux.py
#
python runCmor_ERA40_2D.py
python runCmor_ERA40_3D.py
python runCmor_ERAINT_2D.py
python runCmor_ERAINT_3D.py
#python runCmor_ERA5_alllevs.py
#python runCmor_ERA5_2D_MARS.py

# LONGER TIME SCALE MONTHLY 
python runCmor_20CR_2D.py
python runCmor_ERA20C_2D.py
python runCmor_HadISSTv1.1.py


## PROBLEM DATA
#python runCmor_JRA25_2D.py BAD TIME MODEL
#python runCmor_JRA25_3D.py   "      "

# DAILY

python runCmor_GPCP_v1.3_da.py

# 3HR Data

python runCmor_TRMM_3B43v.7_3hr.py
###python CMORPH_V1.0_3hr.py

python runCmor_ERA5_2d_CREATEIP.py
python runCmor_ERA5_alllevs_CREATEIP.py


######################
chmod -R 755 /p/user_pub/PCMDIobs/PCMDIobs2


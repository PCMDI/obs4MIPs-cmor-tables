# EXECUTE THE BELOW TO PRODUCE obs4MIPs CONTRIBUTIONS PREPARED BY PCMDI 
# REQUIRES CDMS2 and CMOR3 


# MONTHLY

python runCmor_TropFlux.py
python runCmor_HadISSTv1.1.py
python runCmor_AVISO-1-0.py
python runCmor_20CR_2D.py
python runCmor_CMAP-V1902.py
python runCmor_GPCP2.3.py
python runCmor_ERA40_2D.py


chmod -R 755 /p/user_pub/pmp/PCMDIobs/obs4MIPs

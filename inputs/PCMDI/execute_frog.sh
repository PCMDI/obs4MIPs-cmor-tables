# EXECUTE THE BELOW TO PRODUCE obs4MIPs CONTRIBUTIONS PREPARED BY PCMDI 
# REQUIRES CDMS2 and CMOR3 


# DAILY 

#python runCmor_GPCP_1DD_CDR_v1.3_FROGS_da.py
#python runCmor_ERA5_FROGS_da.py  
python runCmor_IMERG_V06_EU_FROGS_da.py
python runCmor_IMERG_V06_LU_FROGS_da.py
python runCmor_IMERG_V06_FU_FROGS_da.py
python runCmor_IMERG_V06_FC_FROGS_da.py

#python runCmor_PERSIANN_CDRv1r1_da.py
#python runCmor_3B42_v7.0_FROGS_da.py
#python runCmor_CMORPH_v1.0_CRT_FROGS_da.py

chmod -R 755 /p/user_pub/PCMDIobs/obs4MIPs

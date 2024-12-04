import xcdat as xc

varz = ['rlut','rsut','rsdt','rsutcs','rlutcs','rsds','rsus','rsuscs','rsdscs','rldscs']
#varz = ['rsds']

obs_template = '/p/user_pub/PCMDIobs/obs4MIPs/NASA-LaRC/CERES-EBAF-4-2/mon/VAR/gn/v20231204/VAR_mon_CERES-EBAF-4-2_RSS_gn_*.nc'  #200003-202307.nc'
mod1_template = '/p/css03/esgf_publish/CMIP6/CMIP/CCCma/CanESM5-1/historical/r1i1p1f1/Amon/VAR/gn/v20190429/VAR_Amon_CanESM5-1_historical_r1i1p1f1_gn_185001-201412.nc' 

print('          MODEL1','                 OBS')
for vr in varz:
   mod1 = mod1_template.replace('VAR',vr)
   mds1 = xc.open_mfdataset(mod1)
   m1 = mds1.isel(time=slice(0,1))[vr].squeeze()
   mavg = float(mds1.isel(time=3).spatial.average(vr,axis=['X','Y'])[vr].compute())

   try:
    obs = obs_template.replace('VAR',vr)
    o1 = xc.open_mfdataset(obs)
    o = o1.isel(time=slice(0,1))[vr].squeeze()
    oavg = float(o1.isel(time=3).spatial.average(vr,axis=['X','Y'])[vr].compute())
   except:
    oavg = 'N/A'
   print(vr,' ',str(mavg),'  ',oavg) 



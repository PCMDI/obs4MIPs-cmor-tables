import xcdat as xc


varz = ['rlut','rsut']

obs_template = ''

mod1_template = '/p/css03/esgf_publish/CMIP6/CMIP/CCCma/CanESM5-1/historical/r1i1p1f1/Amon/VAR/gn/v20190429/VAR_Amon_CanESM5-1_historical_r1i1p1f1_gn_185001-201412.nc' 


for vr in varz:
   mod1 = mod1_template.replace('VAR',vr)
   mds1 = xc.open_dataset(mod1)
   m1 = mds1.isel(time=slice(0,1))[vr].squeeze()
   mavg = float(mds1.isel(time=3).spatial.average(vr,axis=['X','Y'])[vr].compute())
   print(vr,' ',str(mavg)) 



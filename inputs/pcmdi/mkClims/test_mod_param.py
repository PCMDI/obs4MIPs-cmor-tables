# VARIABLES TO USE
vars = ['ts']
# vars = ['ua', 'ta']
#vars = ['pr', 'ua', 'ta']

# START AND END DATES FOR CLIMATOLOGY
start = '1981-01'
# end = '1983-12'
end = '2005-12'

# INPUT DATASET - CAN BE MODEL OR OBSERVATIONS
infile = '/p/user_pub/PCMDIobs/obs4MIPs/MOHC/HadISST-1-1/mon/ts/gn/v20230109/ts_mon_HadISST-1-1_PCMDI_gn_187001-201907.nc'

# DIRECTORY WHERE TO PUT RESULTS
outfile = 'clim_test/hadtest.%(variable).nc'


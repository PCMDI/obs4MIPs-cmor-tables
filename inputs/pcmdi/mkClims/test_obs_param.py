# VARIABLES TO USE
vars = ['ts']
#vars = ['pr', 'ua', 'ta']

# START AND END DATES FOR CLIMATOLOGY
#start = '1981-01'
# end = '1983-12'
#end = '2005-12'

# INPUT DATASET - CAN BE MODEL OR OBSERVATIONS
infile = '/p/user_pub/PCMDIobs/obs4MIPs/MOHC/HadISST-1-1/mon/ts/gn/v20230109/ts_mon_HadISST-1-1_PCMDI_gn_187001-201907.nc'

# DIRECTORY WHERE TO PUT RESULTS
#outfile = '/home/gleckler1/tmp/clim_test/hadtest.%(variable).nc'

tmp = infile.replace('/mon/','/monC/')
outfile = tmp.replace('_mon_','_monC_')

periodinname = 'no'
climlist = ['AC']

print('outfile ',outfile.split('.'))



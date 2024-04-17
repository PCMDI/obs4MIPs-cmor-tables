import cftime

def monthly_times(datumyr,yrs,start_month=1,end_month=12):
    mos = [1,2,3,4,5,6,7,8,9,10,11,12]
    t = []
    tbds = []
    for yr in yrs:
        for mn, mo in enumerate(mos):
            if yr == yrs[0] and mo < start_month: continue
            if yr == yrs[-1] and mo > end_month: continue
            if mo < 12:
                lb = cftime.datetime(yr,mn+1,1,calendar=u'standard')
                ub = cftime.datetime(yr,mn+2,1,calendar=u'standard')
            else:
                lb = cftime.datetime(yr,mn+1,1,calendar=u'standard')
                ub = cftime.datetime(yr+1,1,1,calendar=u'standard')
            lbn = cftime.date2num(lb,f'days since {datumyr}-{str(start_month).zfill(2)}-01')
            ubn = cftime.date2num(ub,f'days since {datumyr}-{str(start_month).zfill(2)}-01')
            mp = lbn + (ubn - lbn)/2.
            t.append(mp)
            tbds.append((lbn,ubn))
    return(t,tbds)

# years = np.arange(2003,2023,1)
# datumyr = '2003'
# yrs = [2000,2001,2002]
# start_month = 3
# end_month = 10
# t,bds = monthly_times(datumyr,years,start_month,end_month)
# print(t)
# print(bds)
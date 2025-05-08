import cftime

def monthly_times(datumyr,yrs,datum_start_month=1,start_month=1,end_month=12):
    """
        Code to fix erroneous time coordinates in certain datasets.
        datumyr = year of the reference time e.g., 2000 in days since 2000-01-01 00:00:00
        yrs = set of years we wish to calculate time bounds for.  Can be a single year or an array/list of years.
        datum_start_month = month of the reference time e.g., 1 in days since 2000-01-01 00:00:00. Default is 1 (January)
        start_month = starting month of the dataset e.g., 4 if the dataset starts in April of a given year. Default is 1 (January)
        end_month = ending month of the dataset e.g., 9 if the dataset ends in September of the final year. Defualt is 12 (December)
    """
    mos = [1,2,3,4,5,6,7,8,9,10,11,12]
    t = []
    tbds = []
    tunits = f'days since {datumyr}-{str(datum_start_month).zfill(2)}-01 00:00:00'
    if isinstance(yrs, int):
          yr = yrs
          for mn, mo in enumerate(mos):
            if  mo < start_month: continue
            if  mo > end_month: continue
            if mo < 12:
                lb = cftime.datetime(yr,mn+1,1,calendar=u'standard')
                ub = cftime.datetime(yr,mn+2,1,calendar=u'standard')
            else:
                lb = cftime.datetime(yr,mn+1,1,calendar=u'standard')
                ub = cftime.datetime(yr+1,1,1,calendar=u'standard')
            lbn = cftime.date2num(lb,f'days since {datumyr}-{str(datum_start_month).zfill(2)}-01')
            ubn = cftime.date2num(ub,f'days since {datumyr}-{str(datum_start_month).zfill(2)}-01')
            mp = lbn + (ubn - lbn)/2.
            t.append(mp)
            tbds.append((lbn,ubn))
    else:
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
                lbn = cftime.date2num(lb,f'days since {datumyr}-{str(datum_start_month).zfill(2)}-01')
                ubn = cftime.date2num(ub,f'days since {datumyr}-{str(datum_start_month).zfill(2)}-01')
                mp = lbn + (ubn - lbn)/2.
                t.append(mp)
                tbds.append((lbn,ubn))
    return(t,tbds,tunits)

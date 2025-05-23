import os, sys
import json
import xcdat as xc
import numpy as np
import datetime
import glob
import math
import matplotlib.pyplot as plt

ver = datetime.datetime.now().strftime('v%Y%m%d')

def main():

    vars_list = ['pr']
    fqs_list = ['day']  #monthly','day','3hr'] #,'day']
    time_slice = 1 

    cfopt = True 
    plot_out_dir = './maps_cf' + str(cfopt)

    os.makedirs(plot_out_dir, exist_ok=True)

    for var in vars_list:
        for fq in fqs_list:
            
            pathin_template = '/p/user_pub/PCMDIobs/catalogue/obs4MIPs_PCMDI_' + fq + '_byVar_catalogue_v????????.json'
            print(pathin_template)
            pathin = sorted(glob.glob(pathin_template))[-1]  # select the latest catalogue file

            print('\nvar, fq, catalogue:', var, fq, pathin.split('/')[-1], '\n')

            ddic = json.load(open(pathin))
            srcs = sorted(list(ddic[var].keys()))

            if 'default' not in srcs:
                print('[WARNING] default is not set for ', var, fq)

            srcs = [ s for s in srcs if ('default' not in s and 'alternate' not in s) ]  # exclude 'default' or 'alternate?' keys
            print(srcs)

            fig, axs = prepare_subplots(srcs)

            ts = 'Mean @ t=' + str(time_slice)            
            print('\nSource'.ljust(25), '\t', ts.ljust(10), '\t', 'Min'.ljust(10), '\t', 'Max'.ljust(10),'\t', 
                  'Units'.ljust(10),'\t','Region')   #, '\t' , 'missing_value'.ljust(10),'\t', 'FillValue'.ljust(10))
            print('-' * 25, '\t', '-' * 10, '\t', '-' * 10, '\t', '-' * 10, '\t', '-' * 10, '\t', '-' * 10, '\t', '-' * 10)
            
            for i, src in enumerate(srcs):
                template = '/p/user_pub/PCMDIobs/' + ddic[var][src]['template']
                # open file
#               print(template)
                ds = xc.open_mfdataset(
                    template,
                    mask_and_scale=True,
                    decode_times=False,
                    decode_cf=cfopt,
                    combine='nested',
                    concat_dim='time',
                    data_vars='all')
                # get spatial mean of the first time step
                ds_avg = float(ds.isel(time=time_slice).spatial.average(var)[var])
                ds_max = ds.isel(time=time_slice)[var].max().values
                ds_min = ds.isel(time=time_slice)[var].min().values

                try:
                 reg = ds.attrs['region']
                except:
                 reg = '-'

                # print on screen 
                print(src.ljust(25), '\t', '{:.10f}'.format(ds_avg),'\t','{:.10f}'.format(ds_min),'\t','{:.10f}'.format(ds_max), '\t', ds[var].units.ljust(10),'\t',reg.ljust(10)) #,'\t',ds[var].attrs['missing_value'],'\t','\t', ds[var].attrs['_FillValue'])
                # plot
                ds.isel(time=time_slice)[var].plot(ax=axs[i])  #, vmax = 0.0003)
                axs[i].set_title(src)
                # close file
                ds.close()
       
            fig.suptitle(var + ', ' + fq)
            fig.tight_layout()
            fig.savefig(os.path.join(plot_out_dir, var + '_' + fq + '_t0map_' + ver + '.png'))
            plt.close()

    print('\n')


def prepare_subplots(srcs):
    total_plots = len(srcs)
    num_rows, num_cols = calculate_subplots(total_plots)

    # Calculate figure size based on desired plot width and height
    plot_width = 600
    plot_height = 400
    fig_width = num_cols * plot_width
    fig_height = num_rows * plot_height
    figsize = (fig_width / 80, fig_height / 80)  # Convert to inches (80 pixels per inch)

    # Create subplots with the calculated figure size
    fig, axs = plt.subplots(num_rows, num_cols, figsize=figsize)

    # Flatten the axs array if it has more than one dimension
    if num_rows > 1 and num_cols > 1:
        axs = axs.flatten()

    return fig, axs


def calculate_subplots(num_plots):
    num_rows = math.floor(math.sqrt(num_plots))
    num_cols = math.ceil(num_plots / num_rows)
    return num_rows, num_cols


if __name__ == "__main__":
    main()

"""
Purpose:
This is the script that calls all the other routines. This script also does basic 
data-prep work.
"""

import pandas as pd
import sys
import os
from matplotlib import pyplot as plt
import numpy as np

#-------------------------#
# Main
if __name__ == '__main__':

    prompt = """
    Parameters
    ----------
      arg1: the python script directory
      arg2: the full path to the directory containing the data folders
      arg3: the folder containing weather data
      arg4: the folder containing yield data
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:

    >>> script_dir = "...\DuPont_Challenge"
    (recommended -> full path to \src folder)
    >>> data_dir = "...\coding-data-exam"
    >>> wx_data_folder = 'wx_data'
    >>> yld_data_folder = 'yld_data'
    (assuming that yld_data = 'US_corn_grain_yield.txt')
    """
    print(prompt_example)
    print("-----------------------------------")

    script_dir = input('script directory: ')
    script_dir = script_dir.replace("\"", "")
    data_dir = input('workspace: ')
    data_dir = data_dir.replace("\"", "")
    wx_data_folder = input('wx data folder name: ')
    yld_data_folder = input('yld data folder name: ')

    #-----#
    output_dir = data_dir
    weather_dir = os.path.join(data_dir, wx_data_folder)
    yield_file = os.path.join(data_dir, os.path.join(yld_data_folder,"US_corn_grain_yield.txt"))
    #-----#

    os.chdir(data_dir)

    # set a sys path to scripts used in this project:
    # directory = r"C:\Users\joogl\PycharmProjects\DuPont_Challenge"
    directory = script_dir
    sys.path.insert(0, directory)
    import missing_prec_data
    import yr_max_stats_freq
    import yr_calc_stats
    import agg_corr_coef
    #-----------------------------------------------#

    # Data Prep: read-in weather-data
    #data_dir = r"C:\Users\joogl\Assessments\DuPont Assessment\coding-data-exam"
    #weather_dir = os.path.join(data_dir, "wx_data")
    #output_dir = r"C:\Users\joogl\Assessments\DuPont Assessment\Outputs"
    #yield_file = os.path.join(data_dir, r"yld_data\US_corn_grain_yield.txt")

    print('Weather data directory: {}'.format(weather_dir))

    # (1) construct a list of weather txt file names
    weather_reports = []
    for file in os.listdir(weather_dir):
        weather_reports.append(file)

    # (2) instantiate a data object for each of the 4 class methods we will apply to the source data
    missing_class_df = missing_prec_data.class_missing_days()
    yr_calc_stats_df = yr_calc_stats.class_calc_stats()
    yr_max_stats_df = yr_max_stats_freq.class_max_stats()
    agg_corr_coef_df = agg_corr_coef.class_corr_coef()

    # (3) construct the yields data pd df
    pd_df_yields = pd.read_table(yield_file, header=0,
                                     names=['year', 'yields_1000mt'])

    for filex in weather_reports:
        # (a) get the file name here
        weather_file_name = filex.split(".")[0]
        weather_file = os.path.join(weather_dir, filex)
        ###
        ###
        print('Processing Weather Report: {}'.format(weather_file))

        test_weather_txt = pd.read_table(weather_file, header=0,
                                         names=['date', 'maxtemp_c', 'mintemp_c', 'precip_mil'])
        test_weather_txt['ddate'] = pd.to_datetime(test_weather_txt['date'],
                                                   format='%Y%m%d', errors='coerce')

        # (b1) call class method missing_prec_data_df.calc_missing_days()
        missing_class_df.calc_missing_days(weather_file_name, test_weather_txt)

        # (c1) call class method yr_calc_stats_df.calc_stats()
        yr_calc_stats_df.calc_stats(weather_file_name, test_weather_txt)

    #---------------------------#

    # (d1) call class method yr_max_stats_df.calc_max_stats()
    pd_df_avgs = yr_calc_stats_df.active_df.copy()
    count_graph = yr_max_stats_df.calc_max_stats(yr_calc_stats_df.active_df)

    ####################################
    # create bar chart:
    fig, ax = plt.subplots()
    index = count_graph['year']
    bar_width = 0.35
    opacity = 0.8

    rects1 = plt.bar(index - bar_width, count_graph['nmax_avg_max_temp'], width=.25, align='center',
                     alpha=opacity,
                     color='b',
                     label='Average Max Temperature (C)')

    rects2 = plt.bar(index, count_graph['nmax_avg_min_temp'], width=.25, align='center',
                     alpha=opacity,
                     color='g',
                     label='Average Min Temperature (C)')

    rects3 = plt.bar(index + (bar_width), count_graph['nmax_total_precip'], width=.25, align='center',
                     alpha=opacity,
                     color='r',
                     label='Total Precipitation (mil)')

    # Major ticks every 1, minor ticks every 5
    major_ticks = np.arange(1985, 2015, 1)
    minor_ticks = np.arange(1985, 2015, 1)

    plt.xlabel('Metrics')
    plt.ylabel('Counts')
    plt.title('Counts by Metric')

    ax.set_xticks(major_ticks)
    ax.set_xticks(minor_ticks, minor=True)
    plt.xticks(rotation=45)

    plt.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir,"YearHistogram.png"))
    print("Close the .png file if it's open")
    plt.show()
    ####################################

    # (e1) call class method agg_corr_coef_df.calc_aggs()

    agg_corr_coef_df.calc_aggs(pd_df_avgs, pd_df_yields)

    ### Write Files
    # (b2) call class method .write_out() for all df objects

    missing_class_df.active_df.to_csv(os.path.join(output_dir,"MissingPrcpData.out.txt"), \
                                      header=None, index=None, mode='a', sep='\t')
    yr_calc_stats_df.active_df.to_csv(os.path.join(output_dir,"YearlyAverages.out.txt"), \
                                      header=None, index=None, mode='a', sep='\t')
    yr_max_stats_df.active_df.to_csv(os.path.join(output_dir,"YearHistogram.out.txt"), \
                                      header=None, index=None, mode='a', sep='\t')

    agg_corr_coef_df.active_df.to_csv(os.path.join(output_dir,"Correlations.out.txt"), \
                                      header=None, index=None, mode='a', sep='\t')

    print("Done.")
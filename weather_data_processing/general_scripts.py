"""
Purpose:
This is the script that calls all the other routines. This script also does basic 
data-prep work.
"""

import pandas as pd

# set a sys path to scripts used in this project:

import sys
import os
from operator import itemgetter
from itertools import groupby
from matplotlib import pyplot as plt
import numpy as np

directory = r"C:\Users\joogl\PycharmProjects\DuPont_Challenge"
sys.path.insert(0, directory)
import missing_prec_data
import yr_max_stats_freq
import yr_calc_stats
import agg_corr_coef

#---------------------------#

#---------------------------#

# Data Prep: read-in weather-data
data_dir = r"C:\Users\joogl\Assessments\DuPont Assessment\coding-data-exam"
weather_dir = os.path.join(data_dir, "wx_data")
yield_file = os.path.join(data_dir, r"yld_data\US_corn_grain_yield.txt")

print(weather_dir)

# (1) construct a list of weather txt file names
weather_reports = []
for file in os.listdir(weather_dir):
    weather_reports.append(file)
print(weather_reports)

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
    print(weather_file_name)
    print(weather_file)
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
plt.show()
####################################

# (e1) call class method agg_corr_coef_df.calc_aggs()

agg_corr_coef_df.calc_aggs(pd_df_avgs, pd_df_yields)

### Write Files
# (b2) call class method df_missing_prec_data.write_out()





######################### SCRATCH #########################
# (b) read-in file
test_weather_txt = pd.read_table(weather_file,header=0, \
                                 names=['date', 'maxtemp_c', 'mintemp_c', 'precip_mil'])
# (c) convert date column data-type to datetime
test_weather_txt['ddate'] = pd.to_datetime(test_weather_txt['date'], format='%Y%m%d', errors='coerce')

######################### SCRATCH #########################

pd_df_yields = pd.read_table(yield_file, header=0,
                                 names=['year', 'yields_1000mt'])

active_df = pd.DataFrame([], columns=['txt_name', 'oorr_maxTemp', 'corr_minTem', \
                                                   'corr_Precip'])

test = pd.DataFrame([], columns=['txt_name', 'year', \
                                                   'avg_max_temp', 'avg_min_temp', 'total_precip'])

test.loc[0] = ['USC00339312', 1986, -13, -60, 50]
test.loc[1] = ['USC00339313', 1991, -12, -70, 25]
test.loc[2] = ['USC00339313', 1991, -12, -70, 25]
test.loc[3] = ['USC00339313', 1988, -3, -30, 10]
test.loc[4] = ['USC00339313', 1989, -5, -80, 15]
test.loc[5] = ['USC00339313', 1987, -10, -50, 30]
test.loc[6] = ['USC00339315', 1987, -5, -10, 60]
test.loc[7] = ['USC00339315', 1989, -6, 1, 40]
test.loc[8] = ['USC00339312', 1988, -10, -30, 35]
test.loc[9] = ['USC00339312', 1989, -7, -24, 10]
test.loc[10] = ['USC00339315', 1992, -17, -22, 2]

t=calc_aggs(test, pd_df_yields, active_df)

def calc_aggs(pd_df_avgs, pd_df_yields, active_df):

    length = len(active_df)
    print(pd_df_avgs['txt_name'].unique())

    for station in pd_df_avgs['txt_name'].unique():
        print(station)

        # conform date domain of Clists to date domain in yields list
        avgs_df = pd_df_avgs[pd_df_avgs['txt_name'] == station]

        cIndex = pd_df_yields.set_index(['year']).index. \
            intersection(avgs_df.set_index(['year']).index)
        print(cIndex)

        avgs_df = avgs_df[avgs_df['year'].isin(cIndex)]
        avgs_df.drop_duplicates(subset=['year'], inplace=True)
        print(avgs_df)

        yields_df = pd_df_yields[pd_df_yields['year'].isin(cIndex)]
        yields_list = list(yields_df['yields_1000mt'])
        print(yields_list)

        maxTemp_Clist = list(avgs_df['avg_max_temp'])
        minTemp_Clist = list(avgs_df['avg_min_temp'])
        precip_Clist = list(avgs_df['total_precip'])

        pearson_YmxT, _YmxT = pearsonr(yields_list, maxTemp_Clist)
        pearson_YmnT, _YmnT = pearsonr(yields_list, minTemp_Clist)
        pearson_Yprp, _Yprp = pearsonr(yields_list, precip_Clist)

        print(pearson_YmxT)
        print(pearson_YmnT)
        print(pearson_Yprp)

        active_df.loc[length + 1] = [station, pearson_YmxT, pearson_YmnT, pearson_Yprp]
        active_df.reset_index()
        length = len(active_df)
        print(length)
        print("==============================")

    return active_df

######################### SCRATCH #########################

# weather_file_name

active_df = pd.DataFrame([], columns=['year', 'nmax_avg_max_temp', 'nmax_avg_min_temp', \
                                                   'nmax_total_precip'])

test = pd.DataFrame([], columns=['txt_name', 'year', \
                                                   'avg_max_temp', 'avg_min_temp', 'total_precip'])

test.loc[0] = ['USC00339312', 1986, -13, -60, 50]
test.loc[1] = ['USC00339313', 1985, -10, -50, 30]
test.loc[2] = ['USC00339313', 1985, -10, -50, 30]
test.loc[3] = ['USC00339313', 1987, -10, -50, 30]
test.loc[4] = ['USC00339315', 1987, -5, -10, 60]
test.loc[5] = ['USC00339315', 1982, -5, 0, 40]

calc_max_stats(test, active_df)

def calc_max_stats(pd_df_avgs, active_df):

    # create a dictionary
    station_avgmax_dict = {}
    station_avgmin_dict = {}
    station_totprec_dict = {}

    # create a new index
    # pd_df_avgs['index'] = pd_df_avgs.index

    # find the year(s) of this subset with the highest avg_max_temp
    st_avg_max_temp = pd_df_avgs.groupby(['txt_name']).agg({'avg_max_temp': 'max'})
    # find the year(s) of this subset with the highest avg_max_temp
    st_avg_min_temp = pd_df_avgs.groupby(['txt_name']).agg({'avg_min_temp': 'max'})
    # find the year(s) of this subset with the highest avg_max_temp
    st_total_precip = pd_df_avgs.groupby(['txt_name']).agg({'total_precip': 'max'})

    # for all maximums, locate related index and then related year
    for station in pd_df_avgs['txt_name'].unique():
        yr_station = pd_df_avgs[pd_df_avgs['txt_name']==station]

        # recover table subset with the max values of avg_max_temp
        yr_station_mxtemp = yr_station[yr_station['avg_max_temp']==st_avg_max_temp.ix[station][0]]
        yr_mxtemp = yr_station_mxtemp['year'].unique()  # ideally 1 element but may be more if
                                                        # several years are tied for max temp
        yr_station_mntemp = yr_station[yr_station['avg_min_temp']==st_avg_min_temp.ix[station][0]]
        yr_mntemp = yr_station_mntemp['year'].unique()  # ideally 1 element but may be more if
                                                        # several years are tied for max temp
        yr_station_precip = yr_station[yr_station['total_precip']==st_total_precip.ix[station][0]]
        yr_precip = yr_station_precip['year'].unique()  # ideally 1 element but may be more if
                                                        # several years are tied for max temp

        # store list under a dictionary whose key is the station ID
        station_avgmax_dict[station] = yr_mxtemp
        station_avgmin_dict[station] = yr_mntemp
        station_totprec_dict[station] = yr_precip

    # get an inverse dictionary
    inv_avgmax_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                           in groupby(sorted(((j, k) for k, v in station_avgmax_dict.items() for j in v), \
                                             key=itemgetter(0)), key=itemgetter(0)))
    inv_avgmin_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                           in groupby(sorted(((j, k) for k, v in station_avgmin_dict.items() for j in v), \
                                             key=itemgetter(0)), key=itemgetter(0)))
    inv_precip_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                           in groupby(sorted(((j, k) for k, v in station_totprec_dict.items() for j in v), \
                                             key=itemgetter(0)), key=itemgetter(0)))

    # for each year, total the number of stations
    length = len(active_df)
    for yr in range(1985,2015):
        try:
            yr_count_avgmax = len(inv_avgmax_dict[yr])
        except:
            yr_count_avgmax = 0
        try:
            yr_count_avgmin = len(inv_avgmin_dict[yr])
        except:
            yr_count_avgmin = 0
        try:
            yr_count_precip = len(inv_precip_dict[yr])
        except:
            yr_count_precip = 0
        active_df.loc[length + 1] = [yr, yr_count_avgmax, yr_count_avgmin, yr_count_precip]
        active_df.reset_index()
        length = len(active_df)


    print(st_avg_max_temp)
    print(st_avg_min_temp)
    print(st_total_precip)
    print("=======================")
    print(station_avgmax_dict)
    print(station_avgmin_dict)
    print(station_totprec_dict)
    print("=======================")
    print(inv_avgmax_dict)
    print(inv_avgmin_dict)
    print(inv_precip_dict)

    print(active_df)

    return active_df




######################### SCRATCH #########################
active_df = pd.DataFrame([], columns=['txt_name', 'year', \
                                                   'avg_max_temp', 'avg_min_temp', 'total_precip'])

calc_stats(weather_file_name, test_weather_txt, active_df)

test_weather_txt.iloc[0][4].date().year

def calc_stats(txt_name, pd_df, active_df):
    # for each row
    # get list of 3 variables
    # if var3 is equal to -9999 and var1 != -9999 and var2 != -9999, increase counter
    # write outputs to a line in active_df

    w_counter = 0

    length = len(active_df)

    dict = {}   # year key, and 3-element tuple of lists ([max_temp], [min_temp], [precip])

    for rowx in pd_df.iterrows():
        ddate = [rowx[1]['ddate']]
        eval_list = [rowx[1]['maxtemp_c'], rowx[1]['mintemp_c'], rowx[1]['precip_mil']]

        # add elements of this list to a dictionary using a year key:
        year_key = rowx[1]['ddate'].date().year
        year_key_list = dict.keys()
        print(year_key_list)
        if year_key in year_key_list:   # year already in list. Add to pre-existing tuple
            if eval_list[0] != -9999:
                dict[year_key][0].append(eval_list[0])
            if eval_list[1] != -9999:
                dict[year_key][1].append(eval_list[1])
            if eval_list[2] != -9999:
                dict[year_key][2].append(eval_list[2])
        else:                           # year not in list. Add this key with 3 lists
            dict[year_key] = ([],[],[])

        print(ddate)
        print(eval_list)

        w_counter = w_counter + 1
        if w_counter >= 10:
            break

    # loop through dictionary. For each year, perform the necessary aggregation. Write to active_df
    for n, year_y in enumerate(dict.keys()):
        # take average and sum metrics
        max_temp_avg = sum(dict[year_y][0]) / float(len(dict[year_y][0]))
        min_temp_avg = sum(dict[year_y][1]) / float(len(dict[year_y][1]))
        cum_precip = sum(dict[year_y][2])

        # append to active_df
        active_df.loc[length + (n + 1)] = [weather_file_name, year_y, max_temp_avg, \
                                            min_temp_avg, cum_precip]
        active_df.reset_index()

    print(dict)
    return active_df


######################### SCRATCH #########################

active_df = pd.DataFrame([], columns=['txt_name', 'missing_data_days'])

calc_missing_days(weather_file_name, test_weather_txt)

def calc_missing_days(txt_name, pd_df, active_df):

    # for each row
    # get list of 3 variables
    # if var3 is equal to -9999 and var1 != -9999 and var2 != -9999, increase counter
    # write outputs to a line in active_df

    w_counter = 0
    counter = 0

    length = len(active_df)

    for rowx in pd_df.iterrows():
        eval_list = [rowx[1]['maxtemp_c'], rowx[1]['mintemp_c'], rowx[1]['precip_mil']]
        # eval_list.append([rowx[1]['maxtemp_c'], rowx[1]['mintemp_c'], rowx[1]['precip_mil']])
        rules = [eval_list[0] != -9999,
                 eval_list[1] != -9999,
                 eval_list[2] == 0]
        print(rules)

        if all(rules):
            counter += 1
        else:
            pass

        w_counter = w_counter + 1
        if w_counter >= 10:
            break

        # append to active_df
        active_df.loc[length + 1] = [weather_file_name, counter]
        active_df.reset_index()

    print(counter)
    return active_df

################################################################
"""
Purpose: called by general_scripts.py

This script contains a class: class_missing_days which upon initialization creates a blank pd df.
It contains the following methods:

1) calc_max_stats() which takes as args:
- pd df created by yr_calc_stats of txt file to process
It returns:
- an appendation of txt_name/year to the initialized dataframe
- an appendation of the number of times a station had that year as their max temp/min temp/max precip
"""

import pandas as pd
from operator import itemgetter
from itertools import groupby

#---------------------------------#

class class_max_stats:
    def __init__(self):
        """
        This class creates upon initialization a pd df that will hold results from the class methods
        """

        self.active_df = pd.DataFrame([], columns=['year', 'nmax_avg_max_temp', 'nmax_avg_min_temp', \
                                                   'nmax_total_precip'])

    #---------------------------------#
    def calc_max_stats(self, pd_df_avgs):
        """
        
        :param pd_df_avgs: the pd df returned in self.active_df from class class_calc_stats in yr_calc_stats.py
        :return: the number of times a station had a year as their max temp/min temp/max precip
        """
        # create a dictionary
        station_avgmax_dict = {}
        station_avgmin_dict = {}
        station_totprec_dict = {}

        # find the year(s) of this subset with the highest avg_max_temp
        st_avg_max_temp = pd_df_avgs.groupby(['txt_name']).agg({'avg_max_temp': 'max'})
        # find the year(s) of this subset with the highest avg_max_temp
        st_avg_min_temp = pd_df_avgs.groupby(['txt_name']).agg({'avg_min_temp': 'max'})
        # find the year(s) of this subset with the highest avg_max_temp
        st_total_precip = pd_df_avgs.groupby(['txt_name']).agg({'total_precip': 'max'})

        # for all maximums, locate related index and then related year
        for station in pd_df_avgs['txt_name'].unique():
            yr_station = pd_df_avgs[pd_df_avgs['txt_name'] == station]

            # recover table subset with the max values of avg_max_temp
            yr_station_mxtemp = yr_station[yr_station['avg_max_temp'] == st_avg_max_temp.ix[station][0]]
            yr_mxtemp = yr_station_mxtemp['year'].unique()  # ideally 1 element but may be more if
            # several years are tied for max temp
            yr_station_mntemp = yr_station[yr_station['avg_min_temp'] == st_avg_min_temp.ix[station][0]]
            yr_mntemp = yr_station_mntemp['year'].unique()  # ideally 1 element but may be more if
            # several years are tied for max temp
            yr_station_precip = yr_station[yr_station['total_precip'] == st_total_precip.ix[station][0]]
            yr_precip = yr_station_precip['year'].unique()  # ideally 1 element but may be more if
            # several years are tied for max temp

            # store list under a dictionary whose key is the station ID
            station_avgmax_dict[station] = yr_mxtemp
            station_avgmin_dict[station] = yr_mntemp
            station_totprec_dict[station] = yr_precip

        # get an inverse dictionary
        inv_avgmax_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                               in groupby(sorted(((j, k) for k, v in station_avgmax_dict.items() for j in v),
                                                 key=itemgetter(0)), key=itemgetter(0)))
        inv_avgmin_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                               in groupby(sorted(((j, k) for k, v in station_avgmin_dict.items() for j in v),
                                                 key=itemgetter(0)), key=itemgetter(0)))
        inv_precip_dict = dict((x, list(t[1] for t in group)) for (x, group) \
                               in groupby(sorted(((j, k) for k, v in station_totprec_dict.items() for j in v),
                                                 key=itemgetter(0)), key=itemgetter(0)))

        # for each year, total the number of stations
        length = len(self.active_df)
        for yr in range(1985, 2015):
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
            self.active_df.loc[length + 1] = [yr, yr_count_avgmax, yr_count_avgmin, yr_count_precip]
            self.active_df.reset_index()
            length = len(self.active_df)

        return self.active_df

    #---------------------------------#
    def write_out(self, file_path):
        """
        :return: ejects a text file whose rows are sorted by filename
        """
        self.active_df.to_csv(file_path, header=None, index=None, mode='a', sep='   ')

        return None
#---------------------------------#
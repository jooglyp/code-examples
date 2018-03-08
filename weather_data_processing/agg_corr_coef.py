"""
Purpose: called by general_scripts.py

This script contains a class: class_missing_days which upon initialization creates a blank pd df.
It contains the following methods:

1) calc_aggs() which takes as args:
- pd df created by yr_calc_stats of txt file to process
- grain yield data in pd df format originally stored in a file named US_corn_grain_yield.txt
It returns:
- an appendation of txt_name/year to the initialized dataframe
- an appendation of the number of times a station had that year as their max temp/min temp/max precip
"""

import pandas as pd
from scipy.stats.stats import pearsonr

#---------------------------------#

class class_corr_coef:
    def __init__(self):
        """
        This class creates upon initialization a pd df that will hold results from the class methods
        """

        self.active_df = pd.DataFrame([], columns=['txt_name', 'oorr_maxTemp', 'corr_minTem', \
                                                   'corr_Precip'])
    #---------------------------------#
    def calc_aggs(self, pd_df_avgs, pd_df_yields):

        length = len(self.active_df)

        for station in pd_df_avgs['txt_name'].unique():
            # conform date domain of Clists to date domain in yields list
            avgs_df = pd_df_avgs[pd_df_avgs['txt_name'] == station]
            avgs_df = avgs_df[avgs_df.avg_max_temp != -9999]
            avgs_df = avgs_df[avgs_df.avg_min_temp != -9999]
            avgs_df = avgs_df[avgs_df.total_precip != -9999]

            cIndex = pd_df_yields.set_index(['year']).index. \
                intersection(avgs_df.set_index(['year']).index)

            avgs_df = avgs_df[avgs_df['year'].isin(cIndex)]
            avgs_df.drop_duplicates(subset=['year'], inplace=True)

            yields_df = pd_df_yields[pd_df_yields['year'].isin(cIndex)]
            yields_list = list(yields_df['yields_1000mt'])

            maxTemp_Clist = list(avgs_df['avg_max_temp'])
            minTemp_Clist = list(avgs_df['avg_min_temp'])
            precip_Clist = list(avgs_df['total_precip'])

            pearson_YmxT, _YmxT = pearsonr(yields_list, maxTemp_Clist)
            pearson_YmnT, _YmnT = pearsonr(yields_list, minTemp_Clist)
            pearson_Yprp, _Yprp = pearsonr(yields_list, precip_Clist)

            self.active_df.loc[length + 1] = [station, round(pearson_YmxT,2),
                                              round(pearson_YmnT,2), round(pearson_Yprp,2)]
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
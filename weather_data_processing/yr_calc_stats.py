"""
Purpose: called by general_scripts.py

This script contains a class: class_calc_stats which upon initialization creates a blank pd df.
It contains the following methods:

1) calc_stats() which takes as args:
- txt filename
- pd df of txt file to process
It returns:
- an appendation of txt_name to the initialized dataframe
- there will be a set of appendations for each year in the pd df of the txt file to process
"""

import pandas as pd

#---------------------------------#
class class_calc_stats:
    def __init__(self):
        """
        This class creates upon initialization a pd df that will hold results from the class methods
        """

        self.active_df = pd.DataFrame([], columns=['txt_name', 'year', \
                                                   'avg_max_temp', 'avg_min_temp', 'total_precip'])

    #---------------------------------#

    def calc_stats(self, txt_name, pd_df):
        """
        
        :param txt_name: name of the text file being passed here
        :param pd_df: the pd.to_table() object of the text file 
        :return: nothing. Appends a row of output to self.active_df
        """

        length = len(self.active_df)

        ndict = {}  # year key, and 3-element tuple of lists ([max_temp], [min_temp], [precip])

        for rowx in pd_df.iterrows():
            eval_list = [rowx[1]['maxtemp_c'], rowx[1]['mintemp_c'], rowx[1]['precip_mil']]

            # add elements of this list to a dictionary using a year key:
            year_key = rowx[1]['ddate'].date().year
            year_key_list = ndict.keys()
            if year_key in year_key_list:  # year already in list. Add to pre-existing tuple
                if eval_list[0] != -9999:
                    ndict[year_key][0].append(eval_list[0])
                if eval_list[1] != -9999:
                    ndict[year_key][1].append(eval_list[1])
                if eval_list[2] != -9999:
                    ndict[year_key][2].append(eval_list[2])
            else:  # year not in list. Add this key with 3 lists
                ndict[year_key] = ([], [], [])

        # loop through dictionary. For each year, perform the necessary aggregation. Write to active_df
        for n, year_y in enumerate(ndict.keys()):
            # take average and sum metrics
            try:
                max_temp_avg = sum(ndict[year_y][0]) / float(len(ndict[year_y][0]))
            except:
                max_temp_avg = -9999
            #---#
            try:
                min_temp_avg = sum(ndict[year_y][1]) / float(len(ndict[year_y][1]))
            except:
                min_temp_avg = -9999
            #---#
            try:
                cum_precip = sum(ndict[year_y][2])
            except:
                cum_precip = -9999
            # append to active_df
            self.active_df.loc[length + (n + 1)] = [txt_name, year_y, round(max_temp_avg,2), \
                                               round(min_temp_avg,2), round(cum_precip,2)]
            self.active_df.reset_index()

        return None
    #---------------------------------#
    def write_out(self, file_path):
        """
        :return: ejects a text file whose rows are sorted by filename
        """
        self.active_df.to_csv(file_path, header=None, index=None, mode='a', sep='   ')

        return None
#---------------------------------#
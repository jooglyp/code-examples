"""
Purpose: called by general_scripts.py

This script contains a class: class_missing_days which upon initialization creates a blank pd df.
It contains the following methods:
 
1) calc_missing_days() which takes as args:
- txt filename
- pd df of txt file to process
It returns:
- an appendation of txt_name/days to the initialized dataframe
"""

import pandas as pd

#---------------------------------#
class class_missing_days:
    def __init__(self):
        """
        This class creates upon initialization a pd df that will hold results from the class methods
        """

        self.active_df = pd.DataFrame([], columns=['txt_name', 'missing_data_days'])

    #---------------------------------#
    def calc_missing_days(self, txt_name, pd_df):
        """

        :param txt_name: name of the text file being passed here
        :param pd_df: the pd.to_table() object of the text file 
        :return: nothing. Appends a row of output to self.active_df
        """
        length = len(self.active_df)
        counter = 0

        for rowx in pd_df.iterrows():
            eval_list = [rowx[1]['maxtemp_c'], rowx[1]['mintemp_c'], rowx[1]['precip_mil']]
            rules = [eval_list[0] != -9999,
                     eval_list[1] != -9999,
                     eval_list[2] == -9999]

            if all(rules):
                counter += 1
            else:
                pass

        # append to active_df
        self.active_df.loc[length + 1] = [txt_name, counter]
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
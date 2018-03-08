

"""
Purpose:
1) Query the RSM database with the TS2 API
2) Run an arbitrary set of balancing algorithms on collated data
3) Take results and write them to a summary output table
"""

##############################################################
# Imports:                                                   #
##############################################################

# Basic Scripts:
import os, datetime, time, csv
import sys
import numpy as np
import pandas as pd

# Exclusive Scripts:
from collections import Counter
import datetime
from datetime import timedelta
from time import strptime
import calendar
from numpy.lib import recfunctions
import re
import math

# ------------------------------------------------------
#################################################
### Directory Management and Model Parameters ###
#################################################

######################
### DATA DIRECTORY ###
######################
w_dir = r"C:\Users\joogl\Dropbox\RSM - RS2 Balancing Algo"
footprint_file = "Ticker_Footprint_SubReg_20170106.csv"
qtr_schedule = "RS Metrics_Fiscal_Quarter_Dates_Matrix.xlsx"
f_dir = os.path.join(w_dir, footprint_file)
q_dir = os.path.join(w_dir, qtr_schedule)

quarter_dictionary = pd.read_excel(q_dir)

ticker_list = ['BBBY', 'BBY', 'BGFV', 'BIG', 'BJRI', 'BWLD', 'BURL', 'CAB', 'CMG', 'CONN', 'DG', \
                'DKS', 'DLTR', 'FDO', 'HD', 'JCP', 'KR', 'KMRT', 'KSS', 'LL', 'LOCO', 'LOW', 'M', 'MNRO', \
                'MRSH', 'PIR', 'PRTY', \
                'PNRA', 'ROST', 'SBUX', 'SHLD', 'SHW', 'SPLS', 'SPG', 'TCS', 'TFM', 'TGT', 'TSCO', 'TJX', \
                'ULTA', 'WFM', 'WMT']

# ---------------------------------------------
###############
### Methods ###
###############

def sampledf(npsample):

    """
    Usage:
    This function converts the structured np "record" array yielded in the data prep process
    into a pandas dataframe.
    ...

    Returns:
    A pd df object
    """

    # Obtain the attributes of the np structured record array
    rdatatype = npsample.dtype
    # Obtain the data descriptions of the attributes. Will be in list-tuple [(),()] form
    datadescr = rdatatype.descr
    # index the np record array data
    # Errata: index = ['Row' + str(i) for i in range(1, len(npsample)+1)]
    index = [i for i in range(1, len(npsample)+1)]
    # Instantiate the np structured record array as a pandas dataframe object
    df = pd.DataFrame(npsample, index=index)
    return df

# -------------------------------------------------------------------------------
def df_str_replace(dataframe, field_list):
    for d in field_list:
        dataframe[d] = dataframe[d].str.replace(',', ' ')
        dataframe[d] = dataframe[d].str.replace('#', ' ')
    return dataframe

# -------------------------------------------------------------------------------
def gen_data(in_report, directory):
    # ----------------------------------------------------------------
    # Conversion of XLSX to CSV and Array
    # ----------------------------------------------------------------
    """
    This process creates an array called "c", which is eventually invoked
    by cnt_loop; cnt_loop is an important function that is invoked by yoy_calc.
    Cnt_loop ends up invoking functions like high_cnt.
    Both cnt_loop and high_cnt only take arrays as primary arguments.
    """

    if os.path.splitext(in_report)[1] == ".xlsx":
        df_out = pd.read_excel(os.path.join(directory, in_report), 'Data')
    elif os.path.splitext(in_report)[1] == ".csv":
        df_out = pd.read_csv(os.path.join(directory, in_report))
    else:
        sys.exit("Incorrect Report Type (.xlsx or .csv ONLY!)")
    df_out = df_str_replace(df_out, ['Address'])
    df_out_np = df_out.to_records()
    c = df_out_np
    return c
# -------------------------------------------------------------------------------

def df_to_sarray(df):
    """
    Convert a pandas DataFrame object to a numpy structured array.
    This is functionally equivalent to but more efficient than
    .to_records() or .as_matrix()

    :param df: the data frame to convert
    :return: a numpy structured array representation of df
    """

    v = df.values
    cols = df.columns
    types = [(cols[i].encode(), df[k].dtype.type) for (i, k) in enumerate(cols)]
    dtype = np.dtype(types)
    z = np.zeros(v.shape[0], dtype)
    for (i, k) in enumerate(z.dtype.names):
        z[k] = v[:, i]
    return z

# -------------------------------------------------------------------------------
def det_qtr(in_month, in_ticker, lookup_matrix):
    """
    Purpose: determine the financial quarter associated with a given ticker and month
    :param month: an integer
    :param ticker: a string
    :param lookup_matrix: a pandas dataframe
    :return: a quarter (integer)
    """
    matrix_record = lookup_matrix[lookup_matrix['Company'] == in_ticker]

    for c, column in enumerate(matrix_record):
        if c > 0 and c < 5:
            try:
                list_split = matrix_record[column][matrix_record.index[0]].split(", ")
            except:
                raise Exception('a supplied ticker in the file list does not exist in the cadence file')
            for matrix_month in list_split:
                matrix_month_n = int(strptime(matrix_month, '%b').tm_mon)
                if matrix_month_n == in_month:
                    return_c = c    # c is the column number = qtr (column 1 is quarter 1, column 4 is quarter 4)
                else:
                    continue
        else:
            continue

    try:
        return return_c
    except NameError:
        raise Exception('No match found for month and ticker combination in det_qtr()')

# -------------------------------------------------------------------------------
def det_wk_weights(in_ticker, lookup_matrix):
    """
    Purpose: determine the weights to be used in a weighted average
    :param in_ticker: a string
    :param lookup_matrix: a pandas dataframe
    :return: list with 3 elements (ea. element gets multiplied by a month in a particular quarter)
    """
    matrix_record = lookup_matrix[lookup_matrix['Company'] == in_ticker]
    cadence_base = matrix_record.iloc[0]['Cadence'].split("-")
    # cadence weights: 5 weeks --> 0.4 | 4 weeks --> 0.3
    cadence_list = []
    for element in cadence_base:
        if element == '5':
            cadence_list.append(0.4)
        elif element == '4':
            cadence_list.append(0.3)
        elif element == 'Calendar':
            cadence_list.append(1)
        else:
            raise Exception('An implausible week number exists in the source week cadence file')

    return cadence_list

# -------------------------------------------------------------------------------
def balance_data(BalancingClass,
                 regex_class,
                 regex_sample,
                 summary_tab,
                 footprint_dir,
                 report_name,
                 data_to_balance,
                 prior_year,
                 current_year,
                 append_to_name,
                 working_directory
                 ):
    """
    Purpose: this function instantiates a data-set as a balancing-class, executes balancing methods,
    and returns (1) the balanced data and (2) the yoy of the balanced data.
    This function also calls summary_tab.yoy_to_summary, where summary_tab is a an object that is
    instantiated by class_yoy_to_summary.
    
    :param BalancingClass: the class object containing balancing methods
    :param regex_class: a regular expression object containing some keyword (see balancing_process())
    :param regex_sample: a regular expression object containing some keyword (see balancing_process())
    :param summary_tab: an object instantiated with class_yoy_to_summary
    :param footprint_dir: the directory containing a sub-region footprint file
    :param report_name: the filename of the raw data object c that is being instantiated as a balancing object
    :param data_to_balance: the raw data object c that is being instantiated herein as a balancing object
    :param prior_year: an integer representing the prior year of the object c
    :param current_year: an integer representing the current year of the object c
    :param append_to_name: a derivative of a check_array element with "_Balanced" tacked onto the end
    :param working_directory: the working directory (one step above the class directory)
    :return: 
    """

    print "---------------------------------------"
    print report_name
    print "Sample Size: %s" % (len(data_to_balance))

    # identify the class name stored in BalancingClass
    module_contents = dir(BalancingClass)
    print module_contents
    related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
    # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
    class_ = getattr(BalancingClass, related_class)
    print class_
    #------------------#
    unbalanced = class_(data_to_balance, prior_year, current_year, footprint_dir)
    class_contents = dir(unbalanced)
    related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
    # (II) Calling a function of a module from a string with the function's name:

    balanced, balanced_yoy = getattr(unbalanced, related_method)()

    # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
    print "Conforming Output to Pandas DF Format..."
    if isinstance(balanced, pd.DataFrame):
        rec_df = balanced.copy()
    else:
        # the output object is a np rec array. Convert to pd df
        rec_df = pd.DataFrame(balanced)

    print "Saving CSV...."
    # write the first balanced dataframe to directory
    report_name = os.path.splitext(report_name)[0]
    sav_csv = "{}_{}.csv".format(report_name, append_to_name)
    sav_csv = os.path.join(working_directory, sav_csv)
    rec_df.drop(['index'], axis = 1, inplace = True)
    rec_df.to_csv(sav_csv, index=False)

    return balanced, balanced_yoy, unbalanced

# -------------------------------------------------------------------------------
def balancing_process(c, prior_yr, current_yr, report_name, mth_n, yr_n, qtr_n, ticker, summary_tab, footprint_dir, \
                      avg_option, check_array, balanced_data_dict, balanced_yoy_dict, unbalanced_dict):

    if avg_option == True:
        class_DDOD = 'class_RB_DDOD_20150309_AvgOnly'
        class_WKE = 'class_RB_WKE_20150309_AvgOnly'
        class_DOW = 'class_RB_DOW_20150309_AvgOnly'
        class_TYPE = 'class_RB_Type_20150309_AvgOnly'
        class_SS = 'class_RB_SameStores_20150309_AvgOnly'
        class_SS1 = 'class_RB_SameStores_plus1_20150309_AvgOnly'
        class_SS2 = 'class_RB_SameStores_v2_20151102_AvgOnly'
        class_POPDEN = 'class_RB_Demographics_20150906_AvgOnly'
        class_REGCOM = 'class_RB_RegCom_v2_20150309_AvgOnly'
        class_REGWKHIGH = 'class_RB_RegWkHigh_20140309_AvgOnly'
        class_REGCENSUS = 'class_RB_RegCensus_20150309_AvgOnly'
        class_SPACES = 'class_RB_Spaces_20150309_AvgOnly'
        class_ZIP = 'class_RB_ZIP_20150906_AvgOnly'
        class_REGONLY = 'class_RB_RegOnly_v2_20150309_AvgOnly'
        class_STATE = 'class_RB_State_20150309_AvgOnly'
        class_REGSPACES = 'class_RB_RegSpaces_20170103_AvgOnly'
        class_REGPOPDEN = 'class_RB_RegPopDen_20170103_AvgOnly'
        class_MATCH_UNMATCH = 'class_MatchUnmatch_Stats_20150908_AvgOnly'
        class_REGCENSUS2 = 'class_RB_RegCensus_v2_20150309_AvgOnly'
    else:
        class_DDOD = 'class_RB_DDOD_20150309'
        class_WKE = 'class_RB_WKE_20150309'
        class_DOW = 'class_RB_DOW_20150309'
        class_TYPE = 'class_RB_Type_20150309'
        class_SS = 'class_RB_SameStores_20150309'
        class_SS1 = 'class_RB_SameStores_plus1_20150309'
        class_SS2 = 'class_RB_SameStores_v2_20151102'
        class_POPDEN = 'class_RB_Demographics_20150906'
        class_REGCOM = 'class_RB_RegCom_v2_20150309'
        class_REGWKHIGH = 'class_RB_RegWkHigh_20140309'
        class_REGCENSUS = 'class_RB_RegCensus_20150309'
        class_SPACES = 'class_RB_Spaces_20150309'
        class_ZIP = 'class_RB_ZIP_20150906'
        class_REGONLY = 'class_RB_RegOnly_v2_20150309'
        class_STATE = 'class_RB_State_20150309'
        class_REGSPACES = 'class_RB_RegSpaces_20170103'
        class_REGPOPDEN = 'class_RB_RegPopDen_20170103'
        class_MATCH_UNMATCH = 'class_MatchUnmatch_Stats_20150908'
        class_REGCENSUS2 = 'class_RB_RegCensus_v2_20150309'

    #----------------------------------------
    # prepare the regex expression for identifying class names in the class modules
    regex_class = re.compile(".*({}).*".format('_balance'), re.IGNORECASE)
    regex_sample = re.compile(".*({}).*".format('_sample'), re.IGNORECASE)

    #############################
    ### SINGLE BALANCE MODELS ###
    #############################

    #----------------------------------------------------------------------------------#
    """
    Process:
    1) loop through check_array (with prefix "class_") to determine which models to run:
        a) if element.split("_") yields more than 1 element, the check_array element is a hybrid model.
            (or it's match/unmatch)
            control statement continue on hybrid models
        b) if element.split("_") yields 1 element only, the check_array element is a simple model.
            execute regular balancing sequence
            i) identify the append_to_name from check_array, with suffix "_Balanced"
            ii) call balance_data(args)
            iii) use the return from balance_data(args) for summary_tab.yoy_to_summary()
                - ensure that the return is named with the element's normal expression + _BALANCED
    2) Run match/unmatch separately
    3) Run unmatched-> zip separately
    4) Construct the Unmatched-Zip + Match dataset
    5) loop again through check_array (with prefix "class_")
        a) if element.split("_") yields more than 1 element, this is a hybrid model. Process it.
            i) identify the input dataset using element.split("_")[0] (assuming it's hybrid)
            ii) if this prefix is "ZUM" then we use the dataset from (4)
            iii) if element is MATCH_UNMATCH, continue
        b)
            i) call balance_data(args)
            ii) use the return from balance_data(args) for summary_tab.yoy_to_summary()
    """

    # (1)
    for n, model in check_array.iterrows():
        if len(check_array.iloc(1)[n][0].split("_")) > 1:
            # this model is a hybrid. continue
            continue
        elif check_array.iloc(1)[n][1] == 0:    # do not process models where In_Use = 0!
            continue
        else:   # the model name has only 1 name. It's a simple model
            base_name = check_array.iloc(1)[n][0].split("_")[0]
            # regex_module = re.compile(".*({}).*".format(base_name), re.IGNORECASE)
            model_class_name = "class_" + base_name
            append_to_name = base_name + "_Balanced"

            # retrieve the BalancingClass module using variable string of the class name in model_clas_name:

            """
            parsers = [v for (k, v) in locals().items()
                       if k.startswith('class_')]
            module_list = []
            for i in parsers:
                try:
                    if i.startswith('class_'):
                        module_list.append(i)
                except:
                    continue

            related_class = [m.group(0) for l in module_list for m in [regex_module.search(l)] if m][0]
            """
            print model_class_name
            # need a string in __import__. Want the explicit name of the class. Variables class_module.
            BalancingClass = __import__(eval(model_class_name))
            print BalancingClass
            balanced_data, balanced_yoy, unbalanced = balance_data(BalancingClass,
                                                         regex_class,
                                                         regex_sample,
                                                         summary_tab,
                                                         footprint_dir,
                                                         report_name,
                                                         c,
                                                         prior_yr,
                                                         current_yr,
                                                         append_to_name,
                                                         w_dir
                                                         )

            module_name = unbalanced.__class__.__name__
            print "Module name for summary yoy table:"
            print module_name
            summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_yoy, module_name)
            # store balanced_data and balanced_yoy with class-specific names in their respective dictionaries
            balanced_data_dict["balanced_" + base_name] = balanced_data
            print balanced_data_dict.keys()
            balanced_yoy_dict["balanced" + base_name + "_yoy"] = balanced_yoy
            unbalanced_dict["unbalanced" + base_name] = unbalanced

    # (2)
    # Model: Match/Unmatch
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name

        BalancingClass = __import__(eval("class_MATCH_UNMATCH"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_mum = class_(c, prior_yr, current_yr, report_name, footprint_dir)
        print "Sample Size: %s" % (len(c))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_mum)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_matched, balanced_unmatched, balanced_matched_yoy, balanced_unmatched_yoy, balanced_overall_yoy  = \
            getattr(unbalanced_mum, related_method)()

        unbalanced_dict["unbalanced" + base_name] = unbalanced_mum

        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Match_Balanced.csv"
        balanced_matched = balanced_matched.copy().drop(['index'], axis = 1)
        balanced_matched.to_csv(sav_csv, index=False)
        #-----#
        balanced_data_dict["balanced_" + base_name] = balanced_matched
        balanced_yoy_dict["balanced" + base_name + "_yoy"] = balanced_matched_yoy

        module_name_1 = "matched"
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_matched_yoy, module_name_1)

        #--------------------------------------------------------------------------------------------#
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Unmatch_Balanced.csv"
        balanced_unmatched = balanced_unmatched.copy().drop(['index'], axis = 1)
        balanced_unmatched.to_csv(sav_csv, index=False)
        #-----#
        balanced_data_dict["balanced_" + base_name] = balanced_unmatched
        balanced_yoy_dict["balanced" + base_name + "_yoy"] = balanced_unmatched_yoy

        module_name_1 = "unmatched"
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_unmatched_yoy, module_name_1)

    #----------------------------------------------------------------------------------#

    ############################
    ### MULTI BALANCE MODELS ###
    ############################

    #####
    # 1 #
    #####
    #--------------------------#
    # Model: TYPE
    if check_array[check_array['model']=='TYPE']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='TYPE_REGCENSUS']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Type is already balanced. Proceeding with secondary balancing."
        module_name_1 = unbalanced_dict['unbalancedTYPE'].__class__.__name__

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegCensus (uses pd df)]
        #--------------------------#
        # Model: RegCensus
        # since RegCensus takes np rec array, reconvert balanced_TYPE to np rec array
        balanced_type_np = balanced_data_dict['balanced_TYPE'].to_records()
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGCENSUS"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regcensus = class_(balanced_type_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_type_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regcensus)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_type_regcensus, balanced_type_regcensus_yoy = getattr(unbalanced_regcensus, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_type_regcensus, pd.DataFrame):
            rec_df = balanced_type_regcensus.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_type_regcensus) + 1)]
            rec_df = pd.DataFrame(balanced_type_regcensus, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Type_RegCensus_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_regcensus.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_type_regcensus_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 2 #
    #####
    #--------------------------#
    # Model: TYPE
    if check_array[check_array['model']=='TYPE']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='TYPE_REGCENSUS2']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Type is already balanced. Proceeding with secondary balancing."
        module_name_1 = unbalanced_dict['unbalancedTYPE'].__class__.__name__

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegCensusv2 (uses numpy rec array)]
        #--------------------------#
        # Model: RegCensus V2
        # since RegCensusv2 takes np rec array, reconvert balanced_TYPE to np rec array
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGCENSUS2"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regcensusv2 = class_(balanced_type_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_type_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regcensusv2)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_type_regcensusv2, balanced_type_regcensusv2_yoy = getattr(unbalanced_regcensusv2, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_type_regcensusv2, pd.DataFrame):
            rec_df = balanced_type_regcensusv2.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_type_regcensusv2) + 1)]
            rec_df = pd.DataFrame(balanced_type_regcensusv2, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Type_RegCensus2_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_regcensusv2.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_type_regcensusv2_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 3 #
    #####
    #--------------------------#
    # Model: Spaces
    if check_array[check_array['model']=='SPACES']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='SPACES_REGONLY']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Spaces is already balanced. Proceeding with secondary balancing."
        module_name_1 = unbalanced_dict['unbalancedSPACES'].__class__.__name__

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegOnly (uses numpy rec array)]
        #--------------------------#
        # Model: RegOnly
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGONLY"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regonly = class_(balanced_data_dict['balanced_SPACES'], prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_data_dict['balanced_SPACES']))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regonly)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_spaces_regonly, balanced_spaces_regonly_yoy = getattr(unbalanced_regonly, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_spaces_regonly, pd.DataFrame):
            rec_df = balanced_spaces_regonly.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_spaces_regonly) + 1)]
            rec_df = pd.DataFrame(balanced_spaces_regonly, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Spaces_RegOnly_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_regonly.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_spaces_regonly_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 4 #
    #####
    #--------------------------#
    # Model: Matched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Matched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "matched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to Zip (already pd df)]
        #--------------------------#
        # Model: ZIP
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_ZIP"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_zip = class_(balanced_matched, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_matched))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_zip)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_matched_zip, balanced_matched_zip_yoy = getattr(unbalanced_zip, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_matched_zip, pd.DataFrame):
            rec_df = balanced_matched_zip.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_matched_zip) + 1)]
            rec_df = pd.DataFrame(balanced_matched_zip, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Matched_Zip_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_zip.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_matched_zip_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 5 #
    #####
    #--------------------------#
    # Model: Unmatched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Unmatched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "unmatched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to ZIP (uses numpy rec array)]
        #--------------------------#
        # Model: ZIP
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_ZIP"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_zip = class_(balanced_unmatched, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_unmatched))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_zip)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]

        # (II) Calling a function of a module from a string with the function's name:
        balanced_unmatched_zip, balanced_unmatched_zip_yoy = getattr(unbalanced_zip, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_unmatched_zip, pd.DataFrame):
            rec_df = balanced_unmatched_zip.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_unmatched_zip) + 1)]
            rec_df = pd.DataFrame(balanced_unmatched_zip, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Unmatched_ZIP_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_zip.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_unmatched_zip_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 6 #
    #####
    #--------------------------#
    # Model: Matched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCHED_REGONLY']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Matched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "matched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegOnly (uses numpy rec array)]
        #--------------------------#
        # Model: RegOnly
        # since RegOnly takes np rec array, reconvert balanced_matched to np rec array
        balanced_matched_np = balanced_matched.to_records()
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGONLY"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regonly = class_(balanced_matched_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_matched_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regonly)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_matched_regonly, balanced_matched_regonly_yoy = getattr(unbalanced_regonly, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_matched_regonly, pd.DataFrame):
            rec_df = balanced_matched_regonly.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_matched_regonly) + 1)]
            rec_df = pd.DataFrame(balanced_matched_regonly, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Matched_RegOnly_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_regonly.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_matched_regonly_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 7 #
    #####
    #--------------------------#
    # Model: Unmatched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCHED_REGONLY']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Unmatched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "unmatched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegOnly (uses numpy rec array)]
        #--------------------------#
        # Model: RegOnly
        # since RegOnly takes np rec array, reconvert balanced_matched to np rec array
        balanced_unmatched_np = balanced_unmatched.to_records()
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGONLY"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regonly = class_(balanced_unmatched_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_unmatched_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regonly)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_unmatched_regonly, balanced_unmatched_regonly_yoy = getattr(unbalanced_regonly, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_unmatched_regonly, pd.DataFrame):
            rec_df = balanced_unmatched_regonly.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_unmatched_regonly) + 1)]
            rec_df = pd.DataFrame(balanced_unmatched_regonly, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Unmatched_RegOnly_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_regonly.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_unmatched_regonly_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 8 #
    #####
    #--------------------------#
    # Model: Matched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCHED_SPACES']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Matched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "matched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to Spaces (uses numpy rec array)]
        #--------------------------#
        # Model: Spaces
        # since Spaces takes np rec array, reconvert balanced_matched to np rec array
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_SPACES"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_spaces = class_(balanced_matched_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_matched_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_spaces)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_matched_spaces, balanced_matched_spaces_yoy = getattr(unbalanced_spaces, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_matched_spaces, pd.DataFrame):
            rec_df = balanced_matched_spaces.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_matched_spaces) + 1)]
            rec_df = pd.DataFrame(balanced_matched_spaces, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Matched_Spaces_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_spaces.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_matched_spaces_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #####
    # 9 #
    #####
    #--------------------------#
    # Model: Unmatched
    if check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='UNMATCHED_SPACES']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Unmatched is already balanced. Proceeding with secondary balancing."
        module_name_1 = "unmatched"

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to Spaces (uses numpy rec array)]
        #--------------------------#
        # Model: Spaces
        # since Spaces takes np rec array, reconvert balanced_unmatched to np rec array
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_SPACES"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_spaces = class_(balanced_unmatched_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_unmatched_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_spaces)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_unmatched_spaces, balanced_unmatched_spaces_yoy = getattr(unbalanced_spaces, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_unmatched_spaces, pd.DataFrame):
            rec_df = balanced_unmatched_spaces.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_unmatched_spaces) + 1)]
            rec_df = pd.DataFrame(balanced_unmatched_spaces, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Unmatched_Spaces_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_2 = unbalanced_spaces.__class__.__name__
        module_combined_name = str(module_name_1) + "_" + str(module_name_2)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_unmatched_spaces_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    #################################################
    # Match + Unmatched/Zip2 (Hybrid dataset merge) #
    #################################################
    #--------------------------#
    # Model: Matched + Unmatched
    if check_array[check_array['model']=='ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        # Work Already Completed
        print "Model Matched is already balanced. Proceeding with secondary balancing."
        print "Model Unmatched->Zip2 is already balanced. Proceeding with data-set merge"
        module_name_0 = "matched"
        module_name_1 = "zip_unmatched"

        # Want to combine (1) balanced_unmatched_zip + (2) balanced_matched
        balanced_zipunmatch_match = balanced_unmatched_zip.append(balanced_matched, ignore_index=True)
        # conform the date column into the format expected by most (if not all) of the balancing modules/classes!
        balanced_zipunmatch_match.loc[:, 'Notes'] = pd.to_datetime(balanced_zipunmatch_match['Notes'], format="%m/%d/%Y").dt.strftime('%Y-%m-%d')
        balanced_zipunmatch_match_np = balanced_zipunmatch_match.to_records()
    #--------------------------------------------------------------------------------------------

    ####$#
    # 10 #
    #####$
    #--------------------------#
    # Model: Zip-Unmatched + Matched
    if check_array[check_array['model']=='DDOD']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='ZUM_DDOD']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Zip-Unmatched + Matched exists. Proceeding with secondary balancing."

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to DDOD (uses numpy rec array)]
        #--------------------------#
        # Model: DDOD
        # since RegOnly takes np rec array, reconvert balanced_matched to np rec array
        balanced_zipunmatch_match_np = balanced_zipunmatch_match.to_records()
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_DDOD"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_ddod = class_(balanced_zipunmatch_match_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_zipunmatch_match_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_ddod)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_zum_ddod, balanced_zum_ddod_yoy = getattr(unbalanced_ddod, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_zum_ddod, pd.DataFrame):
            rec_df = balanced_zum_ddod.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_zum_ddod) + 1)]
            rec_df = pd.DataFrame(balanced_zum_ddod, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Zum_DDOD_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_3 = unbalanced_ddod.__class__.__name__
        module_combined_name = str(module_name_0) + "_" + str(module_name_1) + "_" + str(module_name_3)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_zum_ddod_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    ####$#
    # 11 #
    #####$
    #--------------------------#
    # Model: Zip-Unmatched + Matched
    if check_array[check_array['model']=='POPDEN']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='ZUM_DEM']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Zip-Unmatched + Matched exists. Proceeding with secondary balancing."

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to PopDen (uses pd df)]
        #--------------------------#
        # Model: PopDen(Demographics)
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_POPDEN"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_dem = class_(balanced_zipunmatch_match, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_zipunmatch_match))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_dem)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_zum_dem, balanced_zum_dem_yoy = getattr(unbalanced_dem, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_zum_dem, pd.DataFrame):
            rec_df = balanced_zum_dem.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_zum_dem) + 1)]
            rec_df = pd.DataFrame(balanced_zum_dem, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Zum_Dem_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.to_csv(sav_csv, index=False)

        module_name_3 = unbalanced_dem.__class__.__name__
        module_combined_name = str(module_name_0) + "_" + str(module_name_1) + "_" + str(module_name_3)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_zum_dem_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    ####$#
    # 12 #
    #####$
    #--------------------------#
    # Model: Zip-Unmatched + Matched
    if check_array[check_array['model']=='REGPOPDEN']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='ZUM_REGPOPDEN']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Zip-Unmatched + Matched exists. Proceeding with secondary balancing."

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegPopDen (uses pd df)]
        #--------------------------#
        # Model: RegPopDen
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGPOPDEN"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regpopden = class_(balanced_zipunmatch_match, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_zipunmatch_match))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regpopden)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_zum_regpopden, balanced_zum_regpopden_yoy = getattr(unbalanced_regpopden, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_zum_regpopden, pd.DataFrame):
            rec_df = balanced_zum_regpopden.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_zum_regpopden) + 1)]
            rec_df = pd.DataFrame(balanced_zum_regpopden, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Zum_RegPopDen_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.to_csv(sav_csv, index=False)

        module_name_3 = unbalanced_regpopden.__class__.__name__
        module_combined_name = str(module_name_0) + "_" + str(module_name_1) + "_" + str(module_name_3)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_zum_regpopden_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    ####$#
    # 13 #
    #####$
    #--------------------------#
    # Model: Zip-Unmatched + Matched
    if check_array[check_array['model']=='REGONLY']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='ZUM_REGONLY']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Zip-Unmatched + Matched exists. Proceeding with secondary balancing."

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegOnly (uses np rec array)]
        #--------------------------#
        # Model: RegOnly
        # since RegOnly takes np rec array, reconvert balanced_matched to np rec array
        # balanced_zipunmatch_match_np = balanced_zipunmatch_match.to_records()
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGONLY"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regonly = class_(balanced_zipunmatch_match_np, prior_yr, current_yr, footprint_dir)
        print "Sample Size: %s" % (len(balanced_zipunmatch_match_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regonly)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:
        balanced_zum_regonly, balanced_zum_regonly_yoy = getattr(unbalanced_regonly, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_zum_regonly, pd.DataFrame):
            rec_df = balanced_zum_regonly.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_zum_regonly) + 1)]
            rec_df = pd.DataFrame(balanced_zum_regonly, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Zum_RegOnly_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_3 = unbalanced_regonly.__class__.__name__
        module_combined_name = str(module_name_0) + "_" + str(module_name_1) + "_" + str(module_name_3)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_zum_regonly_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    ####$#
    # 14 #
    #####$
    #--------------------------#
    # Model: Zip-Unmatched + Matched
    if check_array[check_array['model']=='REGWKHIGH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='MATCH_UNMATCH']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model'] == 'UNMATCHED_ZIP']['In_Use'].values[0] == 0:
        pass
    elif check_array[check_array['model']=='ZUM_REGWKHIGH']['In_Use'].values[0] == 0:
        pass
    else:
        print "------------------------------------------------------------------"
        print report_name
        # Work Already Completed
        print "Model Zip-Unmatched + Matched exists. Proceeding with secondary balancing."

        #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
        # pass object to RegWknd (uses np rec array)]
        #--------------------------#
        # Model: RegOnly
        print "------------------------------------------------------------------"
        BalancingClass = __import__(eval("class_REGWKHIGH"))
        module_contents = dir(BalancingClass)
        related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
        # (I) Python dynamic instantiation from string name of a class in dynamically imported module:
        class_ = getattr(BalancingClass, related_class)
        unbalanced_regwkhigh = class_(balanced_zipunmatch_match_np, prior_yr, current_yr, footprint_dir)

        print "Sample Size: %s" % (len(balanced_zipunmatch_match_np))
        print "Building Sample ... Checking Convergence Tolerance"
        class_contents = dir(unbalanced_regwkhigh)
        related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
        # (II) Calling a function of a module from a string with the function's name:

        balanced_zum_regwkhigh, balanced_zum_regskhigh_yoy = getattr(unbalanced_regwkhigh, related_method)()

        # detect whether or not the output data is in pd df or not. If it is not, convert to pd df
        print "Conforming Output to Pandas DF Format..."
        if isinstance(balanced_zum_regwkhigh, pd.DataFrame):
            rec_df = balanced_zum_regwkhigh.copy()
        else:
            # the output object is a np rec array. Convert to pd df
            rec_index = [i for i in range(1, len(balanced_zum_regwkhigh) + 1)]
            rec_df = pd.DataFrame(balanced_zum_regwkhigh, index=rec_index)
        print "Saving CSV...."
        # write the first balanced dataframe to directory
        sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Zum_RegWkHigh_Balanced.csv"
        # s = ','.join(unmatched.headers) + '\n'
        rec_df.drop(['index'], axis = 1, inplace = True)
        rec_df.to_csv(sav_csv, index=False)

        module_name_3 = unbalanced_regwkhigh.__class__.__name__
        module_combined_name = str(module_name_0) + "_" + str(module_name_1) + "_" + str(module_name_3)
        # write to summary
        summary_tab.yoy_to_summary(mth_n, yr_n, qtr_n, ticker, balanced_zum_regskhigh_yoy, module_combined_name)
    #--------------------------------------------------------------------------------------------

    print "**************************"
    print "Printing Summary Report..."
    print "**************************"
    print summary_tab.summary_df
    return summary_tab, balanced_data_dict, balanced_yoy_dict, unbalanced_dict

    # END FUNCTION
    #--------------------------------------------------------------------------------------------

# -------------------------------------------------------------------------------
#################
### Execution ###
#################

"""
0.
Instantiate the summary table as a TEMPLATE
*************************************************************************************************************
I.
For each report in raw_reports, 
    i) separate text identifier _Final reports from raw reports. 2 lists created.
    ii) create 2 dictionaries (for 2 lists) that will hold file name + ticker/date identifying info for these files
    ii) for each report in these final/non-final lists, 
        a) identify the ticker. 
        b) identify the date (month number + year number + quarter number)
        c) store info in the dictionary
*************************************************************************************************************
Function: Write YoY to Summary(month number, year number, quarter number, ticker, yoy, model name)
    i) take the instantiated summary table
    ii) for some ticker, locate the latest month number/year number/quarter number
    iii) add a new record, COLUMN-WISE using the args: (1) model name // (2) yoy
        a) locate the right-most column
        b) create an alphanumeric string = model name + yoy
        c) for the current row, write this string to the column to the right of the column located in (a)
*************************************************************************************************************
Function: Balancing Process(in_df, py, cy, report_name):
    i) run balancing module NAME=X
        a) if non-convergence is occurring,
            - log balancing module NAME
            - log tolerance parameters
            - log report_name
            - continue to NEXT balancing module NAME=X+1
        b) else: 
            - invoke Write YoY to Summary(month number, year number, quarter number, \
                                            report_name, ticker, yoy, model name)
            - with the balanced output df, 
                * optional: run balancing module NAME=X+1 (only if multi-thronged)
                        a) if non-convergence is occurring,
                            - log balancing module NAME=X, X+1
                            - log tolerance parameters
                            - log report_name
                        b) else: 
                            - invoke Write YoY to Summary(month number, year number, quarter number, \
                                                            report_name, yoy, model name)
    ii) run balancing module NAME=X+1
        ...
    iii) run balancing module NAME=X+2
        ...
*************************************************************************************************************
II.
Create temporary subset dictionary for ticker (dict a).
For each ticker in the dictionary's ticker section,
    i) store all dictionary elements for this ticker in the dictionary subset (a) 
    Create temporary subset dictionary for year (dict b).
    For each year number in the dictionary's year section,
        ii) store all dictionary elements for this ticker in the dictionary subset (b)
        For each month number in the dictionary's year section,
            a) generate the numpy record array
            b) determine the py and the cy
            c) determine the ticker
            d) determine the month number, year number, and quarter number
            e) Using (iii, iv) invoke the Function: Balancing Process
*************************************************************************************************************
"""

if __name__ == '__main__':
    prompt = """
    Parameters
    ----------
      ----
      Aux Params:
    """
    print prompt
    print "-----------------------------------"

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:
    """
    print prompt_example
    print "-----------------------------------"

    #-------------------------------------------------------------
    """
    directory = raw_input('Directory: ')
    directory = directory.replace("\"", "")
    ticker = input('Ticker: ')
    start_date_input = raw_input('Start Date:  ')
    start_date_input = directory.replace("\"", "")
    converged = input('Convergence? (Yes/No): ') 
    """
    #-------------------------------------------------------------
    """
    (1) detect downloaded files from some master directory using some known prefix. Detect both xlsx and csv
    (2) log the "Full prefix" with the ticker name. The associated file may be csv or xlsx
    (3) iteratively import all balancing algos as classes. Do this guided by a predesignated permutation set.
    note: in the output, the model permutation path should be written directly above the cell containing the result.
    """

    #-------------------------------------------------------------
    """
    Determine which models to run (create a lookup table that will be used in balancing_process()):
    """

    # user input
    Var_DDOD = 1
    Var_WKE = 1
    Var_DOW = 1
    Var_TYPE = 1    # necessary for hybrid models
    Var_SS = 1
    Var_SS1 = 1
    Var_SS2 = 1
    Var_POPDEN = 1
    Var_REGCOM = 1
    Var_REGWKHIGH = 1
    Var_REGCENSUS = 1
    Var_SPACES = 1  # necessary for hybrid models
    Var_ZIP = 1
    Var_REGONLY = 1
    Var_STATE = 1
    Var_REGSPACES = 1
    Var_REGPOPDEN = 1
    Var_MATCH_UNMATCH = 1   # necessary for hybrid models
    #######################
    Var_TYPE_REGCENSUS = 1
    Var_TYPE_REGCENSUS2 = 1
    Var_SPACES_REGONLY = 1
    Var_MATCHED_ZIP = 1
    Var_UNMATCHED_ZIP = 1
    Var_MATCHED_REGONLY = 1
    Var_UNMATCHED_REGONLY = 1
    Var_MATCHED_SPACES = 1
    Var_UNMATCHED_SPACES = 1
    Var_ZUM_DDOD = 1
    Var_ZUM_DEM = 1
    Var_ZUM_REGPOPDEN = 1
    Var_ZUM_REGONLY = 1
    Var_ZUM_REGWKHIGH = 1

    # create tuple
    var_tuple = [('Var_DDOD', Var_DDOD), ('Var_WKE', Var_WKE), ('Var_DOW', Var_DOW), ('Var_TYPE', Var_TYPE),
                 ('Var_SS', Var_SS), ('Var_SS1', Var_SS1), ('Var_SS2', Var_SS2), ('Var_POPDEN', Var_POPDEN),
                 ('Var_REGCOM', Var_REGCOM), ('Var_REGWKHIGH', Var_REGWKHIGH), ('Var_REGCENSUS', Var_REGCENSUS),
                 ('Var_SPACES', Var_SPACES), ('Var_ZIP', Var_ZIP), ('Var_REGONLY', Var_REGONLY),
                 ('Var_STATE', Var_STATE), ('Var_REGSPACES', Var_REGSPACES), ('Var_REGPOPDEN', Var_REGPOPDEN),
                 ('Var_MATCH_UNMATCH', Var_MATCH_UNMATCH), ('Var_TYPE_REGCENSUS', Var_TYPE_REGCENSUS),
                 ('Var_TYPE_REGCENSUS2', Var_TYPE_REGCENSUS2), ('Var_SPACES_REGONLY', Var_SPACES_REGONLY),
                 ('Var_MATCHED_ZIP', Var_MATCHED_ZIP), ('Var_UNMATCHED_ZIP', Var_UNMATCHED_ZIP),
                 ('Var_MATCHED_REGONLY', Var_MATCHED_REGONLY), ('Var_UNMATCHED_REGONLY', Var_UNMATCHED_REGONLY),
                 ('Var_MATCHED_SPACES', Var_MATCHED_SPACES), ('Var_UNMATCHED_SPACES', Var_UNMATCHED_SPACES),
                 ('Var_ZUM_DDOD', Var_ZUM_DDOD), ('Var_ZUM_DEM', Var_ZUM_DEM), ('Var_ZUM_REGPOPDEN', Var_ZUM_REGPOPDEN),
                 ('Var_ZUM_REGONLY', Var_ZUM_REGONLY), ('Var_ZUM_REGWKHIGH', Var_ZUM_REGWKHIGH)]

    # add to dictionary and list
    model_dict = {}
    for var in var_tuple:
        model_dict[var[0].replace('Var_', '')] = var[1]

    model_check = pd.DataFrame([], columns=['model', 'In_Use'])
    for n, model in enumerate(model_dict.keys()):
        model_check.set_value(n, 'model', model)
        model_check.set_value(n, 'In_Use', model_dict[model])

    #-------------------------------------------------------------
    # User selects converged. If Yes, use original classes. Else if No, use average classes.
    converged = 'Yes'
    #*******************************************************************************************************#
    ########################
    ### SCRIPT DIRECTORY ###
    ########################

    # Custom Scripts:
    # directory = os.getcwd() # only appropriate for server-side jobs
    s_dir = r"C:\Users\joogl\Dropbox\RSM - RS2 Balancing Algo\RSM_StatBalance"
    sys.path.insert(0, s_dir)   # add .py file of class to path

    # Class for instantiating a summary file
    import class_yoy_to_summary_v3

    if converged == 'No':
        import class_RB_ZIP_20150906_AvgOnly
        import class_RB_WKE_20150309_AvgOnly
        import class_RB_Type_20150309_AvgOnly
        import class_RB_State_20150309_AvgOnly
        import class_RB_Spaces_20150309_AvgOnly
        import class_RB_SameStores_v2_20151102_AvgOnly
        import class_RB_SameStores_plus1_20150309_AvgOnly
        import class_RB_SameStores_20150309_AvgOnly
        import class_RB_RegWkHigh_20140309_AvgOnly
        import class_RB_RegSpaces_20170103_AvgOnly
        import class_RB_RegPopDen_20170103_AvgOnly
        import class_RB_RegOnly_v2_20150309_AvgOnly
        import class_RB_RegCom_v2_20150309_AvgOnly
        import class_RB_RegCensus_v2_20150309_AvgOnly
        import class_RB_RegCensus_20150309_AvgOnly
        import class_RB_DOW_20150309_AvgOnly
        import class_RB_Demographics_20150906_AvgOnly
        import class_RB_DDOD_20150309_AvgOnly
        import class_MatchUnmatch_Stats_20150908_AvgOnly
        avg_option = True
    else:
        import class_RB_ZIP_20150906
        import class_RB_WKE_20150309
        import class_RB_Type_20150309
        import class_RB_State_20150309
        import class_RB_Spaces_20150309
        import class_RB_SameStores_v2_20151102
        import class_RB_SameStores_plus1_20150309
        import class_RB_SameStores_20150309
        import class_RB_RegWkHigh_20140309
        import class_RB_RegSpaces_20170103
        import class_RB_RegPopDen_20170103
        import class_RB_RegOnly_v2_20150309
        import class_RB_RegCom_v2_20150309
        import class_RB_RegCensus_v2_20150309
        import class_RB_RegCensus_20150309
        import class_RB_DOW_20150309
        import class_RB_Demographics_20150906
        import class_RB_DDOD_20150309
        import class_MatchUnmatch_Stats_20150908
        avg_option = False

    #*******************************************************************************************************#
    #############################
    ### Report Identification ###
    #############################
    # Part 1

    raw_reports = []
    search_box = os.listdir(w_dir)
    report_keyword = str("RS Metrics_")
    regex = re.compile(".*({}).*".format(report_keyword), re.IGNORECASE)

    related = [m.group(0) for l in search_box for m in [regex.search(l)] if m]
    for f in related:
        if f.endswith(".xlsx"):
            raw_reports.append(f)
        elif f.endswith(".csv"):
            raw_reports.append(f)
        else:
            continue

    distilled_reports = []
    for n, f in enumerate(raw_reports):
        # look for the 1st alphanumeric string after the first underscore. If it's greater than 4 characters, drop it
        if len(f.split("_")[1]) > 4:
            continue
        else:
            distilled_reports.append(f)

    del raw_reports

    # I-i) separate text identifier _Final reports from raw reports
    final_report_list = []
    new_report_list = []
    for f_name in distilled_reports:
        f_name_parts = f_name.split("_")
        f_name_last = f_name_parts[-1:][0]
        if f_name_last == 'Final.csv':
            final_report_list.append(f_name)
        else:
            new_report_list.append(f_name)
    # I-ii) create 2 dictionaries that will hold file name + ticker/date identifying info for these files
    # final_report_dict = {}
    # new_report_dict = {}
    """
    Note on distinguishing between final and new reports:
    Final reports are reports that have already been balanced prior to execution of this script. They
    will NOT be used.
    
    New reports are unbalanced reports.
    """
    final_report_dict_df = pd.DataFrame([], columns=['ticker', 'year', 'month', 'quarter'])
    new_report_dict_df = pd.DataFrame([], columns=['ticker', 'year', 'month', 'quarter'])

    # I-iii) populate dictionaries
    for i, txt_rep in enumerate(final_report_list):
        # (a) identify the ticker. Always second element in a split.
        txt_rep_split = txt_rep.split("_")
        txt_rep_ticker = txt_rep_split[1]
        # (b) identify the date elements. Month/Year always 3rd and 4th elements. 4th may require splitting
        txt_rep_month = txt_rep_split[2]
        txt_rep_year = txt_rep_split[3].split(".")[0]
        # generate the month number from the month identifier + quarter from the month number
        txt_rep_month_n = int(strptime(txt_rep_month, '%b').tm_mon)
        txt_rep_qtr_n = det_qtr(txt_rep_month_n, txt_rep_ticker, quarter_dictionary)
        # (c) store info in dictionaries
        # final_report_dict[txt_rep] = txt_rep_ticker, txt_rep_year, txt_rep_month_n, txt_rep_qtr_n
        final_report_dict_df.set_value(i, 'ticker', txt_rep_ticker)
        final_report_dict_df.set_value(i, 'year', txt_rep_year)
        final_report_dict_df.set_value(i, 'month', txt_rep_month_n)
        final_report_dict_df.set_value(i, 'quarter', txt_rep_qtr_n)
        final_report_dict_df.set_value(i, 'report_name', txt_rep)

    cadence_dict = {}
    for i, txt_rep in enumerate(new_report_list):
        # (a) identify the ticker. Always second element in a split.
        txt_rep_split = txt_rep.split("_")
        txt_rep_ticker = txt_rep_split[1]
        # (b) identify the date elements. Month/Year always 3rd and 4th elements. 4th may require splitting
        txt_rep_month = txt_rep_split[2]
        txt_rep_year = txt_rep_split[3].split(".")[0]
        # generate the month number from the month identifier + quarter from the month number
        txt_rep_month_n = int(strptime(txt_rep_month, '%b').tm_mon)

        """
        Important:
        - Quarter is not always the default calendar quarter! Depends on the company defined quarter!
        """
        txt_rep_qtr_n = det_qtr(txt_rep_month_n, txt_rep_ticker, quarter_dictionary)
        #txt_rep_qtr_n = int(math.ceil(float(txt_rep_month_n) / 3))

        # determine the cadence
        cadence_dict[txt_rep_ticker] = det_wk_weights(txt_rep_ticker, quarter_dictionary)

        # (c) store info in dictionaries
        # new_report_dict[txt_rep] = txt_rep_ticker, txt_rep_year, txt_rep_month_n, txt_rep_qtr_n
        new_report_dict_df.set_value(i, 'ticker', txt_rep_ticker)
        new_report_dict_df.set_value(i, 'year', txt_rep_year)
        new_report_dict_df.set_value(i, 'month', txt_rep_month_n)
        new_report_dict_df.set_value(i, 'quarter', txt_rep_qtr_n)
        new_report_dict_df.set_value(i, 'report_name', txt_rep)

    #*******************************************************************************************************#
    ###########################################################
    # Work:                                                   #
    ###########################################################
    # Part 2. Ignore final_report_dict_df`
    print "-----------------------------------------------------------"
    print "Reports to Process:"
    print new_report_list
    print "-----------------------------------------------------------"

    # sliceable source dictioanry
    sliceable = new_report_dict_df.groupby(['ticker', 'year', 'month', 'report_name', 'quarter']).size()
    # unique tickers
    tickers_unique = new_report_dict_df['ticker'].unique()
    # unique years
    years_unique = new_report_dict_df['year'].unique()
    # unique months
    months_unique = new_report_dict_df['month'].unique()
    # unique quarters
    quarters_unique = new_report_dict_df['quarter'].unique()

    #************************************************************************#
    # create summary file
    # errata: start_year = years_unique[-1:][0]
    # errata: start_month = months_unique.min()
    summary_tab = class_yoy_to_summary_v3.create_summary(w_dir, cadence_dict)    # class name is create_summary
    #************************************************************************#

    # Loop through TICKERS
    for symb in tickers_unique:
        # take a subset of sliceable
        ticker_slice = sliceable[symb]
        # Loop through YEARS
        for yr in years_unique:
            try:
                # take a subset of the ticker slice
                ticker_year_slice = ticker_slice[yr]
                # Loop through MONTHS
                for mth in months_unique:
                    try:
                        # take a subset of the ticker_year_slice
                        ticker_year_month_slice = ticker_year_slice[mth]
                        """
                        II-iii(a-e)
                        BEGIN NP REC ARRAY GENERATION AND PARAM IDENTIFICATION FOR BALANCING MODULES
                        """
                        # (a)
                        # get report name + generate numpy rec array
                        report_name = ticker_year_month_slice.index[0][0]
                        c = gen_data(report_name, w_dir)
                        # (b) determine py and cy
                        yr_u = list(np.unique(c['Year']))
                        yr_u.sort()
                        prior_yr, current_yr = yr_u[0], yr_u[1]
                        # (c) - ticker is symb
                        # (d) - month number = mth | year number = yr | quarter number = \
                        #                                               ticker_year_month_slice.index[0][1]
                        rep_qtr = ticker_year_month_slice.index[0][1]
                        # (e) invoke function "BALANCING PROCESS"
                        print "**************************"
                        print "Entering Balancing Process"
                        print "**************************"
                        # Create holding dictionaries for balanced data and unbalanced data:
                        balanced_data_dict = {}
                        balanced_yoy_dict = {}
                        unbalanced_dict = {}
                        # balancing_process() returns an updated summary_tab class object with all attributed methods.
                        # Important: the input to balancing_process() must be the summary_tab class object with all methods.
                        summary_tab, balanced_data_dict, balanced_yoy_dict, unbalanced_dict = \
                                            balancing_process(c, prior_yr, current_yr, report_name, mth, int(yr), \
                                                                rep_qtr, symb, summary_tab, f_dir, avg_option, \
                                                                model_check, balanced_data_dict, balanced_yoy_dict, \
                                                                unbalanced_dict)
                        ejectable_df = summary_tab.eject_df()
                        ejectable_df.to_csv(str(w_dir + "/balancing_results_summary" + ".csv"), index=False,
                                            encoding='utf-8')
                    except:
                        continue
            except:
                continue

    # Eject summary_tab
    ejectable_df = summary_tab.eject_df()
    ejectable_df.to_csv(str(w_dir + "/balancing_results_summary" + ".csv"), index=False, encoding='utf-8')

# END MODULE
# -------------------------------------------------------------

"""
#---------------------------------
# TESTING TEMP ONLY

symb='CONN'
ticker_slice = sliceable[symb]
ticker_year_slice = ticker_slice['2017']
ticker_year_month_slice = ticker_year_slice[9]
# get report name + generate numpy rec array
report_name = ticker_year_month_slice.index[0][0]
c = gen_data(report_name, w_dir)
# (b) determine py and cy
yr_u = list(np.unique(c['Year']))
yr_u.sort()
prior_yr, current_yr = yr_u[0], yr_u[1]
# (c) - ticker is symb
# (d) - month number = mth | year number = yr | quarter number = \
#                                               ticker_year_month_slice.index[0][1]
rep_qtr = ticker_year_month_slice.index[0][1]
footprint_dir = f_dir

check_array = model_check.copy()

#------------------------------#
avg_option = False

if avg_option == True:
    class_DDOD = 'class_RB_DDOD_20150309_AvgOnly'
    class_WKE = 'class_RB_WKE_20150309_AvgOnly'
    class_DOW = 'class_RB_DOW_20150309_AvgOnly'
    class_TYPE = 'class_RB_Type_20150309_AvgOnly'
    class_SS = 'class_RB_SameStores_20150309_AvgOnly'
    class_SS1 = 'class_RB_SameStores_plus1_20150309_AvgOnly'
    class_SS2 = 'class_RB_SameStores_v2_20151102_AvgOnly'
    class_POPDEN = 'class_RB_Demographics_20150906_AvgOnly'
    class_REGCOM = 'class_RB_RegCom_v2_20150309_AvgOnly'
    class_REGWKHIGH = 'class_RB_RegWkHigh_20140309_AvgOnly'
    class_REGCENSUS = 'class_RB_RegCensus_20150309_AvgOnly'
    class_SPACES = 'class_RB_Spaces_20150309_AvgOnly'
    class_ZIP = 'class_RB_ZIP_20150906_AvgOnly'
    class_REGONLY = 'class_RB_RegOnly_v2_20150309_AvgOnly'
    class_STATE = 'class_RB_State_20150309_AvgOnly'
    class_REGSPACES = 'class_RB_RegSpaces_20170103_AvgOnly'
    class_REGPOPDEN = 'class_RB_RegPopDen_20170103_AvgOnly'
    class_MATCH_UNMATCH = 'class_MatchUnmatch_Stats_20150908_AvgOnly'
    class_REGCENSUS2 = 'class_RB_RegCensus_v2_20150309_AvgOnly'
else:
    class_DDOD = 'class_RB_DDOD_20150309'
    class_WKE = 'class_RB_WKE_20150309'
    class_DOW = 'class_RB_DOW_20150309'
    class_TYPE = 'class_RB_Type_20150309'
    class_SS = 'class_RB_SameStores_20150309'
    class_SS1 = 'class_RB_SameStores_plus1_20150309'
    class_SS2 = 'class_RB_SameStores_v2_20151102'
    class_POPDEN = 'class_RB_Demographics_20150906'
    class_REGCOM = 'class_RB_RegCom_v2_20150309'
    class_REGWKHIGH = 'class_RB_RegWkHigh_20140309'
    class_REGCENSUS = 'class_RB_RegCensus_20150309'
    class_SPACES = 'class_RB_Spaces_20150309'
    class_ZIP = 'class_RB_ZIP_20150906'
    class_REGONLY = 'class_RB_RegOnly_v2_20150309'
    class_STATE = 'class_RB_State_20150309'
    class_REGSPACES = 'class_RB_RegSpaces_20170103'
    class_REGPOPDEN = 'class_RB_RegPopDen_20170103'
    class_MATCH_UNMATCH = 'class_MatchUnmatch_Stats_20150908'
    class_REGCENSUS2 = 'class_RB_RegCensus_v2_20150309'

balanced_data_dict = {}
balanced_yoy_dict = {}
unbalanced_dict = {}
                        
#----------------------------------------
# prepare the regex expression for identifying class names in the class modules
regex_class = re.compile(".*({}).*".format('_balance'), re.IGNORECASE)
regex_sample = re.compile(".*({}).*".format('_sample'), re.IGNORECASE)

#----------------------------------------
# Unmatched/Matched
n = 30
base_name = check_array.iloc(1)[n][0].split("_")[0]
# regex_module = re.compile(".*({}).*".format(base_name), re.IGNORECASE)
model_class_name = "class_MATCH_UNMATCH"
append_to_name = base_name + "_Balanced"

# retrieve the BalancingClass module using variable string of the class name in model_clas_name:

print model_class_name
# need a string in __import__. Want the explicit name of the class. Variables class_module.

BalancingClass = __import__(eval("class_MATCH_UNMATCH"))
module_contents = dir(BalancingClass)
related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
# (I) Python dynamic instantiation from string name of a class in dynamically imported module:
class_ = getattr(BalancingClass, related_class)
unbalanced_mum = class_(c, prior_yr, current_yr, report_name, footprint_dir)
print "Sample Size: %s" % (len(c))
print "Building Sample ... Checking Convergence Tolerance"
class_contents = dir(unbalanced_mum)
related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
# (II) Calling a function of a module from a string with the function's name:
balanced_matched, balanced_unmatched, balanced_matched_yoy, balanced_unmatched_yoy, balanced_overall_yoy  = \
    getattr(unbalanced_mum, related_method)()

unbalanced_dict["unbalanced" + base_name] = unbalanced_mum

sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Match_Balanced.csv"
balanced_matched = balanced_matched.copy().drop(['index'], axis = 1)
balanced_matched.to_csv(sav_csv, index=False)
#-----#
balanced_data_dict["balanced_" + base_name] = balanced_matched
balanced_yoy_dict["balanced" + base_name + "_yoy"] = balanced_matched_yoy

sav_csv = w_dir + "/" + report_name.split(".")[0] + "_Unmatch_Balanced.csv"
balanced_unmatched = balanced_unmatched.copy().drop(['index'], axis = 1)
balanced_unmatched.to_csv(sav_csv, index=False)
#-----#
balanced_data_dict["balanced_" + base_name] = balanced_unmatched
balanced_yoy_dict["balanced" + base_name + "_yoy"] = balanced_unmatched_yoy

#-------------

#------------- #------------- #------------- #------------- #-------------
# Unmatched + Zip
# Model: ZIP
print "------------------------------------------------------------------"
BalancingClass = __import__(eval("class_ZIP"))
print "pass 1"
module_contents = dir(BalancingClass)
print "pass 2"
related_class = [m.group(0) for l in module_contents for m in [regex_class.search(l)] if m][0]
print "pass 3"
# (I) Python dynamic instantiation from string name of a class in dynamically imported module:
class_ = getattr(BalancingClass, related_class)
print "pass 4"
unbalanced_zip = class_(balanced_unmatched, prior_yr, current_yr, footprint_dir)
print "Sample Size: %s" % (len(balanced_unmatched))
print "Building Sample ... Checking Convergence Tolerance"
class_contents = dir(unbalanced_zip)
related_method = [m.group(0) for l in class_contents for m in [regex_sample.search(l)] if m][0]
print "pass 5"
# (II) Calling a function of a module from a string with the function's name:
balanced_unmatched_zip, balanced_unmatched_zip_yoy = getattr(unbalanced_zip, related_method)()

#-------------


"""
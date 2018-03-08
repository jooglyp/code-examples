"""
Purpose:

This script runs a type-balancing script for UNBALANCED WEEKLY REPORTS
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

# declare prefix of weekly input reports
input_prefix = "RS_Metrics_weekly"

# TESTING CONSIDERATION: re-import using the following:

# reload(class_Wk_Type_Balance_client)

# invoking class_QYoySignal will import Type_Match since Type_Match will be in the same directory.

##############################################################
# Methods:                                                   #
##############################################################

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

#-------------------------------
def df_str_replace(dataframe, field_list):
    for d in field_list:
        dataframe[d] = dataframe[d].str.replace(',', ' ')
        dataframe[d] = dataframe[d].str.replace('#', ' ')
    return dataframe

#-------------------------------

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

#-------------------------------

###########################################################
# Work:                                                   #
###########################################################

if __name__ == '__main__':

    prompt = """
    Parameters
    ----------
      arg1: local directory of reports
      arg2: ticker to balance
      arg3: start date (M/D/YYYY), example: 7/1/2016 or 10/14/2001
            note: do not use leading zeros
      arg4: week window (example: 4)
            note: indicates how many weeks past the start date to collate
      arg5: week window forward buffer (example: 2)
            note: indicates how many additional weeks past the start date window to collate
            i.e. the number of weeks ahead of the week-window to search for reports (2 is a safe bet)
      ----
      Aux Params:
      The time stamps for observations in the dataset may be for dates outside of the report
      name's time period. This is due to remote sensing lag: the time period corresponds to a 
      report release date that may be based on much older data.
      ----
      arg6: lower bound (example: -3, would mean to look 3 weeks before the start date)
            note: observations of some +N weeks after the elected start date are considered
      arg7: upper bound (example: -1, would mean to look 1 week after the end date)
            note: observations of some -N weeks before the "implied" end date are considered
    """
    print prompt
    print "-----------------------------------"

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:
    
    >>> directory = "C:\Users\joogl\Dropbox\RSM Direct to Client Modules\Balancing"
    >>> ticker = "BBBY"
    >>> start_date_input = "7/1/2016"
    >>> wk_window = 4
    >>> wk_window_u_limit = 2    
    >>> l_bound = -3
    >>> u_bound = 0
    """
    print prompt_example
    print "-----------------------------------"

    directory = raw_input('Directory: ')
    directory = directory.replace("\"", "")
    ticker = input('Ticker: ')
    start_date_input = input('Start Date: ')
    wk_window = input('Week Window Offset: ')
    wk_window_u_limit = input('Week Window Offset Buffer: ')
    l_bound = input('Lower Bound Record Date: ')
    u_bound = input('Upper Bound Record Date: ')

    # Custom Scripts:
    sys.path.insert(0, directory)  # add .py file of class to path
    import class_Wk_Type_Balance_client  # custom module (class_QYoySignal.py)

    # identify the full path name of Metrics_Log.xlsx

    cd = directory

    #---------------------------------------------------------------------

    ##############################################################
    # Initialization                                             #
    ##############################################################

    """
    Assumptions: the file path for metrics_log (Metrics_Log.xlsx) exists.
    :param metrics_log: a valid windows directory and filename

    Purpose:
    Given a Metrics_Log.xlsx file, identify the following
    a) working directory
    b) all weekly reports
    """
    ##########################
    #### IDENTIFY REPORTS ####
    ##########################

    # identify the latest weekly report in the cd
    # (1) construct a list of filenames that share the global variable "input_prefix"
    weekly_reports = []        # attribute: weekly_reports
    for file in os.listdir(cd):
        if file.startswith(input_prefix):
            # if shpfile.endswith("grid.shp"):
            if file.endswith(".csv"):
                weekly_reports.append(file)

    #################################################
    ## Create Ticker List and Collation Dictionary ##
    #################################################

    # this list will be used during individual updates of metrics_log or in ticker_stitch()
    ticker_list = ['BBBY', 'BBY', 'BGFV', 'BIG', 'BJRI', 'BWLD', 'BURL', 'CAB', 'CMG', 'CONN', 'DG', \
                        'DKS', 'DLTR', 'FDO', 'HD', 'JCP', 'KR', 'KMRT', 'KSS', 'LL', 'LOCO', 'LOW', 'M', 'MNRO', \
                        'MRSH', 'PIR', 'PRTY', \
                        'PNRA', 'ROST', 'SBUX', 'SHLD', 'SHW', 'SPLS', 'SPG', 'TCS', 'TFM', 'TGT', 'TSCO', 'TJX', \
                        'ULTA', 'WFM', 'WMT']

    #################################
    ## Manage Datetime Information ##
    #################################

    start_date_raw = datetime.datetime.strptime(str(start_date_input), "%m/%d/%Y").strftime('%Y-%m-%d')
    # Identify start date
    start_date = pd.to_datetime(start_date_raw.split("-")[1] + start_date_raw.split("-")[2] + \
                                start_date_raw.split("-")[0][2:])

    #################################
    ##### Manage Reports by Date ####
    #################################

    # (2) create a separate list that contain the datetimes + week for the given input report
    report_dt = []         # attribute: report dates (Timestamp(''))
    for report in weekly_reports:
        # obtain all alphanumerics after the last underscore
        datestr = report[report.rindex('_')+1:].split(".")[0]
        # obtain the datetime from this string. This will be a date dictionary of a datetime object
        dttime = pd.to_datetime(datestr)
        # append this object to report_dt
        report_dt.append(dttime)

    #*********************************************************************************************************        
    # Create pooled report:
    wk_reports = weekly_reports
    rep_dates = report_dt
    # (1) identify all reports between start_date and end_date
    report_list = []
    """
    Assumption: the files and their dates listed in weekly_reports are ordered the same as the dates
    listed in wk_reports
    """
    rep_timestamps = zip(wk_reports, rep_dates)
    for wk_rep in rep_timestamps:
        # Important: start_date may be 12/31/YYYY. If it is, shift this by 1 day.
        if start_date == pd.to_datetime(str(1231) + str(start_date.date().year)[2:]):
            start_date_s = start_date + timedelta(days=(1))
        else:
            start_date_s = start_date
        if wk_rep[1] >= start_date_s:
            # IMPORTANT: All reports will be pulled for start date until end date(interval) + wk_window
            """
            Very Important: we want report data up to a period out from the start date. The quantopian
            date that will be reported for the yoy based on these data will be the end date calculated
            at the end of this function. This end-date will not be the interval-end_date but rather
            the look-back-window-end_date. 
            """
            if wk_rep[1] < start_date_s + timedelta(days=7 * (wk_window + wk_window_u_limit)):
                report_list.append(wk_rep[0])
            else:
                pass
    # (2) for each eligible report, open it, turn it into a np structured array, and concatenate all reports
    report_dict = {}  # will be storing reports into a dictionary
    for n, filt_report in enumerate(report_list):
        # pass filt_report (file name) and directory to gen_data(in_report, directory)
        c = gen_data(filt_report, cd)
        # take the appropriate subset of this data according to arg --> ticker

        # the ticker might not exist in the data-set.
        try:
            c_subset = c[c['Ticker'] == ticker]
        except:
            raise Exception("User-elected Ticker does not exist in the data set. Try another ticker.")

        # store this report in dictionary
        report_dict[n] = c_subset
    # Important: if no reports are present, set all attributes to np.nan

    # create the end date window:
    end_date_s = start_date_s + timedelta(days=7 * (wk_window))

    # combine all dictionary elements into one master rec.array
    try:

        pooled_wk_rep = np.hstack((report_dict[element] for element in report_dict))

        """
        Addendum 2 (v5):
        Identify cases of hybrid years. For instance if there's a cross-over from late Dec. 2016 into early
        Jan. 2017 for cy, then that would imply the existence of a Dec. 2015 and Jan. 2016 py. In these cases,
        yr_u would contain 3-4 year elements.
    
        Solution:
        1) identify whether an observation is a cy or py:
            a) identify the number of unique dates
            b) if the number of unique dates is greater than 2
                i) find the max date
                ii) subtract 6 months from this date. Call this mid_divide
        2) create a ['py_cy'] field that is in numerical format 99999 or 99998
            a) loop through the rec array. Evaluate dates against mid_divide
            b) populate the py_cy field appropriately
        """

        """
        Important:
        Need to find some arbitrary date that separates py from cy observations. This
        becomes especially necessary when the start date is somewhere near the end of December.
        Want to reclassify Year into a py and cy classification using 999998/999999
        """
        mid_divide = start_date_s - timedelta(days=182)  # heuristic

        n_metrics = recfunctions.rec_append_fields(pooled_wk_rep, "py_cy", [], int)
        # there is now a field called "cy_py" with values all set to 999999
        for rix in range(len(n_metrics)):
            rec_date = pd.to_datetime(n_metrics[rix]['Notes'])
            # evaluate this date:
            if rec_date <= mid_divide:
                # this is a py observation
                n_metrics[rix]["py_cy"] = 999998
            else:
                pass
        """
        print "number py/999998 obs:"
        print len(n_metrics[n_metrics["py_cy"]==999998])
        print "number cy/999999 obs:"
        print len(n_metrics[n_metrics["py_cy"]==999999])
        """
        pooled_wk_rep = n_metrics
        del n_metrics

        """
        Addendum 1 (v5):
        Drop all observations whose dates do not fall within the [start] & [start + week-band-offset]
        """
        n_metrics = recfunctions.rec_append_fields(pooled_wk_rep, "flag", [], int)
        # there is now a field called "flag" with values all set to 999999
        for rix in range(len(n_metrics)):
            # create time indices (cy), start date:
            yr1_start = start_date_s.date().year

            # create time indices (cy), end date:
            yr1_end = end_date_s.date().year

            # Solve for prior year date time stamp
            if start_date_s.date().day < 10:
                start_day_adj = "0"
            else:
                start_day_adj = ""
            if start_date_s.date().month < 10:
                start_month_adj = "0"
            else:
                start_month_adj = ""

            if end_date_s.date().day < 10:
                end_day_adj = "0"
            else:
                end_day_adj = ""
            if end_date_s.date().month < 10:
                end_month_adj = "0"
            else:
                end_month_adj = ""

            """
            Important: The issue of leap years
            - for a cy start of 2016-02-01 and a 4 week window, the cy end will be 2016-02-29
            - for a cy start of 2016-02-29 and a 4 week window, the cy end will be 2016-03-28
            - Both of these windows contain the 2016 leap year February date 02-29.
            - The py date equivalent of the 2016 leap year Feb date 02-29 does not exist on the calendar
            - if 02/29 is found to be a date in start_date_s or end_date_s, then day should be set to 28
            """
            start_md = np.string0(np.string0(start_date_s.date().month) + "-" + \
                                  np.string0(start_date_s.date().day))
            end_md = np.string0(np.string0(end_date_s.date().month) + "-" + \
                                np.string0(end_date_s.date().day))
            if end_md == '2-29':
                # leap year detected
                end_ts = pd.to_datetime("0" + str(2) + \
                                        "" + str(28) + str(yr1_end - 1)[2:])
            else:
                end_ts = pd.to_datetime(end_month_adj + str(end_date_s.date().month) + \
                                        end_day_adj + str(end_date_s.date().day) + str(yr1_end - 1)[2:])

            if start_md == '2-29':
                # leap year detected
                start_ts = pd.to_datetime("0" + str(2) + \
                                          "" + str(28) + str(yr1_start - 1)[2:])
            else:
                start_ts = pd.to_datetime(start_month_adj + str(start_date_s.date().month) + \
                                          start_day_adj + str(start_date_s.date().day) + str(yr1_start - 1)[2:])

            # REC DATE EVALUATION
            rec_date = pd.to_datetime(n_metrics[rix]['Notes'])
            rec_yr = rec_date.date().year

            if rec_date.date().day < 10:
                rec_date_adj = "0"
            else:
                rec_date_adj = ""
            if rec_date.date().month < 10:
                rec_month_adj = "0"
            else:
                rec_month_adj = ""
            """
            Important:
            Determine whether the rec_date is a cy or py observation
            """
            rec_md = np.string0(np.string0(rec_date.date().month) + "-" + \
                                np.string0(rec_date.date().day))

            if n_metrics[rix]['py_cy'] == 999998:  # this is a py observation
                if rec_md == '2-29':
                    # present rec date day is a leap year
                    opp_rec_date = pd.to_datetime("0" + str(2) + \
                                                  "" + str(28) + str(rec_yr + 1)[2:])
                else:
                    opp_rec_date = pd.to_datetime(rec_month_adj + str(rec_date.date().month) + \
                                                  rec_date_adj + str(rec_date.date().day) + str(rec_yr + 1)[2:])
                # evaluate this date:
                if opp_rec_date >= start_date_s + timedelta(days=7 * (l_bound)):
                    if opp_rec_date <= end_date_s - timedelta(days=7 * (u_bound)):
                        check_cy = 1
                    else:
                        check_cy = 0
                else:
                    check_cy = 0

                if rec_date >= start_ts + timedelta(days=7 * (l_bound)):
                    if rec_date <= end_ts - timedelta(days=7 * (u_bound)):
                        check_py = 1
                    else:
                        check_py = 0
                else:
                    check_py = 0

                if check_py == 1:
                    if check_cy == 1:
                        checks = 1
                    else:
                        checks = 0
                else:
                    checks = 0

                if checks == 1:
                    # keep this observation since it falls within the date band
                    pass
                else:
                    # flag this observation
                    n_metrics[rix]["flag"] = 0

            else:  # this is a cy observation
                if rec_md == '2-29':
                    # present rec date day is a leap year
                    opp_rec_date = pd.to_datetime("0" + str(2) + \
                                                  "" + str(28) + str(rec_yr - 1)[2:])
                else:
                    opp_rec_date = pd.to_datetime(rec_month_adj + str(rec_date.date().month) + \
                                                  rec_date_adj + str(rec_date.date().day) + str(rec_yr - 1)[2:])
                # evaluate this date:
                if rec_date >= start_date_s + timedelta(days=7 * (l_bound)):
                    if rec_date <= end_date_s - timedelta(days=7 * (u_bound)):
                        check_cy = 1
                    else:
                        check_cy = 0
                else:
                    check_cy = 0

                if opp_rec_date >= start_ts + timedelta(days=7 * (l_bound)):
                    if opp_rec_date <= end_ts - timedelta(days=7 * (u_bound)):
                        check_py = 1
                    else:
                        check_py = 0
                else:
                    check_py = 0

                if check_py == 1:
                    if check_cy == 1:
                        checks = 1
                    else:
                        checks = 0
                else:
                    checks = 0

                if checks == 1:
                    # keep this observation since it falls within the date band
                    pass
                else:
                    # flag this observation
                    n_metrics[rix]["flag"] = 0

        # drop all observations with flag = 0
        pooled_wk_rep = n_metrics[n_metrics["flag"] != 0].copy()
    except:
        raise Exception("There are no reports in the user elected date range.")

    del n_metrics

    #-----------------------------------------------------------------

    c = pooled_wk_rep.copy()

    #-----------------------------------------------------------------
    # determine ticker
    rt = np.unique(c['Ticker'])[0]
    # define prior year/current year from array
    yr_u = list(np.unique(c['Year']))
    yr_u.sort()
    prior_yr,current_yr = yr_u[0],yr_u[1]
    #-----------------------------------------------------------------

    # Invoke Stepp Type Balancing:

    print "Stepp Type Balancing..."
    print "----------------------------------"
    print "Collated Reports"
    print "----------------------------------"
    unmatched = class_Wk_Type_Balance_client.type_balance(c, prior_yr, current_yr)
    # instantiation creates the attribute unmatched.c (gen_data() deprecated in original Stepp function)
    print "Sample Size: %s" % (len(c))
    print "Building Sample ... Checking Convergence Tolerance"
    unmatched.type_sample()
    print "Finalizing..."
    fn_balanced = unmatched.long_type_sample()  # this must be done to finalize

    """
    # obtain the type matching yoy
    yoy = unmatched.yoy  # this draws on initial balancing work
    wke_yoy100 = unmatched.wke_yoy100
    wkd_yoy100 = unmatched.wkd_yoy100
    yoy_100 = unmatched.yoy_100
    wke_yoy = unmatched.wke_yoy
    wkd_yoy = unmatched.wkd_yoy
    """
    #-----------------------------------------------------------------

    # Write Data
    sav_csv = directory + "/" + start_date_raw + "_Type_Balanced.csv"
    # s = ','.join(unmatched.headers) + '\n'
    out_df = sampledf(fn_balanced)
    out_df.to_csv(sav_csv)

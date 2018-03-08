"""
Purpose:
This class contains the following pseudo-methods:

1)	The compound object contains balancing methods, like Gibbs or Davids random reduction process
2)	The compound object contains a metric_update method, which calculates/recalculates the YoY change for the particular
week-month.
3)	The compound object also contains a signal_gen method, which generates a signal according to a window size (this is
an exogenous parameter) and a standard deviation hurdle (also exogenous but set to 0.5 by default)

Instantiation:
- this class will instantiate a file such as "C:\PATH\Metrics_Log.xlsx". Upon instantiation, the script locates
the directory in which Metrics_Log resides and then identifies all weekly reports in that directory. It is assumed
that Metrics_Log.xlsx sits in a directory with necessary input data for updating the contents of Metrics_Log.

Prerequisites:
Metrics_Log.xlsx has a very specific header structure, with header labels given in alphabetical order. It is 
advisable to include a method that checks for the existence of this file, and if it does not exist, to create
this file with the specific header structure.
"""

##############################################################
# Imports:                                                   #
##############################################################

# Basic Scripts:
import sys
import math
import os

# Exclusive Scripts:
import numpy as np
import pandas as pd
import datetime
from datetime import timedelta
from time import strptime
import calendar
from numpy.lib import recfunctions

# Custom Scripts:
import class_Wk_Type_Balance_v2

##############################################################
# Directory Management:                                      #
##############################################################

# declare prefix of weekly input reports
input_prefix = "RS_Metrics_weekly"
# declare name of output report
output_prefix = "Metrics_Log"  # note in this case prefix is name

##############################################################
# Exogenous Parameters                                       #
##############################################################

wk_window = 5   # this identifies how many weeks of input reports to aggregate
search_offset = 3   # this is the number of weeks to apply to the week-offset search band
l_bound = -3
u_bound = 0

##############################################################
# Non-class Methods                                          #
##############################################################

def get_week_of_month(date):
    date = date.to_pydatetime()

    days_this_month = calendar.mdays[date.month]
    for i in range(1, days_this_month):
        d = datetime.datetime(date.year, date.month, i)
        if d.day - d.weekday() > 0:
            startdate = d
            break
    # now we canuse the modulo 7 appraoch
    return (date - startdate).days //7 + 1

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

##############################################################
# Class Declarations:                                        #
##############################################################

class quant_metrics:
    """
	class type_balance() takes the following arguments:
		1) self
		2) The unbalanced weekly report directory
		# Report as .xlsx or .csv (include file extension in variable name)
		# example: in_report = "RS Metrics_SPG_JUN_2016.xlsx"

	ATTRIBUTES:
	self will have the following attributes:
		1) the numpy structured array, c, which contains pooled (window) data
		2) the week-month period

	METHODS:
        1) David's random reduction process
        2) metric_calc, which calculates/recalculates the YoY change for the particular week-month
            => should take a date range, pool all reports in that range, and calculate the YoY
        3) full_rehash, which subdivides the directory's weekly reports into 2 week segments (using
        the earliest report and the latest report) and invokes metric_calc for each unique period_id
            => this method should only be executed once to generate the historic log of Metrics_Log.xlsx
        4) signal_gen, which generates a signal according to a window size (this is exogenous) and
        a standard deviation hurdle (exogenous but default set to 0.5)
	"""
    #######################
    ## Auxiliary Scripts ##
    #######################

    # Custom Scripts:
    # import David's Type_Matching.py script (ASSUMING it's in the same directory as this script)
    """
    Comments:
    David's random reduction process assumes a specific type of header structure in month-level unbalanced
    reports. In fact, the monthly reports that his methods take contain more elements in the attribute vector
    than in the weekly report. If weekly reports are going to be instantiated using the classed version
    of his type_match script, this parent class should have some of its functions converted into virtual
    functions so that they can be overridden by any child class that is derivative of type_match.
    
    Optionally, type_match could be written in such a way so that decorators (i.e. friend class structure)
    can invoke specific methods in type_match. If there is reason to believe that David's script (along
    with the Gibbs script) will eventually be applied to several variations of the RSM unbalanced report,
    then it may be useful to create a parent class containing several balancing methods.
    """

    ##############################################################
    # Initialization                                             #
    ##############################################################
    def __init__(self, metrics_log):

        """
        Assumptions: the file path for metrics_log (Metrics_Log.xlsx) exists.
        :param metrics_log: a valid windows directory and filename

        example:
        cd = "C:\Users\joogl\Documents\Temp"
        fn = "Metrics_Log.xlsx"
        directory = os.path.join(cd, fn)

        Purpose:
        Given a Metrics_Log.xlsx file, identify the following
        a) working directory
        b) latest weekly report
        c) earliest date to pull weekly reports
        """
        ##########################
        ## DIRECTORY MANAGEMENT ##
        ##########################

        # identify the working directory of metrics_log
        self.directory = metrics_log
        # obtain the path and the filename
        self.cd, self.fn = os.path.split(self.directory)     # attribute: cd
        #-------#
        # identify the latest weekly report in the cd
        # (1) construct a list of filenames that share the global variable "input_prefix"
        self.weekly_reports = []        # attribute: weekly_reports
        for file in os.listdir(self.cd):
            if file.startswith(input_prefix):
                # if shpfile.endswith("grid.shp"):
                if file.endswith(".csv"):
                    self.weekly_reports.append(file)

        ##############################################
        ## Initialize the Metrics_Log Target Object ##
        ##############################################

        self.metrics_log = pd.read_excel(open(self.directory, 'rb'), sheetname='Sheet1')

        #################################################
        ## Create Ticker List and Collation Dictionary ##
        #################################################

        # this list will be used during individual updates of metrics_log or in ticker_stitch()
        self.ticker_list = ['BBBY', 'BBY', 'BGFV', 'BIG', 'BJRI', 'BWLD', 'BURL', 'CAB', 'CMG', 'CONN', 'DG', \
                            'DKS', 'DLTR', 'FDO', 'HD', 'JCP', 'KR', 'KMRT', 'KSS', 'LL', 'LOCO', 'LOW', 'M', 'MNRO', \
                            'MRSH', 'PIR', 'PRTY', \
                            'PNRA', 'ROST', 'SBUX', 'SHLD', 'SHW', 'SPLS', 'SPG', 'TCS', 'TFM', 'TGT', 'TSCO', 'TJX', \
                            'ULTA', 'WFM', 'WMT']

        # this dictionary contains subsets of metrics_log by ticker. This dictionary will be collated in ticker_stitch
        self.dict_collate = {}

        #################################
        ## Manage Datetime Information ##
        #################################

        # (2) create a separate list that contain the datetimes + week for the given input report
        self.report_dt = []         # attribute: report dates (Timestamp(''))
        for report in self.weekly_reports:
            # obtain all alphanumerics after the last underscore
            datestr = report[report.rindex('_')+1:].split(".")[0]
            # obtain the datetime from this string. This will be a date dictionary of a datetime object
            dttime = pd.to_datetime(datestr)
            # append this object to report_dt
            self.report_dt.append(dttime)

        # (3a) identify the most contemporary report in report_dt
        last_date = max(self.report_dt)
        self.last_period = last_date    # this is one of the attributes for instantiation

        # (3b) identify the earliest report in report_dt
        first_date = min(self.report_dt)
        self.first_period = first_date  # this is one of the attributes for instantiation

        # ***** BEGIN PROCESSING END-DATE FOR USE IN ticker_stitch()'s _init_ CASE! ***** #
        # (4) identify all reports that will be used to fill the ancillary data pool
        # ...obtain the week-month-year
        r_wk = self.last_period.week
        # identify the work-week, month, and year of the latest report
        r_wrk_wk = get_week_of_month(self.last_period)  # IMPORTANT
        r_month = self.last_period.date().month # IMPORTANT
        r_year = self.last_period.date().year   # IMPORTANT
        # (5) identify the previous PERIOD of interest (period being defined by wk_window)
        prev_wk = r_wk - wk_window  # this is NOT a work week number
        # prevent reports from the first 2 weeks of the year from drawing a wk param that is negative. Restrict to 01/01
        if prev_wk < 1:
            prev_wk = 1
        d_str = np.string0(r_year) + "-" + "W" + np.string0(prev_wk)
        r_prev_wk = pd.to_datetime(datetime.datetime.strptime(d_str + '-0', "%Y-W%W-%w"))
        # r_prev_wk is a Sunday (Sunday being the last day of the week). Obtain the Monday of this week
        self.last_prev_monday = r_prev_wk - timedelta(days=(6))
        # use get_week_of_month to obtain the work-week for this t0 date
        self.last_wrk_wk_prev = get_week_of_month(self.last_prev_monday) # IMPORTANT (row attribute)
        # get the month and year associated with the Monday of this work week
        self.last_month_prev = self.last_prev_monday.date().month    # IMPORTANT (row attribute)
        self.last_year_prev = self.last_prev_monday.date().year  # IMPORTANT (row attribute)
        ####################################################################################

        # FAIL SAFE: prevent year_prev from being different from r_year.
        """
        Reason for fail safe: if we have present data in the 1st week of Jan, then the previous week of data
        would fall in the previous year. This will lead to a pooled set of observations that span 3 years. YoY
        calculations rely on easily year-subdivided data. Having 3 years over-complicates this process.
        """
        if self.last_year_prev != r_year:
            # set r_wrk_wk_prev, r_month_prev, and r_year_prev to the first day of the year
            self.last_wrk_wk_prev = 1
            self.last_month_prev = 1
            self.last_year_prev = r_year

        """
        IMPORTANT: the following period_id (time0) has been moved to metric_calc()
        self.time0 = np.string0(self.r_year_prev) + "-" + np.string0(self.r_month_prev) + "-" + \
                          np.string0(self.r_wrk_wk_prev)

        Recap:
        a) Assume that Metric_Log.xlsx exists
        b) Identify the latest weekly report in the Metrics_Log.xlsx directory
        c) Identify the earliest date that weekly reports will be pulled for
        """
        # Misc attributes used in yoy calculations:
        self.wke_ly_fl_li = []
        self.wke_ty_fl_li = []
        self.wke_yoy_li = []
        self.wkd_ly_fl_li = []
        self.wkd_ty_fl_li = []
        self.wkd_yoy_li = []
        self.ly_fl_li = []
        self.ty_fl_li = []
        self.yoy_li = []

    #-------------------------------------------------------------
    #################
    # Class Methods #
    #################

    def yoy_calc(self, bal_cpy):
        """
        Note: This class method may be overridden by a similar class method name in:
        class_Wk_Type_Balance_v1. 
        Consequently, it is advisable to write this class as a "virtual" class.

        :param bal_cpy: requires that self.prior_yr and self.current_yr variables exist.
        In order for these variables to exist, self.metric_calc() needs to be run. __init__(self,args*) does
        not yield values for these 2 variables. Note that __init__ simply identifies the working directory,
        weekly reports, weekly report dates, and misc. variables.

        => metric_calc() must be run!

        Notes:
        Some 2016 reports do not seem to contain weekend observations. Deal with these using exceptions.

        :return: a series of yoy metrics
        """
        # weekday/weekend fill rate calculations
        wke_ly = bal_cpy[(bal_cpy['Week End'] == 1) & (bal_cpy['py_cy'] == self.prior_yr)]
        wke_ty = bal_cpy[(bal_cpy['Week End'] == 1) & (bal_cpy['py_cy'] == self.current_yr)]
        wkd_ly = bal_cpy[(bal_cpy['Week End'] == 0) & (bal_cpy['py_cy'] == self.prior_yr)]
        wkd_ty = bal_cpy[(bal_cpy['Week End'] == 0) & (bal_cpy['py_cy'] == self.current_yr)]
        # Weekends
        wke_ly_sm_cr = float(np.sum(wke_ly['Cars']))
        wke_ty_sm_cr = float(np.sum(wke_ty['Cars']))
        # Weekdays
        wkd_ly_sm_cr = float(np.sum(wkd_ly['Cars']))
        wkd_ty_sm_cr = float(np.sum(wkd_ty['Cars']))
        # Weekends
        wke_ly_sm_sp = float(np.sum(wke_ly['Spaces']))
        wke_ty_sm_sp = float(np.sum(wke_ty['Spaces']))
        # Weekdays
        wkd_ly_sm_sp = float(np.sum(wkd_ly['Spaces']))
        wkd_ty_sm_sp = float(np.sum(wkd_ty['Spaces']))
        try:
            wke_ly_fl = (wke_ly_sm_cr / wke_ly_sm_sp) * 100
            wke_ty_fl = (wke_ty_sm_cr / wke_ty_sm_sp) * 100
        except:
            wke_ly_fl = 0
            wke_ty_fl = 0
        wkd_ly_fl = (wkd_ly_sm_cr / wkd_ly_sm_sp) * 100
        wkd_ty_fl = (wkd_ty_sm_cr / wkd_ty_sm_sp) * 100
        try:
            self.wke_yoy = ((wke_ty_fl - wke_ly_fl) / wke_ly_fl) * 100
        except:
            self.wke_yoy = 0
        self.wkd_yoy = ((wkd_ty_fl - wkd_ly_fl) / wkd_ly_fl) * 100
        # ----------------------------
        # full week fill rate calculations
        ly = bal_cpy[bal_cpy['py_cy'] == self.prior_yr]
        ty = bal_cpy[bal_cpy['py_cy'] == self.current_yr]
        ly_sm_cr = float(np.sum(ly['Cars']))
        ty_sm_cr = float(np.sum(ty['Cars']))
        ly_sm_sp = float(np.sum(ly['Spaces']))
        ty_sm_sp = float(np.sum(ty['Spaces']))
        ly_fl = (ly_sm_cr / ly_sm_sp) * 100
        ty_fl = (ty_sm_cr / ty_sm_sp) * 100
        self.yoy = round((((ty_fl - ly_fl) / ly_fl) * 100), 4)
        # ----------------------------
        self.wke_yoy100 = int(self.wke_yoy * 1000)
        self.wkd_yoy100 = int(self.wkd_yoy * 1000)
        self.yoy_100 = int(self.yoy * 1000)
        # important: need to return these variables in a specific order so that they can be called into long_type_sample()
        return self.wke_yoy100, self.wkd_yoy100, self.yoy_100, self.wke_yoy, self.wkd_yoy, self.yoy

    #-----------------------------#
    def write_data(self, ticker):
        """
        Purpose: Run this after running metric_calc. write_data() will take:
         self.f_wk, self.f_mo, self.f_yr, self.f_time0
        and write these values to attributes in Metrics_Log.xlsx

        * Run this in either full_rehash() or standalone
        
        Self.Dates Input: The date that will be populated in the dataset is = Monday Start Date + Week Offset
        i.e. the end date. This method creates problems for the end of the dataset. Although we want the dataset
        date to contain information pulled all the way up to the date, we don't want to create signals for dates
        that haven't actually yet occurred. The solution is to ensure that if the input date Self.Date is
        greater than the date of the last report in the report list, not to populate that report.

        Method:
        write_data() will populate Metrics_Log.xlsx with an evaluation_id. For each invocation of write_data(),
        a unique evaluation_id is populated on the same row as self_f_time0. The index number chosen for evaluation_id
        is based on the previous row's evaluation_id. If no previous evaluation_id exists, then evaluation_id is
        by default 0. Moreover, if f_time0 (period_id) already exists in Metrics_Log.xlsx, then evaluation_id will
        equal whatever the evaluation_id is for the preexisting value of period_id. This constitutes an override.
        The purpose of having evaluation id's is to ensure that new writes of data occur in an ordered fashion and
        are period_id sensitive.

        Parameters: the period_id and date information is attributed to self in metric_calc(). This information
        is derivative of start_date, the parameter (a Monday date) that was also passed to metric_calc(). This full
        date needs to be used to evaluate interval regularity in Metrics_Log.xlsx

        Note: metric_calc() accepts start/end dates either passed from __init__ or from full_rehash(). Consequently,
        period_id will only exist if metric_calc() has been executed.

        Run Priority: Do not run this function until metric_calc() has also been run. Therefore this is a function
        that should only be nested alongside metric_calc() in full_rehash() or it should be invoked standalone
        with __init__ (when a historic log is not being generated).

        :return: a newly updated version of Metrics_Log.xlsx with an evaluation_id
        """
        # (1) obtain a pandas version of Metrics_Log.xlsx; assume that the sheetname here is 'Sheet1'
        # metrics_log1.loc[0] = 6, 2, 2016, "2016-2-6", 1, 5, 1
        # metrics_log1.loc[1] = 8, 2, 2016, "2016-2-8", 2, -5, -1
        """
        Every time write_data() is called, self.metrics_log needs to be recalled into memory for processing.
        During initialization, we have self.metrics_log = pd.read_excel(open(self.directory,'rb'), sheetname='Sheet1'),
        and only upon completion of "ticker_stitch()" is this file overridden.
        """
        # deprecated: metrics_log = pd.read_excel(open(self.directory,'rb'), sheetname='Sheet1')

        # Important: it is possible that no reports were pooled between the start and end date
        """
        ...see metric_calc() for solution. Set self.<attributes> to null.
        """

        """
        Important: since ticker-subsetting is occurring, ensure that metrics_log is ticker specific:
        Note: during a full_rehash(), metrics_log is likely empty.
        """
        # self.ticker_df is created within the ticker-loop in ticker_stitch(). It is reset per ticker iteration
        metrics_log = self.ticker_df
        # deprecated: metrics_log = self.metrics_log[self.metrics_log['ticker'] == ticker]
        """
        try:
            print "current ticker: %s" % (ticker)
            metrics_log = metrics_log[metrics_log['ticker']==ticker]
        except:
            return None
        """
        # RECALLING THE END DATE (possibly  a -1 week-monday from _init_ date that falls between mondays in file)
        # (2) recall self.f_wk, self.f_mo, self.f_yr, self.f_time0, self.yoy
        wrk_wk = self.f_wrk_wk
        wk = self.f_wk
        mo = self.f_mo
        yr = self.f_yr
        pid = self.f_time0
        yoy = self.yoy
        #--#
        # eid = metrics_log[metrics_log['period_id'] == pid].evaluation_id    # currently in float. Will need to be int
        # will also need the exact Monday date of start_date in Timestamp('') format
        d_str = np.string0(yr) + "-" + "W" + np.string0(wk)
        # input of 2016-01-11 will return 2016-01-11...
        monday_date = pd.to_datetime(datetime.datetime.strptime(d_str + '-1', "%Y-W%W-%w"))

        # (3) set evaluation_id. if period_id (e.g. self.f_time0) already exists in [period_id], evaluation_id
        # equals the lookup evaluation_id of this period_id. if not, evaluation_id is 1 + the last evaluation_id
        # in metrics_log['evaluation_id']
        #----#
        # (3a) Get a pd array of period_id. pid_array
        pid_array = metrics_log['period_id']

        # (3b) if pid is contained in pid_array, then evaluation_id equals whatever the eval_id already is
        # test: test1 = test.append(pd.Series([1])), elm = pd.Series((1)), trythis = elm.isin(test1), any(trythis)
        pid_eval = pd.Series((pid))

        """
        Ensure that the week of pid is the correct week with blackbox testing:
        print "original pid:"
        print pid
        print "all prev pid's:"
        print pid_array
        """

        pid_array_bool = pid_eval.isin(pid_array)
        if any(pid_array_bool) == True: # if any element of the boolean array is true, then pid is in pid_array already.
            # identify the current evaluation_id for this pid and assign eid equal to the value of the pd eid
            # print "write_data(): pid is in pid_array already"
            # obtain the eid of the last observation in the dataset:
            eid = metrics_log.evaluation_id[-1:].values[0]
            # eid = int(eid[0])
        elif any(pid_array_bool) == False:
            # Purpose: identify
            # print "write_data(): pid is not in pid_array already"
            """
            Since pid's are based on Monday dates, and since pid's are backfilled using start/end of the entire time
            series, it is possible that the Monday start date obtained in __init__ falls between any 2 consecutive
            Monday dates generated in full_rehash(). Especially (in the 2 week case), if __init__ is run before 1
            entire week elapses since the last execution of full_rehash(). This condition should be checked in this
            boolean evaluation.

            # Exception: if write_data() is performed when Metrics_Log.xlsx is empty, the user is essentially
            generating the 1st and 2nd observations of the historic dataset. In this case, follow this process:

            1) create a row in metrics_log with eid=1 (use insertion logic)
            2) simply exit this hierarchy of booleans to step (4)
            """
            if len(metrics_log) == 0:
                eid = 1
                eid_insert = pd.DataFrame([[eid]], columns=['evaluation_id'])
                metrics_log = pd.concat([metrics_log, eid_insert]).reset_index(drop=True)
            elif len(metrics_log) == 1:
                eid = 2
                eid_insert = pd.DataFrame([[eid]], columns=['evaluation_id'])
                metrics_log = pd.concat([metrics_log, eid_insert]).reset_index(drop=True)
            else:
                # obtain the last monday date recorded in Timestamp('') format
                # (a) for each row in the dataset, obtain week/month/year, create a date, and throw this date into an array
                monday_array = []
                eid_array = []
                for index, row in metrics_log.iterrows():   # be sure to handle date values as integers, not as floats
                    # test: metrics_log1.loc[1]['week'].astype(int)
                    array_wk = int(row['week'])
                    array_yr = int(row['year'])
                    array_d_str = np.string0(array_yr) + "-" + "W" + np.string0(array_wk)
                    array_date = pd.to_datetime(datetime.datetime.strptime(array_d_str + '-1', "%Y-W%W-%w"))
                    # append this date to monday_array
                    monday_array.append(array_date)
                    # keep track of the eid associated with this date:
                    l_eid = row.evaluation_id   # currently in float. Will need to be int
                    eid_array.append(l_eid)
                # (b) sort this list and choose the last element in the list
                monday_array.sort()
                last_monday = monday_array[-1:][0]
                # (c) compare the last monday in the monday array to monday_date

                ########################################################################
                # THIS IS TRUE WHEN THE START DATE FALLS BETWEEN MONDAY INTERVALS!!!!  #
                ########################################################################
                """
                recall all last_mondays are based on a date_start from metric_calc() or from the -1 week-mon in init
                Therefore, this condition implicitly only holds during __init__
                Since the start_date passed from __init__ is always a -wk_offset week-monday (typically 2 weeks),
                as long as this constitutes the date_start, this date will
                """
                # only an _init_ date_start that is 2 weeks (wk_window = 2) ahead shall trigger an append
                # Important Assumption: last_monday must be a Monday; this is true since monday_array is
                # a temporary object created using yr/wk.
                if monday_date + timedelta(days=7*(wk_window)) > last_monday + timedelta(days=7*(wk_window)):
                    # THIS IS IDEAL: eid index will be = last eid + 1
                    eid_array.sort()
                    eid = int(eid_array[-1:][0]) + 1
                    # create a row in metrics_log with this new eid:
                    eid_insert = pd.DataFrame([[eid]], columns=['evaluation_id'])
                    metrics_log = pd.concat([metrics_log, eid_insert]).reset_index(drop=True)
                    # proceed populate this new line item: proceed to step (4)
                else:   # if this is false, that means this evaluation date falls in a previous evaluation window
                    # proposed solution: change the date identifiers for the argument and override the redundant obs
                    # print "preparing to override pre-existing EID and EID attributes..."
                    wrk_wk = get_week_of_month(last_monday)
                    wk = last_monday.week
                    mo = last_monday.date().month
                    yr = last_monday.date().year
                    pid = np.string0(yr) + "-" + np.string0(mo) + "-" + np.string0(wrk_wk)
                    # use the preexisting eid
                    eid = metrics_log.evaluation_id[-1:].values[0]
                    # this will still constitute a change to yoy which is fine
        else:
            pass
        # (4) write elements in (2) (including period_id) to the row of the current evaluation_id.
        # this may constitute and override.
        # not needed: eval_row = metrics_log.loc[metrics_log[metrics_log['evaluation_id'] == eid].index]
        metrics_log.loc[metrics_log.evaluation_id == eid, 'month'] = mo
        metrics_log.loc[metrics_log.evaluation_id == eid, 'period_id'] = pid
        metrics_log.loc[metrics_log.evaluation_id == eid, 'week'] = wk
        metrics_log.loc[metrics_log.evaluation_id == eid, 'year'] = yr
        metrics_log.loc[metrics_log.evaluation_id == eid, 'yoy_change'] = yoy
        metrics_log.loc[metrics_log.evaluation_id == eid, 'date'] = monday_date.date()

        """
        print "PID:"
        print pid
        print "YoY:"
        print yoy
        print "--------------"
        """

        # print monday_date.date()
        # designate the ticker identifier...
        metrics_log.loc[metrics_log.evaluation_id == eid, 'ticker'] = ticker
        # Reset attribute values:
        wrk_wk = np.nan
        wk = np.nan
        mo = np.nan
        yr = np.nan
        pid = np.nan
        yoy = np.nan

        """
        Deprecated:
        Instead of writing this ticker-subset to metrics_log, write it to a class attribute dictionary.
        - collate this dictionary in a super-function like "ticker_stitch()". 
        - collation occurs over this dictionary of subsets, using ticker as a dictionary key
        - for one-time report updates, full_rehash() is not called. hence collation is a process
        that occurs outside of full_rehash() but within ticker_stitch().
        
        # (5) Save over the preexisting version Metrics_Log.xlsx
        metrics_log.to_excel(self.cd + "/Metrics_Log" + ".xlsx", encoding='utf-8')
        """
        # update the df for this current ticker
        self.ticker_df = metrics_log
        # deprecated: self.dict_collate[ticker] = metrics_log

    #-----------------------------#
    def metric_calc(self, ticker, start_date, end_date, apply_balancing=False):
        """
        Purpose:
        Calculates a YoY from pooled observations across 1 or more weekly unbalanced reports.

        Assumptions:
        start_date and end_date are pd.to_datetime() objects; in other words, they are Timestamp('') objects.
        metric_calc will use the date interval to source and pool any and all weekly unbalanced reports that
        fall within this interval.

        Parameters: Pass to this function the start/end dates either generated in __init__ or in full_rehash()

        :return:
        * yoy_change
        * generate period_id from self.first_period itidem self.time0 in __init__
        ---
        * evaluation_id (this is a simple 1 to n index)
        note:
        period_id is either generated in __init__ or in the body of full_rehash()

        Example:
        metric_calc(self, self.r_prev_wk_monday, self.last_period)
        """

        # PART 1. Data Preparation
        # (0) identify the working directory and the list of available reports
        l_dir = self.cd
        wk_reports = self.weekly_reports
        rep_dates = self.report_dt
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
            if wk_rep[1] >= start_date_s - timedelta(days=7*(search_offset)):
                # IMPORTANT: All reports will be pulled for start date until end date(interval) + wk_window
                """
                Very Important: we want report data up to a period out from the start date. The quantopian
                date that will be reported for the yoy based on these data will be the end date calculated
                at the end of this function. This end-date will not be the interval-end_date but rather
                the look-back-window-end_date. 
                """
                if wk_rep[1] < start_date_s + timedelta(days=7*(wk_window)):
                    report_list.append(wk_rep[0])
                else:
                    pass
        # (2) for each eligible report, open it, turn it into a np structured array, and concatenate all reports
        self.report_dict = {}        # will be storing reports into a dictionary
        for n, filt_report in enumerate(report_list):
            # pass filt_report (file name) and directory to gen_data(in_report, directory)
            c = gen_data(filt_report, l_dir)
            # take the appropriate subset of this data according to arg --> ticker

            # the ticker might not exist in the data-set.
            c_subset = c[c['Ticker'] == ticker]

            # store this report in dictionary
            self.report_dict[n] = c_subset
        # Important: if no reports are present, set all attributes to np.nan

        # create the end date window:
        end_date_s = start_date_s + timedelta(days=7 * (wk_window))

        try:
            # combine all dictionary elements into one master rec.array
            self.pooled_wk_rep = np.hstack((self.report_dict[element] for element in self.report_dict))

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

            n_metrics = recfunctions.rec_append_fields(self.pooled_wk_rep, "py_cy", [], int)
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
            self.pooled_wk_rep = n_metrics
            del n_metrics

            """
            Addendum 1 (v5):
            Drop all observations whose dates do not fall within the [start] & [start + week-band-offset]
            """
            n_metrics = recfunctions.rec_append_fields(self.pooled_wk_rep, "flag", [], int)
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

                if n_metrics[rix]['py_cy'] == 999998:    # this is a py observation
                    if rec_md == '2-29':
                        # present rec date day is a leap year
                        opp_rec_date = pd.to_datetime("0" + str(2) + \
                                                       "" + str(28) + str(rec_yr + 1)[2:])
                    else:
                        opp_rec_date = pd.to_datetime(rec_month_adj + str(rec_date.date().month) + \
                                                       rec_date_adj + str(rec_date.date().day) + str(rec_yr + 1)[2:])
                    # evaluate this date:
                    if opp_rec_date >= start_date_s + timedelta(days=7*(l_bound)):
                        if opp_rec_date <= end_date_s - timedelta(days=7*(u_bound)):
                            check_cy = 1
                        else:
                            check_cy = 0
                    else:
                        check_cy = 0

                    if rec_date >= start_ts + timedelta(days=7*(l_bound)):
                        if rec_date <= end_ts - timedelta(days=7*(u_bound)):
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

                else:   # this is a cy observation
                    if rec_md == '2-29':
                        # present rec date day is a leap year
                        opp_rec_date = pd.to_datetime("0" + str(2) + \
                                                       "" + str(28) + str(rec_yr - 1)[2:])
                    else:
                        opp_rec_date = pd.to_datetime(rec_month_adj + str(rec_date.date().month) + \
                                                       rec_date_adj + str(rec_date.date().day) + str(rec_yr - 1)[2:])
                    # evaluate this date:
                    if rec_date >= start_date_s + timedelta(days=7*(l_bound)):
                        if rec_date <= end_date_s - timedelta(days=7*(u_bound)):
                            check_cy = 1
                        else:
                            check_cy = 0
                    else:
                        check_cy = 0

                    if opp_rec_date >= start_ts + timedelta(days=7*(l_bound)):
                        if opp_rec_date <= end_ts - timedelta(days=7*(u_bound)):
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
            self.pooled_wk_rep = n_metrics[n_metrics["flag"]!=0].copy()

            del n_metrics

            #----------------------------------------------------------
            """
            Set prior year and current year to mid_divide identifiers 999998 and 999999
            """
            # Property 2a-2b the prior and current years of this particular data-set
            self.prior_yr = min(self.pooled_wk_rep["py_cy"])
            self.current_yr = max(self.pooled_wk_rep["py_cy"])

            # Part 2. Metric Calculations
            if apply_balancing == False:  # user elects to not balance the data
                """
                yoy_change
                """
                self.wke_yoy100, self.wkd_yoy100, self.yoy_100, \
                self.wke_yoy, self.wkd_yoy, self.yoy = self.yoy_calc(self.pooled_wk_rep)
            else:   # user elects the data type to be balanced
                # Invoke Stepp Type Balancing:
                """
                Possible Suggestion:
                The method self.yoy_calc doesn't need to be turned into overridable class - i.e. a virtual class method. 
                The reason is that the .yoy_calc() method is class-specific. The below object unmatched is actually
                a separate object from self (hybrid_obj in the batch script that calls this class).
                """
                print "Stepp Balancing..."
                print "----------------------------------"
                print self.pooled_wk_rep
                print "----------------------------------"
                unmatched = class_Wk_Type_Balance_v2.type_balance(self.pooled_wk_rep, self.prior_yr, self.current_yr)
                # instantiation creates the attribute unmatched.c (gen_data() deprecated in original Stepp function)
                print "Current reports in processing: %s" % (report_list)
                print "Sample Size: %s" % (len(self.pooled_wk_rep))
                print "pass 0"
                unmatched.type_sample()
                print "pass 1"
                unmatched.long_type_sample()  # this must be done to finalize
                # obtain the type matching yoy
                self.yoy = unmatched.yoy    # this draws on initial balancing work
                self.wke_yoy100 =  unmatched.wke_yoy100
                self.wkd_yoy100 =  unmatched.wkd_yoy100
                self.yoy_100 = unmatched.yoy_100
                self.wke_yoy = unmatched.wke_yoy
                self.wkd_yoy = unmatched.wkd_yoy
        except:
            # print "The following reports caused an error in yoy_calc() ~ likely due to divide by 0:"
            # print report_list
            self.pooled_wk_rep = []
            self.prior_yr = np.nan
            self.current_yr = np.nan
            self.yoy = np.nan
            self.wke_yoy100 = np.nan
            self.wkd_yoy100 = np.nan
            self.yoy_100 = np.nan
            self.wke_yoy = np.nan
            self.wkd_yoy = np.nan
        # ----------------------------------------------------------
        # (4) need to get the following stats into Metrics_Log.xlsx (using an alternative method):
        """
        1) start_date.week
        2) start_date.date().month
        3) start_date.date().year
        4) period_id
        """
        # Construct the period_id (using the _prev date information). This is a unique ID (row attribute)
        """
        IMPORTANT: Although periods in the data set are set by the date interval, the actual look-back window
        is based on a week offset from the start_date in metric_calc. The original interval-end_date is declared and 
        unaltered in full_rehash. Therefore data INTERVALS are set in full_rehash, but the rolling window bands
        have their intervals set in metric_calc().
        """
        end_date = start_date_s + timedelta(days=7 * (wk_window))
        """
        Ensure that the week being created from end date is the correct week with blackbox testing:
        print "--------------------------------------"
        print "end date to be passed to write_data():"
        print end_date
        """
        self.f_wk = end_date.week
        self.f_wrk_wk = get_week_of_month(end_date)  # this number is a work week (like in __Init__)
        self.f_mo = end_date.date().month
        self.f_yr = end_date.date().year
        self.f_time0 = np.string0(self.f_yr) + "-" + np.string0(self.f_mo) + "-" + \
                       np.string0(self.f_wrk_wk)

    #-----------------------------#
    def full_rehash(self, ticker, date_interval, apply_balancing = False):
        """
        Purpose:
        Subdivides the directory's weekly reports into 2 week segments (using the earliest report and the
        latest report) and calculates the YoY's for each unique period_id.

        [self.first_period, self.last_period], where first_period is actually a Monday date!
        Primary Method:
        1) take self.first_period.
            a) identify the two week interval from the MONDAY of self.first_period
                i) It is essential that first_period and every subsequent first_period be the Monday of the week.
                The reason for this is to ensure that the pid's evaluated in write_data() fall on a consistent basis.
            b) invoke metric_calc
            c) loop until the endpoint of the interval falls beyond self.last_period

        Note:
        This method should only be executed once to generate the historic log of Metrics_Log.xlsx
        Normal updates to Metrics_Log.xlsx should never invoke full_rehash(), but rather only invoke metrics_calc()
        (therefore implicitly also invoking write_data()) using self.time0, self.r_prev_wk_monday, and self.last_period

        :return: a fully populated Metrics_Log.xlsx file
        """
        self.stop_metric = False
        # (1) take first_date from __init__, and identify the 2nd week-monday from this starting point,
        # if there are 1+ reports within this date range, invoke metric_calc
        date_start = self.first_period
        wk = date_start.week
        yr = date_start.date().year
        # obtain the monday for this date:
        d_str = np.string0(yr) + "-" + "W" + np.string0(wk)
        monday_date_start = pd.to_datetime(datetime.datetime.strptime(d_str + '-1', "%Y-W%W-%w"))
        """
        Critical: in some calendar weeks, the identified Monday date is after the first_period. We don't want to
        leave out any reports - even the first report in the database - so the 1st date range will use a -1 week
        offset on monday_date_start.
        """
        monday_date_start = monday_date_start - timedelta(days=(7*(1)))
        # note: it is possible that a report in Jan 1 YYYY would then be adjusted to December...
        #   (1a) if the 1st week-monday is in a different year, then set 1st week-monday to 1/1/YYYY

        ####################################################################################################
        # Intuition: do not want periods to overlap years because WANT TO AVOID A DATASET THAT HAS MORE    #
        # THAN 2 YEARS (ONLY WANT A PY AND CY YEAR!!!)                                                     #
        ####################################################################################################

        if monday_date_start.date().year < date_start.date().year:
            # create a timestamp for 1/1/YYYY
            # For example: date_start could be 01/02 and the Monday for that is 12/28. Want a LOWER BOUND date.
            ts_str = '0101' + str(yr)[2:]
            # override date_start
            date_start = pd.to_datetime(ts_str)
        else:
            # override date_start
            date_start = monday_date_start

        # (4) Begin a loop. date_start has been initialized. Determine date_end in loop body.
        # loop until date_end > self.last_period
        day_offset = (7*(wk_window))
        # identify the Monday that is associated with last_period
        last_yr = self.last_period.date().year
        last_wk = self.last_period.week
        last_exp = np.string0(last_yr) + "-" + "W" + np.string0(last_wk)
        last_date = pd.to_datetime(datetime.datetime.strptime(last_exp + '-1', "%Y-W%W-%w"))
        # in the following loop, date_start is endogenous (date_start = date_end)
        while date_start  <= last_date:
            if self.stop_metric == True:
                break
            else:
                #   (1b) generate the date_end, which is equal to an offset of days equal to date_interval
                date_end = date_start + timedelta(days=7*(date_interval))
                """
                Now, the +7th day will always be a Monday, unless the date has been reset to 01/01/YYYY, which
                means that the +7th day from 01/01/YYYY might be a day other than Monday.
                That 7th day is a Sunday (07/01/2017) in 2017 for instance.
                date_end, which is always based on date_start starting at 01/01/YYYY, must be a Monday.
    
                The algorithm identifies this Monday by looking (a) looking at the week of the year 01/01/YYYY falls in
                and then assigning the Monday of that week. Unfortunately, sometimes that week is from the following year,
                and the corresponding Monday might just be the 2nd day of the following year.
    
                If 01/01 falls on the 52/53 week of the preceding year, which happens with
                01/01/2016 (it's the 53rd week of 2015). The date-creator(week, month) constructs a date using
                the logic of the 53rd week of year=2016. The Monday of that week is 01/02/2017.
    
                To prevent this confusion, we use the following HEURISTIC:
                a) if the week is not equal to 1, there will be a year discrepancy to the output.
                b) simply subtract 1 year from the output year
                """
                #   (1c) obtain the week and year and identify the correct Monday
                e_wk = date_end.week
                e_yr = date_end.date().year
                e_str = np.string0(e_yr) + "-" + "W" + np.string0(e_wk)
                """
                Because week is in the monday constructor, week=52 in Dec. would return 12/2016 and not 12/2015!
                """
                monday_date_end = pd.to_datetime(datetime.datetime.strptime(e_str + '-1', "%Y-W%W-%w"))
                """
                For some years, like the Monday of 07/27/15, the Monday date constructor above will actually
                return the subsequent Monday (contrary to 01/18/16). Therefore, ensure that if monday_date_end
                is greater than date_end, to just subtract 1 week from monday_date_end.
                
                By doing this, if we have a 01/01/YYYY start date, we may reset the end-date-Monday to a date
                after the original computation of end_date. Hence, rule this out by just testing if there's
                an exact 1 week difference.
                """

                if int((monday_date_end - date_end).days) == 7:
                    monday_date_end = monday_date_end - timedelta(days=7)

                if monday_date_end.date().year != e_yr:     # fix for monday-constructor-type error
                    # prepare a new date string expression:
                    adj_yr = monday_date_end.date().year
                    adj_day = monday_date_end.date().day
                    adj_mo = monday_date_end.date().month
                    str_adj_day = str(monday_date_end.date().day)
                    str_adj_mo = str(monday_date_end.date().month)
                    # if the day and/or month are less than 10, add a 0 to the the input expression
                    if adj_day < 10:
                        str_adj_day = str(0) + str_adj_day
                    if adj_mo < 10:
                        str_adj_mo = str(0) + str_adj_mo
                    adj_str = str(str_adj_day) + str(str_adj_mo) + str(adj_yr - 1)[2:]

                    # Apply the date heuristic:
                    date_end = pd.to_datetime(adj_str)
                else:
                    date_end = monday_date_end

                """
                Now after doing a lap of end_dates throughout the year. The end_date may spill over to the following year.
                We always want the last date of a year to be the 31st, so terminate date_end at 12/31.
                """
                #   (1d) if the 2nd week-monday is in a different year than date_start, then set 2nd week-monday to 12/31/YYYY
                # Intuition: as before, we cannot have a data-set that has 2+ years under 'Year'
                if date_end.date().year > date_start.date().year:
                    """
                    Infinite loop prevention: date_start may equal 12/31. To prevent UPPER BOUND capping to stay stuck
                    on 12/31, need to evaluate if date_start is already 12/31. If it is not, then run UPPER CAPPING.
                    Otherwise, pass.
                    """
                    if date_start == pd.to_datetime(str(1231) + str(date_start.date().year)[2:]):
                        # date_start is ALREADY currently 12/31. Do not change date_end to 12/31!
                        pass
                    else:
                        # if date_start is anything else, it must be BEFORE 12/31!
                        # create a timestamp for 12/31/YYYY
                        # For example, date end could be in 01/02 when date_start is 12/27. Want an UPPER BOUND limit on date.
                        ts_str = str(1231) + str(date_start.date().year)[2:]
                        # sd_str = '0101' + str(date_end.date().year + 1)[2:]
                        # override date_end
                        date_end = pd.to_datetime(ts_str)
                        # date_start = pd.to_datetime(sd_str)

                # (2) given date_start and date_end, invoke metric_calc()
                self.metric_calc(ticker, start_date=date_start, end_date=date_end, apply_balancing=apply_balancing)
                # (3) after metric_calc() is invoked, then invoke write_data()
                """
                Important:
                Since the time stamp is based on start date + week offset, signals will be populated for dates that
                occur after the most recent report start date + week offset = end date. To prevent write_data() from 
                being called when hitting the start date (-) week offset, use a boolean check (see line 738).
                
                Note:
                self.f_wk = end_date.week
                self.f_wrk_wk = get_week_of_month(end_date)  # this number is a work week (like in __Init__)
                self.f_mo = end_date.date().month
                self.f_yr = end_date.date().year
                """
                if pd.to_datetime(datetime.datetime.strptime(np.string0(self.f_yr) + "-" + "W" + \
                                                            np.string0(self.f_wk) + '-1', "%Y-W%W-%w")) > \
                                                            self.last_period:
                    date_start = date_end
                    self.stop_metric = True
                    continue
                    # break
                else:
                    self.write_data(ticker)
                    # start_date will now be whatever date_end was, unless date_end was 12/31/YYYY
                    """
                    metric_calc() is responsible for the date interval span in the final dataset!
                    1) There is a parameter (i > 0) that indicates what this interval is.
                    2) It is possible that any date arithmetic performed on date_end (say 7 days) 
                    may yield a date_start that is BEFORE the PREVIOUS value of date_start.
                    3) an if statement should be written to determine if date_end < date_start,
                    where date_start here is the start-loop value. It should also be determined
                    if date_end - date_start < 7. If this is true, it must be true that date_end
                    hit the UPPER BOUND LIMIT 12/31/YYYY. When the second condition is true, the
                    first is always true.
                    """
                    date_start = date_end
                    """
                    if int((date_end - date_start).days) < 7:
                        date_start = date_end
                    else:
                        date_start = date_start + timedelta(days=7*(date_interval))
                    """

    #-------------------------------
    def calc_signal_rsm(self, element, stdh, window, block_off):
        """
        Purpose:
        a) for some given date,
            i) determine the week-subset of some window size that's before the monday of the given date
            ii) if the data are already weekly, each window unit corresponds to 1 week
            iii) calculate the summary stats for this subset
            iv) compare the current week (with some lookback period equal to window_wk in the algo above)
            to the standard deviations computed in iv. Determine the corresponding signal
           
        :param element: a pd df of yoy's for a particular ticker 
        :param stdh: the desired multiplier to stdev
        :param window: the number of preceding periods to use in a window with summary statistic attributes
        :return: an updated pd df
        """

        for i, row in element.iterrows():
            # check if yoy_change is not NA
            if np.isnan(row['yoy_change']) == True:
                # signal must not be n/a. Set to 0
                element.loc[element.evaluation_id == int(i + 1), 'signal'] = 0
                continue
            # check if the evaluation row's window contains a start value
            elif row.name - (row.name - window) < 0:
                # signal must not be n/a. Set to 0
                element.loc[element.evaluation_id == int(i + 1), 'signal'] = 0
                continue
            else:
                # compute the signal
                # (a) identify the eid for this row
                id = row['evaluation_id']
                # (b) take the yoy_change subset over the window interval
                subset = element['yoy_change'].iloc[(i - window - 1): i - block_off]
                # (c) remove any NA values in this subset
                subset = subset.dropna()
                # (d) take the average of this subset
                mean = subset.mean()
                # (e) calculate the standard deviation and the hurdles
                stdd = subset.std()
                stdh_u = mean + stdd * stdh
                stdh_l = mean - stdd * stdh
                # (f) evaluate what the signal should be
                if row['yoy_change'] > stdh_u:
                    signal = 1
                elif row['yoy_change'] < stdh_l:
                    signal = -1
                else:
                    signal = 0
                # print "signal:"
                # print signal
                # (g) update the signal for this row
                # print element.loc[element.evaluation_id == int(i+1)]
                element.loc[element.evaluation_id == int(i+1), 'signal'] = signal

    #-------------------------------------------------------------

    def ticker_stitch(self, rehash=False, date_interval=1, balance=False):
        """
        Purpose:
        Create a time panel dataset of tickers with their YoY's calculated. 
        
        Process:
        1) ticker_stitch takes a list of tickers (created in _init_)
        2) ticker_stitch calls metrics_calc() and write_data(), each of these functions will
        take a single argument over a loop over elements of the list of tickers created in (1)
        3) Each subset dataset of YoY's created in (2) will be stored in a dictionary
        4) at the end of the loop, all elements generated in (3) get horizontally stacked
        
        Considerations:
        - ticker_stitch() needs to be able to handle individual report updates, not only
        full_rehash()'s. By default, this function will handle only individual report updates.
        - When an individual report update is conducted, ticker_stitch() still loops through
        the ticker_list generated in _init_; however, full_rehash() will not be called. 
        - individual report updates yield an update to the metrics_log. Updates override subsets
        according to the 'ticker' (a required column in the metrics_log) and the period_id 
        (cross-referenced against the self.start/end date attributes identified in _init).
        
        - historical report generation also yields an update to the metrics_log. Each output
        for each ticker calls the override process.
        
        :return: a time panel dataset of ticker YoY's
        """
        # (1) begin looping through all elements of self.ticker_list
        for ticker_id in self.ticker_list:

            ####################################################
            # Create a holding array for this specific ticker! #
            ####################################################
            print "==================================================================="
            print "Current evaluation ticker is: %s" % (ticker_id)

            # self.ticker_df will hold all writes performed for a ticker in write_data()
            self.ticker_df = self.metrics_log[self.metrics_log['ticker'] == ticker_id]

            # if rehash=True, invoke full_rehash(metric_calc(), write_data()),
            # else invoke metric_calc() and write_data()
            if rehash:
                self.full_rehash(ticker_id, date_interval, apply_balancing=balance)
            # Single Updates, rehash=False
            else:   # for updates using Monday date intervals from _init_
                """
                Note: 
                
                Recall that i_start is always the Monday before the identified-week-Monday of the _init_
                DATE_END REPORT!
                
                There will be occasions in which the Monday start date lies between any two pid date intervals
                in metrics_log; however, write_data() already contains logic for ensuring that such cases
                are handled with an updated of a preexisting pid instead of being handled as an add.
                """
                i_start = self.last_prev_monday
                i_end = i_start + timedelta(days=7*(date_interval))
                if i_end.date().year > i_start.date().year:
                    i_end == pd.to_datetime(str(1231) + str(i_start.date().year)[2:])

                # make sure i_start and i_end (attributed in _init_) are correct dates
                self.metric_calc(ticker_id, start_date = i_start, end_date= i_end, apply_balancing=True)
                self.write_data(ticker_id)
            # Update self.dict_collate
            self.dict_collate[ticker_id] = self.ticker_df

        # (2) calculate signals for each element in self.dict_collate
        for element in self.dict_collate:
            # (element, standard deviation hurdle, period window (6 periods is 3 months)
            self.calc_signal_rsm(self.dict_collate[element], 0.75, 12, 0)

        # (3) self.dict_collate is now ready for collation:
        total_collation = pd.concat([self.dict_collate[ticker_id] for ticker_id in self.dict_collate])

        # (4):
        """
        Notes:
        - the total collation in the case of full_rehash() does not require any further processing and
        can written to .xlsx.
        - the total collation in the case of a singular update using _init_ arguments demands invocation
        of an overriding process, where the overridden object will be Metrics_Log.xlsx. In a setting where
        there is no ticker-heterogeneity, overrides occurred in write_data() according to pid and eid. write_data()
        will now subset metrics_log according to ticker type before proceeding with an update. There shouldn't
        be any identification issues if updates are being written to a pd df subset of metrics_log. 
        
        Hence, write_data() for attribute arguments passed from _init_ will simply update subsets of metrics_log.
        These updated subsets will be stitched together within the list comprehension for total_collation.
        """
        total_collation.to_excel(self.cd + "/Metrics_Log" + ".xlsx", encoding='utf-8')

# END MODULE
# -------------------------------------------------------------
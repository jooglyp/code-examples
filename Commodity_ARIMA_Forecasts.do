* Args:
* This script specifically processes a file called "agg_ToSTATA.csv". This file
* is yielded by running a set of python analyses.

drop order - totarea
drop cprice - avgproduction

rename v43 YrMo
label variable YrMo

gen date = date(fdate, "YMD")
gen month = month(date)
gen year = year(date)
*** MONTHLY DATA ***

* generate a month and year field from the date column

gen qdate = ym(year, month)
format qdate %tm
tsset qdate, monthly

*********************************************************************************
* Rename the Variables:

rename cpriceavg price
rename clmeavg lme
gen aggtot =  aggproduction
gen aaggtot =  avgaggprod

*********************************************************************************

* GRAPH ZINC PRICE:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line price qdate, ylabel(1400(200)2100, gmax angle(horizontal)) ///
tlabel(2013m1(6)2017m1, format(%tm)) xtitle("Year/Month") ///
ytitle("World Zinc Price") ///
title("World Zinc Price") ///
subtitle("USA, 2013-2016") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "Zinc Price")) ///
lwidth(thick  thick  thick ) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH

*********************************************************************************

* GRAPH LME INVENTORY:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line lme qdate, ylabel(2100000(600000)5500000, gmax angle(horizontal)) ///
tlabel(2013m1(6)2017m1, format(%tm)) xtitle("Year/Month") ///
ytitle("LME Zinc Inventory") ///
title("LME Zinc Inventory") ///
subtitle("USA, 2013-2016") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "LME Zinc Inventory")) ///
lwidth(thick  thick  thick ) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH

*********************************************************************************
* GRAPH AGGREGATE ZINC PRODUCTION:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line aggproduction qdate, ylabel(25000(50000)275000, gmax angle(horizontal)) ///
tlabel(2013m1(6)2016m10, format(%tm)) xtitle("Year/Month") ///
ytitle("Square Meters of Crates") ///
title("Aggregate Zinc Production") ///
subtitle("USA, 2013-2016") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "Sq. Meters of Crates")) ///
lwidth(thick  thick  thick ) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH

*********************************************************************************
* GRAPH AVERAGE AGGREGATE ZINC PRODUCTION:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line avgaggprod qdate, ylabel(3200(3000)18000, gmax angle(horizontal)) ///
tlabel(2013m1(6)2016m10, format(%tm)) xtitle("Year/Month") ///
ytitle("Square Meters of Crates") ///
title("Avg Aggregate Zinc Production") ///
subtitle("USA, 2013-2016") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "Sq. Meters of Crates")) ///
lwidth(thick  thick  thick ) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH

*********************************************************************************

*********************************************************
*********************************************************
*********************************************************
* Probably want to deseasonalize LME with YoY
gen yoy_lme = (lme - lme[_n-12])/lme[_n-12]

gen qtr_lme = (lme - lme[_n-3])/lme[_n-3]

* Probably want to deseasonalize Production with YoY
gen yoy_aggtot = (aggtot - aggtot[_n-12])/aggtot[_n-12]

gen qtr_aggtot = (aggtot - aggtot[_n-3])/aggtot[_n-3]

gen yoy_aaggtot = (aaggtot - aaggtot[_n-12])/aaggtot[_n-12]

gen qtr_aaggtot = (aaggtot - aaggtot[_n-3])/aaggtot[_n-3]

* Probably want to deseasonalize Price with YoY
gen yoy_price = (price - price[_n-12])/price[_n-12]

gen qtr_price = (price - price[_n-3])/price[_n-3]

*********************
*********************
* FINAL MODELS:
*********************
*********************

***************************************************************
* Price Forecasts:

**********************************
capture program drop forecast_loop
program define forecast_loop
	syntax varlist [if] [in]
	* alternative: syntax varlist [if] [in], exog(string)
	* ...where string would be for example invoked with `variable'
	* Args:
	* var1 -> dep_var
	* var2 -> orig_dep_var
	* var3 -> date_var
	
	* Declare Variables:
	tokenize `varlist'
	local dep_var : word 1 of `varlist'
	local orig_dep_var : word 2 of `varlist'
	local date_var : word 3 of `varlist'
	* combine the non-exogenous variables
	local covs `dep_var' `orig_dep_var' `date_var'
	di "`covs'"
	* obtain the exogenous variables through macro-list subtraction
	local exog : list varlist - covs
	
	di "`dep_var'"
	di "`orig_dep_var'"
	di "`date_var'"
	di "`exog'"

	// get corresponding integers
	local start = ym(2014, 12)
	local end_ = ym(2017, 3)

	* Begin to loop over date range, using the date-cycling operator "/"
	* (0) set enumeration counters
	local N 1
	* (1) loop over each date element in start to end
	***********************************************************
	/*
	Generate the Date List
	*/

	forvalues element = `start'/`end_' {
		display "`element'"
		arima `dep_var' `exog' if `date_var' <= `element', hessian arima(1,1,1)
		local yhat y_fcprice`N'
		local msehat pr_mse`N'
		local conv_yhat y_fcprice_r`N'
		local yhat_u yhat_u`N'
		local yhat_l yhat_l`N'
		local conv_yhat_u y_fcprice_ru`N'
		local conv_yhat_l y_fcprice_rl`N'
		* Macros for fan charts:
		local yp yp`N'
		local er er`N'
		local q10 q10`N'
		local q10_r q10_r`N'
		local q25 q25`N'
		local q25_r q25_r`N'
		local q50 q50`N'
		local q50_r q50_r`N'
		local q75 q75`N'
		local q75_r q75_r`N'
		local q90 q90`N'
		local q90_r q90_r`N'
		* Example print statement: di "`yhat'"
		* However, don't need outer "" to invoke these macros...
		* Predictions for arima forecasts:
		predict double `yhat', y
		predict `msehat', mse
		* Predictions for fan charts ("river of blood")
		predict double `yp' if `date_var' > `element'
		predict `er', resid
		* real variable conversions and upper and lower bounds of forecast confidence
		gen `yhat_u' = `yhat' + 1.96*sqrt(`msehat')
		gen `yhat_l' = `yhat' - 1.96*sqrt(`msehat')
		gen `conv_yhat' = (1+`yhat')*`orig_dep_var'[_n-3] if `date_var' > `element'
		gen `conv_yhat_u' = (1+`yhat_u')*`orig_dep_var'[_n-3] if `date_var' > `element'
		gen `conv_yhat_l' = (1+`yhat_l')*`orig_dep_var'[_n-3] if `date_var' > `element'
		* obtain quantile bands ("river of blood")
		qreg `er', quantile(0.10)
		predict `q10' if `date_var' > `element'
		gen `q10_r' = (1+(`yp' + `q10'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.25)
		predict `q25' if `date_var' > `element'
		gen `q25_r' = (1+(`yp' + `q25'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.50)
		predict `q50' if `date_var' > `element'
		gen `q50_r' = (1+(`yp' + `q50'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.75)
		predict `q75' if `date_var' > `element'
		gen `q75_r' = (1+(`yp' + `q75'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.90)
		predict `q90' if `date_var' > `element'
		gen `q90_r' = (1+(`yp' + `q90'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		* iterate the counter
		local N = `N' + 1
	}
	***********************************************************
end

* Create a new row in the dataset for the next 2 periods:
* Note: DO THIS ONLY ONCE
tsappend, add(2)
tsset qdate, monthly
***********************************************************

* STATA Programs do not allow nesting of lag or difference operators.
* Proceed to generate lagged variables

gen qaagtL1 = L1.qtr_aaggtot 

* Run the program:

forecast_loop qtr_price price qdate qaagtL1

* End Price Forecasts
***************************************************************
***************************************************************
***************************************************************
* Volume Forecasts:

**********************************
capture program drop forecast_loop
program define forecast_loop
	syntax varlist [if] [in]
	* alternative: syntax varlist [if] [in], exog(string)
	* ...where string would be for example invoked with `variable'
	* Args:
	* var1 -> dep_var
	* var2 -> orig_dep_var
	* var3 -> date_var
	
	* Declare Variables:
	tokenize `varlist'
	local dep_var : word 1 of `varlist'
	local orig_dep_var : word 2 of `varlist'
	local date_var : word 3 of `varlist'
	* combine the non-exogenous variables
	local covs `dep_var' `orig_dep_var' `date_var'
	di "`covs'"
	* obtain the exogenous variables through macro-list subtraction
	local exog : list varlist - covs
	
	di "`dep_var'"
	di "`orig_dep_var'"
	di "`date_var'"
	di "`exog'"

	// get corresponding integers
	local start = ym(2014, 12)
	local end_ = ym(2017, 3)

	* Begin to loop over date range, using the date-cycling operator "/"
	* (0) set enumeration counters
	local N 1
	* (1) loop over each date element in start to end
	***********************************************************
	/*
	Generate the Date List
	*/

	forvalues element = `start'/`end_' {
		display "`element'"
		arima `dep_var' `exog' if `date_var' <= `element', hessian ar(1)
		local yhat Ly_fcprice`N'
		local msehat Lpr_mse`N'
		local conv_yhat Ly_fcprice_r`N'
		local yhat_u Lyhat_u`N'
		local yhat_l Lyhat_l`N'
		local conv_yhat_u Ly_fcprice_ru`N'
		local conv_yhat_l Ly_fcprice_rl`N'
		* Macros for fan charts:
		local yp Lyp`N'
		local er Ler`N'
		local q10 Lq10`N'
		local q10_r Lq10_r`N'
		local q25 Lq25`N'
		local q25_r Lq25_r`N'
		local q50 Lq50`N'
		local q50_r Lq50_r`N'
		local q75 Lq75`N'
		local q75_r Lq75_r`N'
		local q90 Lq90`N'
		local q90_r Lq90_r`N'
		* Example print statement: di "`yhat'"
		* However, don't need outer "" to invoke these macros...
		* Predictions for arima forecasts:
		predict double `yhat', y
		predict `msehat', mse
		* Predictions for fan charts ("river of blood")
		predict double `yp' if `date_var' > `element'
		predict `er', resid
		* real variable conversions and upper and lower bounds of forecast confidence
		gen `yhat_u' = `yhat' + 1.96*sqrt(`msehat')
		gen `yhat_l' = `yhat' - 1.96*sqrt(`msehat')
		gen `conv_yhat' = (1+`yhat')*`orig_dep_var'[_n-3] if `date_var' > `element'
		gen `conv_yhat_u' = (1+`yhat_u')*`orig_dep_var'[_n-3] if `date_var' > `element'
		gen `conv_yhat_l' = (1+`yhat_l')*`orig_dep_var'[_n-3] if `date_var' > `element'
		* obtain quantile bands ("river of blood")
		qreg `er', quantile(0.10)
		predict `q10' if `date_var' > `element'
		gen `q10_r' = (1+(`yp' + `q10'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.25)
		predict `q25' if `date_var' > `element'
		gen `q25_r' = (1+(`yp' + `q25'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.50)
		predict `q50' if `date_var' > `element'
		gen `q50_r' = (1+(`yp' + `q50'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.75)
		predict `q75' if `date_var' > `element'
		gen `q75_r' = (1+(`yp' + `q75'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		qreg `er', quantile(0.90)
		predict `q90' if `date_var' > `element'
		gen `q90_r' = (1+(`yp' + `q90'))*`orig_dep_var'[_n-3] if `date_var' > `element'
		* iterate the counter
		local N = `N' + 1
	}
	***********************************************************
end

* STATA Programs do not allow nesting of lag or difference operators.
* Proceed to generate lagged variables

gen aagtL3 = L3.aaggtot

* Run the program:

forecast_loop qtr_lme lme qdate aagtL3

* End Regressions
****************************************

* Begin Data Consolidation:

**********************
*** MATA Functions ***
**********************

version 11
mata:
mata clear
real matrix function insert(string scalar m, a, rw, name) {
	// Usage: (1) m is the blank matrix, (2) a is the scalar input,
	// (3) rw is the row that will be filled, (4) name is the desired output 
	// name of the matrix
	M = st_matrix(m)
	M[rw, 1] = a 	// 1 refers to the column
	// return a matrix with the same name as the input
	st_matrix(name, M)
	return(M)
}
end

**********************

version 11
mata:
// mata clear
void fillmatrix(string scalar in_vec, r)
{
	// Note: vector, val are reserved words, do not use them.
	
	// The following retrieves the input matrix:
	// > real matrix out_vec
	// > st_view(out_vec=., ., in_vec)
	// > out_vec
	
	// find the rth element of this vector
	real matrix ix
	real matrix element
	element = st_data(ix=r, in_vec, .)
	// X	// This statement will print r
	// store this scalar
	st_numscalar("rscalar", ix)	// This statement will store r to local X
	st_numscalar("output", element)
}
end

**********************

**********************
** DATA CONSOLIDATE **
**********************

capture program drop create_matrices
program create_matrices
	version 11
	syntax [, size(real 1.0)] [if] [in]
	// Usage: create_matrices, size(1)
	matrix forecast = J(`size', 1, .)
	matrix upper_bound = J(`size', 1, .)
	matrix lower_bound = J(`size', 1, .)
	matrix quantile_10 = J(`size', 1, .)
	matrix quantile_25 = J(`size', 1, .)
	matrix quantile_50 = J(`size', 1, .)
	matrix quantile_75 = J(`size', 1, .)
	matrix quantile_90 = J(`size', 1, .)
end

**********************
* PRICE CONSOLIDATE **
**********************
* Important Note: need to globalize all parameters or else they will not be available in forvalues{}...
* (0) Determine the rank of the data-set. Record under the local macro size
sum(qdate)
* Note that local size = r(N) followed by global size = `size' will not work since you can't macro a macro.
global size = r(N)

* (2) Set column counter for variable names t+1
global N = 1

* (3) Count the rank of the t+1 matrix (same-prefix count of variables)
unab mvars : q10_r*
global count : word count `mvars'
* display `count'

* (1) Set row counter starting at the row containing the 1st out of sample forecast.
global r = $size - $count + 1

* (4) Create "holding matrices" for the outputs of the search-loop
* Note: these will eventually be the outputs that are rejoined to the original STATA data matrix
create_matrices, size($size)

* matrix list forecast

forvalues num = $N/$count {
	* (a) Declare matrix names for the N (t+1) forecast iterations of the vector subset 
	local conv_yhat y_fcprice_r`num'
	local conv_yhat_u y_fcprice_ru`num'
	local conv_yhat_l y_fcprice_rl`num'
	local q10_r q10_r`num'
	local q25_r q25_r`num'
	local q50_r q50_r`num'
	local q75_r q75_r`num'
	local q90_r q90_r`num'

	* (b) Assign STATA data to MATA-compatible matrices for each prefix N
	* note 1: the data is identified from the local macros containing variable names.
	* note 2: although conv_yhat is accessed with di "`conv_yhat'", mkmat takes `conv_yhat'
	/* DEPRECATED:
	mkmat `conv_yhat', matrix(forecast_`N')
	* Matrix list conv_yhat
	mkmat `conv_yhat_u', matrix(upper_bound_`N')
	mkmat `conv_yhat_l', matrix(lower_bound_`N')
	mkmat `q10_r', matrix(quantile_10_`N')
	mkmat `q25_r', matrix(quantile_25_`N')
	mkmat `q50_r', matrix(quantile_50_`N')
	mkmat `q75_r', matrix(quantile_75_`N')
	mkmat `q90_r', matrix(quantile_90_`N')
	*/

	* Assign the global variable to this local subroutine
	local r = $r
	/* (c) Identify the rth element of each of these MATA-compatible matrices. Assign this 
	element to the rth row in the appropriate "holding matrix". The scalar macro name
	can be override for each iteration N
	*/
	mata: fillmatrix("`conv_yhat'", $r)
	/* VERY IMPORTANT: Use the "=" operator to actually override out_val with output's value
	instead of making out_val a mirror-copy of output. */
	local out_val = output
	* (d) Update the "holding matrices":
	mata: insert("forecast", `out_val', $r, "forecast")
	* matrix list forecast

	mata: fillmatrix("`conv_yhat_u'", $r)
	local out_val = output
	mata: insert("upper_bound", `out_val', $r, "upper_bound")

	mata: fillmatrix("`conv_yhat_l'", $r)
	local out_val = output
	mata: insert("lower_bound", `out_val', $r, "lower_bound")

	mata: fillmatrix("`q10_r'", $r)
	local out_val = output
	mata: insert("quantile_10", `out_val', $r, "quantile_10")

	mata: fillmatrix("`q25_r'", $r)
	local out_val = output
	mata: insert("quantile_25", `out_val', $r, "quantile_25")

	mata: fillmatrix("`q50_r'", $r)
	local out_val = output
	mata: insert("quantile_50", `out_val', $r, "quantile_50")

	mata: fillmatrix("`q75_r'", $r)
	local out_val = output
	mata: insert("quantile_75", `out_val', $r, "quantile_75")

	mata: fillmatrix("`q90_r'", $r)
	local out_val = output
	mata: insert("quantile_90", `out_val', $r', "quantile_90")

	* Update the global row counter 
	global r = `r' + 1
}

* (e) generate stata variables from these stata matrix objects:
svmat double forecast, name(forecast)
svmat double upper_bound, name(upper_bound)
svmat double lower_bound, name(lower_bound)
svmat double quantile_10, name(quantile_10)
svmat double quantile_25, name(quantile_25)
svmat double quantile_50, name(quantile_50)
svmat double quantile_75, name(quantile_75)
svmat double quantile_90, name(quantile_90)

**********************
* VOLUME CONSOLIDATE *
**********************
* Important Note: need to globalize all parameters or else they will not be available in forvalues{}...
* (0) Determine the rank of the data-set. Record under the local macro size
sum(qdate)
* Note that local size = r(N) followed by global size = `size' will not work since you can't macro a macro.
global size = r(N)

* (2) Set column counter for variable names t+1
global N = 1

* (3) Count the rank of the t+1 matrix (same-prefix count of variables)
unab mvars : q10_r*
global count : word count `mvars'
* display `count'

* (1) Set row counter starting at the row containing the 1st out of sample forecast.
global r = $size - $count + 1

* (4) Create "holding matrices" for the outputs of the search-loop
* Note: these will eventually be the outputs that are rejoined to the original STATA data matrix
create_matrices, size($size)

* matrix list forecast

forvalues num = $N/$count {
	* (a) Declare matrix names for the N (t+1) forecast iterations of the vector subset 
	local conv_yhat Ly_fcprice_r`num'
	local conv_yhat_u Ly_fcprice_ru`num'
	local conv_yhat_l Ly_fcprice_rl`num'
	local q10_r Lq10_r`num'
	local q25_r Lq25_r`num'
	local q50_r Lq50_r`num'
	local q75_r Lq75_r`num'
	local q90_r Lq90_r`num'

	* (b) Assign STATA data to MATA-compatible matrices for each prefix N
	* note 1: the data is identified from the local macros containing variable names.
	* note 2: although conv_yhat is accessed with di "`conv_yhat'", mkmat takes `conv_yhat'
	/* DEPRECATED:
	mkmat `conv_yhat', matrix(forecast_`N')
	* Matrix list conv_yhat
	mkmat `conv_yhat_u', matrix(upper_bound_`N')
	mkmat `conv_yhat_l', matrix(lower_bound_`N')
	mkmat `q10_r', matrix(quantile_10_`N')
	mkmat `q25_r', matrix(quantile_25_`N')
	mkmat `q50_r', matrix(quantile_50_`N')
	mkmat `q75_r', matrix(quantile_75_`N')
	mkmat `q90_r', matrix(quantile_90_`N')
	*/

	* Assign the global variable to this local subroutine
	local r = $r
	/* (c) Identify the rth element of each of these MATA-compatible matrices. Assign this 
	element to the rth row in the appropriate "holding matrix". The scalar macro name
	can be override for each iteration N
	*/
	mata: fillmatrix("`conv_yhat'", $r)
	/* VERY IMPORTANT: Use the "=" operator to actually override out_val with output's value
	instead of making out_val a mirror-copy of output. */
	local out_val = output
	* (d) Update the "holding matrices":
	mata: insert("forecast", `out_val', $r, "forecast")
	* matrix list forecast

	mata: fillmatrix("`conv_yhat_u'", $r)
	local out_val = output
	mata: insert("upper_bound", `out_val', $r, "upper_bound")

	mata: fillmatrix("`conv_yhat_l'", $r)
	local out_val = output
	mata: insert("lower_bound", `out_val', $r, "lower_bound")

	mata: fillmatrix("`q10_r'", $r)
	local out_val = output
	mata: insert("quantile_10", `out_val', $r, "quantile_10")

	mata: fillmatrix("`q25_r'", $r)
	local out_val = output
	mata: insert("quantile_25", `out_val', $r, "quantile_25")

	mata: fillmatrix("`q50_r'", $r)
	local out_val = output
	mata: insert("quantile_50", `out_val', $r, "quantile_50")

	mata: fillmatrix("`q75_r'", $r)
	local out_val = output
	mata: insert("quantile_75", `out_val', $r, "quantile_75")

	mata: fillmatrix("`q90_r'", $r)
	local out_val = output
	mata: insert("quantile_90", `out_val', $r', "quantile_90")

	* Update the global row counter 
	global r = `r' + 1
}

* (e) generate stata variables from these stata matrix objects:
svmat double forecast, name(Lforecast)
svmat double upper_bound, name(Lupper_bound)
svmat double lower_bound, name(Llower_bound)
svmat double quantile_10, name(Lquantile_10)
svmat double quantile_25, name(Lquantile_25)
svmat double quantile_50, name(Lquantile_50)
svmat double quantile_75, name(Lquantile_75)
svmat double quantile_90, name(Lquantile_90)

* End Function
***************************************************************************

* Final Graphs:

*---------------------------
* GRAPH PRICE:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line price forecast1 upper_bound1 lower_bound1 qdate, ///
ylabel(1500(150)3000, gmax angle(horizontal)) ///
tlabel(2013m6(7)2017m3, format(%tm)) xtitle("Year/Month") ///
ytitle("LME Zinc Price") ///
title("LME Zinc Price") ///
subtitle("USA, 2013-2017") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "LME Zinc Price" 2 "1-Step-Ahead Forecast (SF)" 3 "U-Bound SF" 4 "L-Bound SF")) ///
lwidth(thick  medthick  thin thin ) ///
lpattern(solid solid dash dash) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH

*---------------------------
* GRAPH VOLUME:
local markdate1 = tm(2013m1)
local markdate2 = tm(2013m4)
local markdate3 = tm(2013m7)
local markdate4 = tm(2013m10)
local markdate5 = tm(2014m1)
local markdate6 = tm(2014m4)
local markdate7 = tm(2014m7)
local markdate8 = tm(2014m10)
local markdate9 = tm(2015m1)
local markdate10 = tm(2015m4)
local markdate11 = tm(2015m7)
local markdate12 = tm(2015m10)
local markdate13 = tm(2016m1)
local markdate14 = tm(2016m4)
local markdate15 = tm(2016m7)
local markdate16 = tm(2016m10)

line lme Lforecast1 Lupper_bound1 Llower_bound1 qdate, ///
ylabel(350000(100000)1100000, gmax angle(horizontal)) ///
tlabel(2013m6(7)2017m3, format(%tm)) xtitle("Year/Month") ///
ytitle("LME Inventory") ///
title("LME Inventory") ///
subtitle("USA, 2013-2017") ///
note("Source: Bloomberg, RS-Metrics") ///
legend( order(1 "LME Inventory" 2 "1-Step-Ahead Forecast (SF)" 3 "U-Bound SF" 4 "L-Bound SF")) ///
lwidth(thick  medthick  thin thin ) ///
lpattern(solid solid dash dash) ///
xline(`markdate1', lstyle(grid) lpattern(dash)) ///
xline(`markdate2', lstyle(grid) lpattern(dash)) ///
xline(`markdate3', lstyle(grid) lpattern(dash)) ///
xline(`markdate4', lstyle(grid) lpattern(dash)) ///
xline(`markdate5', lstyle(grid) lpattern(dash)) ///
xline(`markdate6', lstyle(grid) lpattern(dash)) ///
xline(`markdate7', lstyle(grid) lpattern(dash)) ///
xline(`markdate8', lstyle(grid) lpattern(dash)) ///
xline(`markdate9', lstyle(grid) lpattern(dash)) ///
xline(`markdate10', lstyle(grid) lpattern(dash)) ///
xline(`markdate11', lstyle(grid) lpattern(dash)) ///
xline(`markdate12', lstyle(grid) lpattern(dash)) ///
xline(`markdate13', lstyle(grid) lpattern(dash)) ///
xline(`markdate14', lstyle(grid) lpattern(dash)) ///
xline(`markdate15', lstyle(grid) lpattern(dash)) ///
xline(`markdate16', lstyle(grid) lpattern(dash))
* END GRAPH


***************************************************************************

* Long-term non-naive forecasts (3 Month Forecast)
tsappend, add(1)

arima qtr_price L3.qtr_aaggtot L4.qtr_aaggtot L5.qtr_aaggtot, hessian arima(0,1,1)
predict yhat_pr
gen r_yhat_pr = (1+yhat_pr)*price[_n-3]

* If the arima model doesn't fit at well, use AR noise as a predictor (ARCH):
arch qtr_lme L3.aaggtot, hessian narch(1)
predict yhat_in
gen r_yhat_in = (1+yhat_in)*lme[_n-3]

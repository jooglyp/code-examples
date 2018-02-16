
"""
Requirements:
(1) American Fact Finder ACS_2015_5YR_ZCTA.gdb (this is a 2015 ACS geodatabase)
ftp://ftp.census.gov/geo/tiger/TIGER_DP/2015ACS
(2) American Fact Finder ACS_15_5YR_S2301 (this is a census flatfile report S2301 for EMPLOYMENT STATUS (11'-15' ACS 5-YR)
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

# geodatabase and geography modules
import osgeo.gdal
osgeo.gdal.__version__  # need 1.9.2 or higher to open ESRI gdb (currently have 2.1.3)
from osgeo import ogr
import fiona
import geopandas as gpd

# ------------------------------------------------------
#################################################
### Directory Management and Model Parameters ###
#################################################

######################
### DATA DIRECTORY ###
######################
w_dir = r"<<ACS Spreadsheet Data Directory>>"
gis_dir = r"<<ACS GDB Directory>>"

s2301_dir = "<<ACS SPREADSHEET>>"
s2301 = "<<ACS GDB>>"

############################
### ZIP .SHP DECLARATION ###
############################

zip_shp = gpd.read_file(r'<<ACS GDB>>', driver='FileGDB')

############################
### GEODATABASE HANDLING ###
############################


age_sex_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X01_AGE_AND_SEX')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B01001e2 = age_sex_dbf[['GEOID', 'B01001e2']]
B01001e20 = age_sex_dbf[['GEOID', 'B01001e20']]
B01001e21 = age_sex_dbf[['GEOID', 'B01001e21']]
B01001e22 = age_sex_dbf[['GEOID','B01001e22']]
B01001e23 = age_sex_dbf[['GEOID', 'B01001e23']]
B01001e24 = age_sex_dbf[['GEOID', 'B01001e24']]
B01001e25 = age_sex_dbf[['GEOID', 'B01001e25']]
B01001e26 = age_sex_dbf[['GEOID', 'B01001e26']]
B01001e27 = age_sex_dbf[['GEOID', 'B01001e27']]
B01001e28 = age_sex_dbf[['GEOID', 'B01001e28']]
B01001e29 = age_sex_dbf[['GEOID', 'B01001e29']]
B01001e3 = age_sex_dbf[['GEOID', 'B01001e3']]
B01001e30 = age_sex_dbf[['GEOID', 'B01001e30']]
B01001e4 = age_sex_dbf[['GEOID', 'B01001e4']]
B01001e44 = age_sex_dbf[['GEOID', 'B01001e44']]
B01001e45 = age_sex_dbf[['GEOID', 'B01001e45']]
B01001e46 = age_sex_dbf[['GEOID', 'B01001e46']]
B01001e47 = age_sex_dbf[['GEOID', 'B01001e47']]
B01001e48 = age_sex_dbf[['GEOID', 'B01001e48']]
B01001e49 = age_sex_dbf[['GEOID', 'B01001e49']]
B01001e5 = age_sex_dbf[['GEOID', 'B01001e5']]
B01001e6 = age_sex_dbf[['GEOID', 'B01001e6']]
B01003e1 = age_sex_dbf[['GEOID', 'B01003e1']]
B01001e1 = age_sex_dbf[['GEOID', 'B01001e1']]

# clear memory
del age_sex_dbf
print "pass 1"

#----------------------------------------------------------------------------------------------

race_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X02_RACE')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B02001e2 = race_dbf[['GEOID', 'B02001e2']]
B02001e3 = race_dbf[['GEOID', 'B02001e3']]
B02001e4 = race_dbf[['GEOID', 'B02001e4']]
B02001e5 = race_dbf[['GEOID', 'B02001e5']]
B02001e6 = race_dbf[['GEOID', 'B02001e6']]
B02001e7 = race_dbf[['GEOID', 'B02001e7']]
B02001e8 = race_dbf[['GEOID', 'B02001e8']]

# clear memory
del race_dbf
print "pass 2"

#----------------------------------------------------------------------------------------------

hispanic_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X03_HISPANIC_OR_LATINO_ORIGIN')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B03003e3 = hispanic_dbf[['GEOID', 'B03003e3']]
B03003e1 = hispanic_dbf[['GEOID', 'B03003e1']]

# clear memory
del hispanic_dbf
print "pass 3"

#----------------------------------------------------------------------------------------------

income_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X19_INCOME')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B19301e1 = income_dbf[['GEOID', 'B19301e1']]

# clear memory
del income_dbf
print "pass 4"

#----------------------------------------------------------------------------------------------


commuting_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X08_COMMUTING')
#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B08014e1 = commuting_dbf[['GEOID', 'B08014e1']]
"""
B08014e10 = commuting_dbf[['GEOID', 'B08014e10']]   # male, 1 veh
B08014e11 = commuting_dbf[['GEOID', 'B08014e11']]   # male, 2 veh
B08014e17 = commuting_dbf[['GEOID', 'B08014e17']]   # female, 1 veh
B08014e18 = commuting_dbf[['GEOID', 'B08014e18']]   # female, 2 veh
"""
B08203e10 = commuting_dbf[['GEOID', 'B08203e10']]
B08203e13 = commuting_dbf[['GEOID', 'B08203e13']]
B08203e14 = commuting_dbf[['GEOID', 'B08203e14']]
B08203e16 = commuting_dbf[['GEOID', 'B08203e16']]
B08203e19 = commuting_dbf[['GEOID', 'B08203e19']]
B08203e20 = commuting_dbf[['GEOID', 'B08203e20']]
B08203e22 = commuting_dbf[['GEOID', 'B08203e22']]
B08203e25 = commuting_dbf[['GEOID', 'B08203e25']]
B08203e26 = commuting_dbf[['GEOID', 'B08203e26']]
B08203e7 = commuting_dbf[['GEOID', 'B08203e7']]
B08203e8 = commuting_dbf[['GEOID', 'B08203e8']]
B08203e28 = commuting_dbf[['GEOID', 'B08203e28']]

B08014e3 = commuting_dbf[['GEOID', 'B08014e3']] # census mislabeled. likely 1 vehicle available in general
B08014e4 = commuting_dbf[['GEOID', 'B08014e4']] # census mislabeled. likely 2 vehicles available in general


# clear memory
del commuting_dbf
print "pass 5"

#----------------------------------------------------------------------------------------------


families_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X11_HOUSEHOLD_FAMILY_SUBFAMILIES')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B11016e1 = families_dbf[['GEOID', 'B11016e1']]
B11016e10 = families_dbf[['GEOID', 'B11016e10']]
B11016e11 = families_dbf[['GEOID', 'B11016e11']]
B11016e12 = families_dbf[['GEOID', 'B11016e12']]
B11016e13 = families_dbf[['GEOID', 'B11016e13']]
B11016e14 = families_dbf[['GEOID', 'B11016e14']]
B11016e15 = families_dbf[['GEOID', 'B11016e15']]
B11016e16 = families_dbf[['GEOID', 'B11016e16']]
B11016e3 = families_dbf[['GEOID', 'B11016e3']]
B11016e4 = families_dbf[['GEOID', 'B11016e4']]
B11016e5 = families_dbf[['GEOID', 'B11016e5']]
B11016e6 = families_dbf[['GEOID', 'B11016e6']]
B11016e7 = families_dbf[['GEOID', 'B11016e7']]
B11016e8 = families_dbf[['GEOID', 'B11016e8']]
B11002e1 = families_dbf[['GEOID', 'B11002e1']]
B11002e2 = families_dbf[['GEOID', 'B11002e2']]

# clear memory
del families_dbf
print "pass 6"

#----------------------------------------------------------------------------------------------


education_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X15_EDUCATIONAL_ATTAINMENT')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B15003e1 = education_dbf[['GEOID', 'B15003e1']]
B15003e21 = education_dbf[['GEOID', 'B15003e21']]
B15003e17 = education_dbf[['GEOID', 'B15003e17']]
B15003e22 = education_dbf[['GEOID', 'B15003e22']]

# clear memory
del education_dbf
print "pass 7"

#----------------------------------------------------------------------------------------------


housing_dbf = gpd.read_file(r'<<ACS GDB>>', \
                                driver='FileGDB', layer= u'X25_HOUSING_CHARACTERISTICS')

#--------------------------#
#-- Attribute Extraction --#
#--------------------------#

B25009e1 = housing_dbf[['GEOID', 'B25009e1']]
B25009e13 = housing_dbf[['GEOID', 'B25009e13']]
B25009e14 = housing_dbf[['GEOID', 'B25009e14']]
B25009e15 = housing_dbf[['GEOID', 'B25009e15']]
B25009e16 = housing_dbf[['GEOID', 'B25009e16']]
B25009e17 = housing_dbf[['GEOID', 'B25009e17']]
B25009e5 = housing_dbf[['GEOID', 'B25009e5']]
B25009e6 = housing_dbf[['GEOID', 'B25009e6']]
B25009e7 = housing_dbf[['GEOID', 'B25009e7']]
B25009e8 = housing_dbf[['GEOID', 'B25009e8']]
B25009e9 = housing_dbf[['GEOID', 'B25009e9']]
B25010e1 = housing_dbf[['GEOID', 'B25010e1']]

# clear memory
del housing_dbf
print "pass 8"

# 3 gb of 16 gb used!

#--------------------------------------------

#########################
### FLATFILE HANDLING ###
#########################

emp_status_raw = pd.read_csv(os.path.join(s2301_dir, s2301))
# we need unemployment rate by zipcode (HC04_EST_VC01)

u_rate = emp_status_raw[['GEO.id', 'HC04_EST_VC01']][1:]

############################
### Attribute Extraction ###
############################

# (1) Persons 18 years and over, percent
var1 = ((B01001e2[B01001e2.columns[1]] - (B01001e3[B01001e3.columns[1]] + B01001e4[B01001e4.columns[1]] + \
        B01001e5[B01001e5.columns[1]] + B01001e6[B01001e6.columns[1]])) + (B01001e26[B01001e26.columns[1]] - \
        (B01001e27[B01001e27.columns[1]] + B01001e28[B01001e28.columns[1]] + B01001e29[B01001e29.columns[1]] + \
         B01001e30[B01001e30.columns[1]]))) / B01001e1[B01001e1.columns[1]]
var1_frame = var1.to_frame().rename(columns={0: 'Age_18_Plus'})
var1_tab = var1_frame.join(B01001e1[B01001e1.columns[0]])

# (2) Persons 65 years and over, percent
var2 = ((B01001e20[B01001e20.columns[1]] + B01001e21[B01001e21.columns[1]] + B01001e22[B01001e22.columns[1]] + \
        B01001e23[B01001e23.columns[1]] + B01001e24[B01001e24.columns[1]] + B01001e25[B01001e25.columns[1]]) + \
       (B01001e44[B01001e44.columns[1]] + B01001e45[B01001e45.columns[1]] + B01001e46[B01001e46.columns[1]] + \
        B01001e47[B01001e47.columns[1]] + B01001e48[B01001e48.columns[1]] + B01001e49[B01001e49.columns[1]])) \
       / B01001e1[B01001e1.columns[1]]
var2_frame = var2.to_frame().rename(columns={0: 'Age_65_Plus'})
var2_tab = var2_frame.join(B01001e1[B01001e1.columns[0]])

# (3) Persons under 18 years, percent
var3 = (B01001e3[B01001e3.columns[1]] + B01001e4[B01001e4.columns[1]] + \
        B01001e5[B01001e5.columns[1]] + B01001e6[B01001e6.columns[1]]) / B01001e1[B01001e1.columns[1]]
var3_frame = var3.to_frame().rename(columns={0: 'Age_Below_18'})
var3_tab = var3_frame.join(B01001e1[B01001e1.columns[0]])

# (4) Associate degree or higher, percent
var4 = B15003e21[B15003e21.columns[1]] / B15003e1[B15003e1.columns[1]]
var4_frame = var4.to_frame().rename(columns={0: 'Associate_Degree'})
var4_tab = var4_frame.join(B15003e1[B15003e1.columns[0]])

# (5) Average family size
var5 = B25010e1[B25010e1.columns[1]]
var5_frame = var5.to_frame().rename(columns={'B25010e1': 'Average_Family_Size'})    ### 0 column not default
var5_tab = var5_frame.join(B25010e1[B25010e1.columns[0]])

# (6) Bachelor's degree or higher, percent
var6 = B15003e22[B15003e22.columns[1]] / B15003e1[B15003e1.columns[1]]
var6_frame = var6.to_frame().rename(columns={0: 'Bachelors_Degree'})
var6_tab = var6_frame.join(B15003e1[B15003e1.columns[0]])

# (7) Family households
var7 = B11002e2[B11002e2.columns[1]]
var7_frame = var7.to_frame().rename(columns={'B11002e2': 'Family_Households'})           ### 0 column not default
var7_tab = var7_frame.join(B11002e2[B11002e2.columns[0]])

# (8) Female persons, percent
var8 = B01001e26[B01001e26.columns[1]] / B01001e1[B01001e1.columns[1]]
var8_frame = var8.to_frame().rename(columns={0: 'Female_Population'})
var8_tab = var8_frame.join(B01001e1[B01001e1.columns[0]])

# (9) High school graduate or higher, percent
var9 = B15003e17[B15003e17.columns[1]] / B15003e1[B15003e1.columns[1]]
var9_frame = var9.to_frame().rename(columns={0: 'High_Schl_Grad'})
var9_tab = var9_frame.join(B15003e1[B15003e1.columns[0]])

# (10) Households
var10 = B11002e1[B11002e1.columns[1]]
var10_frame = var10.to_frame().rename(columns={'B11002e1': 'Households'})       ### 0 column not default
var10_tab = var10_frame.join(B11002e1[B11002e1.columns[0]])

# (11) Male persons, percent
var11 = B01001e2[B01001e2.columns[1]] / B01001e1[B01001e1.columns[1]]
var11_frame = var11.to_frame().rename(columns={0: 'Male_Population'})
var11_tab = var11_frame.join(B01001e1[B01001e1.columns[0]])

# (12) Households having 1 vehicle, percent
var12 = B08014e3[B08014e3.columns[1]] / B08014e1[B08014e1.columns[1]]
var12_frame = var12.to_frame().rename(columns={0: 'PCT_1_Vehicle'})
var12_tab = var12_frame.join(B08014e1[B08014e1.columns[0]])

# (13) Households having 2 vehicles, percent
var13 = B08014e4[B08014e4.columns[1]] / B08014e1[B08014e1.columns[1]]
var13_frame = var13.to_frame().rename(columns={0: 'PCT_2_Vehicles'})
var13_tab = var13_frame.join(B08014e1[B08014e1.columns[0]])

# (14) Unemployment rate, percent
var14 = u_rate.copy()
var14_tab = var14.rename(columns = {'GEO.id': 'GEOID', 'HC04_EST_VC01': 'PCTCivilian_Unemp'})

# (15) Households having more than 2 vehicles, percent
var15 =  (B08203e10[B08203e10.columns[1]] + B08203e16[B08203e16.columns[1]] + B08203e22[B08203e22.columns[1]] + \
          B08203e28[B08203e28.columns[1]]) / (B08203e7[B08203e7.columns[1]] + B08203e13[B08203e13.columns[1]] + \
          B08203e19[B08203e19.columns[1]] + B08203e25[B08203e25.columns[1]])
var15_frame = var15.to_frame().rename(columns={0: 'PCTMore_2_Vehicles'})
var15_tab = var15_frame.join(B08203e25[B08203e25.columns[0]])

# (16) Households having no vehicles, percent
var16 =  (B08203e8[B08203e8.columns[1]] + B08203e14[B08203e14.columns[1]] + B08203e20[B08203e20.columns[1]] + \
          B08203e26[B08203e26.columns[1]]) / (B08203e7[B08203e7.columns[1]] + B08203e13[B08203e13.columns[1]] + \
          B08203e19[B08203e19.columns[1]] + B08203e25[B08203e25.columns[1]])
var16_frame = var16.to_frame().rename(columns={0: 'PCTNo_Vehicle'})
var16_tab = var16_frame.join(B08203e25[B08203e25.columns[0]])

# (17) Per Capita income
var17 = B19301e1[B19301e1.columns[1]]
var17_frame = var17.to_frame().rename(columns={'B19301e1': 'Per_Capita_Income'})         ### 0 column not default
var17_tab = var17_frame.join(B19301e1[B19301e1.columns[0]])

# (18) Population
var18 = B01001e1[B01001e1.columns[1]]
var18_frame = var18.to_frame().rename(columns={'B01001e1': 'Population'})                ### 0 column not default
var18_tab = var18_frame.join(B01001e1[B01001e1.columns[0]])

# (19) Population density, per square mile (calculated field)
us_albers_equal_area = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"
zip_shp_cpy = zip_shp.copy()
zip_shp_cpy.to_crs(us_albers_equal_area, inplace=True)    # currently in NAD83 (epsg 4269)
zip_shp_cpy["area"] = zip_shp_cpy['geometry'].area/ 10**6   # square km
# join population data to zipcode
zip_shp_cpy = zip_shp_cpy.set_index('GEOID_Data').join(B01001e1.set_index('GEOID'))
var19 = zip_shp_cpy["B01001e1"] / zip_shp_cpy["area"]
var19_frame = var19.to_frame().rename(columns={0: 'Population_Density'})
var19_frame.reset_index(inplace=True)
var19_frame = var19_frame.rename(columns={"GEOID_Data": 'GEOID'})
var19_tab = var19_frame.copy()
del zip_shp_cpy

# (20) Households with more than 2 people, percent
var20 = ((B11016e4[B11016e4.columns[1]] + B11016e5[B11016e5.columns[1]] + \
        B11016e6[B11016e6.columns[1]] + B11016e7[B11016e7.columns[1]] + B11016e8[B11016e8.columns[1]]) + \
        (B11016e12[B11016e12.columns[1]] + B11016e13[B11016e13.columns[1]] + B11016e14[B11016e14.columns[1]] + \
         B11016e15[B11016e15.columns[1]] + B11016e16[B11016e16.columns[1]])) / B11016e1[B11016e1.columns[1]]
var20_frame = var20.to_frame().rename(columns={0: 'MT2PPHousehold_2Plus'})
var20_tab = var20_frame.join(B11016e1[B11016e1.columns[0]])

# (21) American-Indian population, percent
var21 = B02001e4[B02001e4.columns[1]] / B01003e1[B01003e1.columns[1]]
var21_frame = var21.to_frame().rename(columns={0: 'PCTAIANPop'})
var21_tab = var21_frame.join(B01003e1[B01003e1.columns[0]])

# (22) Asian population, percent
var22 = B02001e5[B02001e5.columns[1]] / B01003e1[B01003e1.columns[1]]
var22_frame = var22.to_frame().rename(columns={0: 'PCTAPop'})
var22_tab = var22_frame.join(B01003e1[B01003e1.columns[0]])

# (23) Black population, percent
var23 = B02001e3[B02001e3.columns[1]] / B01003e1[B01003e1.columns[1]]
var23_frame = var23.to_frame().rename(columns={0: 'PCTBPop'})
var23_tab = var23_frame.join(B01003e1[B01003e1.columns[0]])

# (24) Hispanic population, percent
var24 = B03003e3[B03003e3.columns[1]] / B03003e1[B03003e1.columns[1]]
var24_frame = var24.to_frame().rename(columns={0: 'PCTHisPop'})
var24_tab = var24_frame.join(B03003e1[B03003e1.columns[0]])

# (25) Hawaiian and Pacific Islander population, percent]
var25 = B02001e6[B02001e6.columns[1]] / B01003e1[B01003e1.columns[1]]
var25_frame = var25.to_frame().rename(columns={0: 'PCTHPIPop'})
var25_tab = var25_frame.join(B01003e1[B01003e1.columns[0]])

# (26) Minority (non-white) population, percent
var26 = 1 - (B02001e2[B02001e2.columns[1]] / B01003e1[B01003e1.columns[1]])
var26_frame = var26.to_frame().rename(columns={0: 'PCTMinority'})
var26_tab = var26_frame.join(B01003e1[B01003e1.columns[0]])

# (27) Multirace population, percent
var27 = B02001e8[B02001e8.columns[1]] / B01003e1[B01003e1.columns[1]]
var27_frame = var27.to_frame().rename(columns={0: 'PCTMultiracePop'})
var27_tab = var27_frame.join(B01003e1[B01003e1.columns[0]])

# (28) Other race population, percent
var28 = B02001e7[B02001e7.columns[1]] / B01003e1[B01003e1.columns[1]]
var28_frame = var28.to_frame().rename(columns={0: 'PCTOtherRacePop'})
var28_tab = var28_frame.join(B01003e1[B01003e1.columns[0]])

# (29) White population, percent
var29 = B02001e2[B02001e2.columns[1]] / B01003e1[B01003e1.columns[1]]
var29_frame = var29.to_frame().rename(columns={0: 'PCTWhitePop'})
var29_tab = var29_frame.join(B01003e1[B01003e1.columns[0]])

# (30) Households with 1 person, percent
var30 = B11016e10[B11016e10.columns[1]] / B11016e1[B11016e1.columns[1]]
var30_frame = var30.to_frame().rename(columns={0: 'PPHouseholds_1'})
var30_tab = var30_frame.join(B11016e1[B11016e1.columns[0]])

# (31) Households with 2 persons, percent
var31 = (B11016e3[B11016e3.columns[1]] + B11016e11[B11016e11.columns[1]]) / B11016e1[B11016e1.columns[1]]
var31_frame = var31.to_frame().rename(columns={0: 'PPHouseholds_2'})
var31_tab = var31_frame.join(B11016e1[B11016e1.columns[0]])

#--------------------------------------------
###############################
### Zipcode File Generation ###
###############################

zip_shp_cpy = zip_shp.copy()
# join all attributes on GEOID
zip_shp_cpy = zip_shp_cpy.set_index('GEOID_Data').join(var1_tab.set_index('GEOID')) # this takes up var1_tab

"""
# generate list consisting of varXX_tab from 2 to 31
# use eval(string variable name) to recall the actual df object for the underlying string variable name
zip_shp_cpy = zip_shp_cpy.join(var2_tab.set_index('GEOID'))
"""

gen_exp = ("var"+str(n)+"_tab" for n in range(2,31))

def gen_zip_data(zip_shp_cpy, gen_exp):
    for exp in gen_exp:
        zip_shp_cpy = zip_shp_cpy.join(eval(exp).set_index('GEOID'))
        yield zip_shp_cpy

g = gen_zip_data(zip_shp_cpy, gen_exp)  # this takes up var2_tab

for n in range(3,32):
    gen_zip_data(zip_shp_cpy, gen_exp)
    element = next(g, None)
    print n

print element

# Write-out
out_dir = os.path.join(w_dir, "Dems.shp")
element.to_file(out_dir)
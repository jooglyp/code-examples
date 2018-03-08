"""
Purpose:
This script instantiates a weekly retail points file (derived from an intersection of satellite imagery with 
a population points file. It is assumed that all input files for initialization, sub-methods, methods, and general
methods all sit within the same directory. Here is the general structure of this class:

class(0: sample points file)

__init__:
    a) RSM regions file
    b) subsetted hex(shp) - optional
    c) population retail points
    d) satellite imagery strips
    e) output directory
    
I. Methods I. (hybrid sub): req. 0, a
    -> sub routines
    -> suboption method: quadrantize()
    -> main method: create_hex_grid()
    # returns a self.hex(shp): 1

II. Methods II. (hybrid sub): req. 0, 1/b, c 
# this set of methods must return a hotspot hex grid, point-scores, point-multipliers, and point-classifiers
    -> sub routines
    -> main method: create_scores()
    # returns a self.hexscores(shp) and self.points(shp): 2

III. Methods III. req. 2, d
    -> sub routines
    -> main method: create_aois()
    # returns a self.aois(shp): 3

IV. General Method. req. 1/2/3
    -> main method: export_shp()
    # ejects all self.xxx(shp) objects to a .shp file in output directory
"""

#---------------------------------------------
######################
### MODULE IMPORTS ###
######################

import sys
#---#
# 64bit anaconda architecture:
sys.path.append(r"C:\Anaconda2_64bit")
sys.path.append(r"C:\Anaconda2_64bit\Scripts")
sys.path.append(r"C:\Anaconda2_64bit\Library\bin")
sys.path.append(r"C:\Anaconda2_64bit\Lib\site-packages")
#---#
import os
import pandas as pd
import geopandas as gpd
import pysal
from pysal.esda.getisord import G_Local
import shapely
from shapely import speedups
from shapely.geometry import Polygon, Point, box, asPolygon, asPoint, MultiPoint, shape, base
import shapefile
import math
import numpy as np
from numpy.lib.recfunctions import append_fields
import re
import time
import jenkspy

# ignore numpy floating point errors
np.seterr(all='ignore')

#---------------------------------------------
#########################
### MODULE INITIATION ###
#########################

print "How to Use:"
print "Instantiate a global retail points file with class stores_to_aoi(Working Directory, Shape File Name.shp)"
print "--------------------------------------------------------------------------------------------------------"
print "The following files must be located in the same working directory:"
print "1) RSM Regions (shape file)"
print "2) Satellite Imagery (shape file)"
print "3) Full Retailer Distribution (shape file)"
print "--------------------------------------------------------------------------------------------------------"
print "Working Directory Example: 'C:/Folder/'"
print "Shape File Name Example: 'shapefile.shp'"
print "--------------------------------------------------------------------------------------------------------"

#---------------------------------------------
class StoreToAOI:

    """
    Instantiation Notes:
    sample_points is a file path directory (it is identified in a super-module).
    sample_points is a shapefile.
    """

    ##############################################################
    # Initialization                                             #
    ##############################################################
    def __init__(self, cd, sample_points):

        """
        a) RSM regions file
        b) subsetted hex(shp) - optional
        c) population retail points
        d) satellite imagery strips
        e) output directory
        """

        # Designate commonly used projection systems as class attributes:
        self.us_albers_equal_area_prj = 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID\
        ["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],\
        PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],\
        PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]'

        self.wgs84_prj = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'

        self.us_albers_equal_area = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"

        self.wgs84 = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

        # 0: make sample_points an attribute as well:
        self.cd = cd
        self.sample_points = os.path.join(self.cd, sample_points)

        # e: output folder. If none exists, create one
        ocd = "Output"
        if not os.path.exists(os.path.join(self.cd, ocd)):
            os.makedirs(os.path.join(self.cd, ocd))
        self.output_dir = os.path.join(self.cd, ocd)

        # a: RSM regions file is assumed to be named RSM_Regions.shp
        reg_name_shp = "RSM_Regions.shp"
        self.rsm_regions = os.path.join(self.cd, reg_name_shp)

        # b: subsetted hex file is assumed to follow a consistent prefix naming convention, "Hex"
        prefix_hex = "Hex"
        # loop through directory and identify all shapefiles with "prefix" and ending .shp
        try:
            self.hex_list = {s: None for s in os.listdir(self.cd) if s.startswith(prefix_hex) and s.endswith(".shp")}
        except:
            self.hex_list = {}

        # c: Population retail points is assumed to be named Retailers.shp
        retail_file = "Retailers.shp"
        self.population_points = os.path.join(self.cd, retail_file)

        # d: Satellite imagery strips are assumed to follow a consistent prefix naming convention, "Imagery_Final"
        prefix_imagery = "Imagery_Final"
        self.in_imagery = [i for i in os.listdir(self.cd) if i.startswith(prefix_imagery) and i.endswith(".shp")][0]
        self.in_imagery = os.path.join(self.cd, self.in_imagery)

    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#

    def min_threshold_dist_from_points(self, in_geodataframe, radius=None, p=2):
        """
        Source Code:
        http://pysal.readthedocs.io/en/latest/_modules/pysal/weights/Distance.html
        
        MODIFIED VERSION OF 'pysal.min_threshold_dist_from_shapefile'
        NOW TAKES GEODATAFRAME INSTEAD OF SHAPEFILE
        ----------
        Kernel weights with adaptive bandwidths.
        Parameters
        ----------
        shapefile  : string
                    shapefile name with shp suffix.
        radius     : float
                    If supplied arc_distances will be calculated
                    based on the given radius. p will be ignored.
        p          : float
                    Minkowski p-norm distance metric parameter:
                    1<=p<=infinity
                    2: Euclidean distance
                    1: Manhattan distance
        Returns
        -------
        d          : float
                    Maximum nearest neighbor distance between the n
                    observations.
        """
        points = np.vstack([np.array(shape.centroid) for shape in in_geodataframe['geometry']])
        if radius is not None:
            kdt = pysal.cg.kdtree.Arc_KDTree(points, radius=radius)
            nn = kdt.query(kdt.data, k=2)
            nnd = nn[0].max(axis=0)[1]
            return nnd
        return pysal.weights.min_threshold_distance(points, p)

    ##################
    ### Methods I. ###
    ##################

    #---------------------#
    ### Sub Routines I. ###
    #---------------------#

    def calculate_polygons(self, startx, starty, endx, endy, radius):
        """ 
        Calculate a grid of hexagon coordinates of the given radius
        given lower-left and upper-right coordinates 
        Returns a list of lists containing 6 tuples of x, y point coordinates
        These can be used to construct valid regular hexagonal polygons
    
        You will probably want to use projected coordinates for this
        """
        # calculate side length given radius
        sl = (2 * radius) * math.tan(math.pi / 6)
        # calculate radius for a given side-length
        # (a * (math.cos(math.pi / 6) / math.sin(math.pi / 6)) / 2)
        # see http://www.calculatorsoup.com/calculators/geometry-plane/polygon.php

        # calculate coordinates of the hexagon points
        # sin(30)
        p = sl * 0.5
        b = sl * math.cos(math.radians(30))
        w = b * 2
        h = 2 * sl

        # offset start and end coordinates by hex widths and heights to guarantee coverage
        startx = startx - w
        starty = starty - h
        endx = endx + w
        endy = endy + h

        origx = startx
        origy = starty

        # offsets for moving along and up rows
        xoffset = b
        yoffset = 3 * p

        polygons = []
        row = 1
        counter = 0

        while starty < endy:
            if row % 2 == 0:
                startx = origx + xoffset
            else:
                startx = origx
            while startx < endx:
                p1x = startx
                p1y = starty + p
                p2x = startx
                p2y = starty + (3 * p)
                p3x = startx + b
                p3y = starty + h
                p4x = startx + w
                p4y = starty + (3 * p)
                p5x = startx + w
                p5y = starty + p
                p6x = startx + b
                p6y = starty
                poly = [
                    [p1x, p1y],
                    [p2x, p2y],
                    [p3x, p3y],
                    [p4x, p4y],
                    [p5x, p5y],
                    [p6x, p6y],
                    [p1x, p1y]]
                polygons.append(poly)
                counter += 1
                startx += w
            starty += yoffset
            row += 1
        return polygons

    #------------------------------#

    def geoms_to_hex_shp(self, in_geoms, out_shp, projection):
        # algorithm pulled from here:
        # https://github.com/DigitalGlobe/gbdxtools/blob/master/gbdxtools/catalog_search_aoi.py

        prj_name = '{}.prj'.format(out_shp.split('.')[0])
        with open(prj_name, 'w') as prj:
            prj.write(projection)
        shp_writer = shapefile.Writer(shapefile.POLYGON)

        """
        Errata:
        shp_writer.field('FIRST_FLD','C','40')
        shp_writer.field('SECOND_FLD','C','40')
        shp_writer.record('First','Polygon')
        shp_writer.save(grid_out)
        """

        out_fields = [
            ['id', 'N']
        ]
        out_fields_names = [x[0] for x in out_fields]
        for name in out_fields:
            shp_writer.field(*name)

        for in_id, geom in enumerate(in_geoms, start=1):
            shp_writer.record(*[str(in_id)])
            shp_writer.poly(parts=[geom])
        shp_writer.save(out_shp)

    #------------------------------#

    def quadrantize(self, minx, miny, maxx, maxy):
        from shapely.geometry import LineString

        """
        :param w: the minx of a bounding box
        :param s: the miny of a bounding box
        :param e: the maxx of a bounding box
        :param n: the maxy of a bounding box
        :return: 4 subdivisions of a super-bounding box
        """

        # declare the bounding-division dictionary:
        SubBoxes = {}

        half_x = LineString([(minx, miny), (maxx, miny)]).centroid.x
        half_y = LineString([(minx, miny), (minx, maxy)]).centroid.y
        box1 = box(minx, miny, half_x, half_y)
        box2 = box(half_x, miny, maxx, half_y)
        box3 = box(minx, half_y, half_x, maxy)
        box4 = box(half_x, half_y, maxx, maxy)

        # append to dictionary
        SubBoxes["b1"] = box1  # quadrant 3
        SubBoxes["b2"] = box2  # quadrant 1
        SubBoxes["b3"] = box3  # quadrant 2
        SubBoxes["b4"] = box4  # quadrant 4

        return SubBoxes

    #------------------------------#

    def create_subpoints(self):
        """
        Inputs:
        1) self.rsm_regions
        2) self.sample_points
        :return: spatial join of RSM regions to retail points
        """
        # create gdf's
        sub_gdf = gpd.GeoDataFrame.from_file(self.sample_points)
        if sub_gdf.crs != self.us_albers_equal_area:
            sub_gdf.to_crs(self.us_albers_equal_area, inplace=True)
        rsm_regions_gdf = gpd.GeoDataFrame.from_file(self.rsm_regions)
        if rsm_regions_gdf.crs != self.us_albers_equal_area:
            rsm_regions_gdf.to_crs(self.us_albers_equal_area, inplace=True)
        sample_regions = gpd.sjoin(sub_gdf, rsm_regions_gdf, how='left')
        self.sample_regions = sample_regions

    #------------------------------#

    #---------------------#
    ### Main Routine I. ###
    #---------------------#

    def create_hex_grid(self, hex_area):
        """
        :inputs:
        1) self.cd
        2) self.sample_points
        3) self.rsm_regions
        :return: a gdb of hex
        """

        hex_region_field = 'NAME'
        # hex_area = 86602540.378  # 86602540.378 is the area of a hexagon with radius = 5000 meters

        #---------------------------------------------
        ## Grid Creation ##

        # For each gdf in self.sample_points_region, determine the bounding box extent, and generate a hex grid
        all_bboxes = self.sample_regions.groupby(hex_region_field)['geometry'].agg(lambda g: g.total_bounds)
        for b in all_bboxes.iteritems():
            name = b[0]
            print name
            geom = b[1]
            geom_box = box(*geom)
            extent_area = geom_box.area

            if extent_area < hex_area:  # 86602540.378 is the area of a hexagon with radius = 5000 meters
                # begin rescaling the extent_area
                # (1) The following condition, box(a,b,c,d).area/box(w,s,e,n).area = xfact*yfact.
                # (2) want to know --> (86602540.378*1.1)/box(w,s,e,n).area --> sqrt(*)
                req_growth = (hex_area * 1.1) / extent_area
                scale_factor = req_growth ** 0.5
                nshp_bounds = shapely.affinity.scale(geom_box, xfact=scale_factor, yfact=scale_factor).bounds
                # obtain new bounds
                geom = nshp_bounds

            # # # Create the fishnet # # #
            w, s, e, n = geom
            vertices = self.calculate_polygons(w, s, e, n, 5000)    # 5000 meter radius (UTM)

            # Create the hex geodataframe
            v_dict = {ndx: Polygon(v) for ndx, v in enumerate(vertices)}
            hex_gdf = gpd.GeoDataFrame.from_dict({'geometry': v_dict})
            hex_gdf.crs = self.sample_regions.crs
            hex_gdf = hex_gdf.reset_index().rename(columns={'index': 'polyid'})

            # store in a zipped list (file_name will keep track of which hex-region is being stored)
            self.hex_list[name] = hex_gdf
            # write hex to shapefile for debugging
            # self.geoms_to_hex_shp([list(s.exterior.coords) for s in hex_gdf['geometry'].tolist()], '{}.shp'.format(name), self.us_albers_equal_area_prj)

    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#

    ###################
    ### Methods II. ###
    ###################

    """
    Notes on design:
    The purpose of splitting the main routines in Methods II. into 3 separate main methods is to compartmentalize
    and separate different high-intensity computational activities. Data classification for instance is computationally
    heavy with large n. Separating field generation into separate tasks in less cumbersome on memory usage.
    """

    #----------------------#
    ### Sub Routines II. ###
    #----------------------#

    # Nothing here... yet

    #-----------------------#
    ### Main Routine IIa. ###
    #-----------------------#

    def create_scores_OLD(self):
        """
        inputs:
        1) the list of hex grid gdb's (by RSM region)
        2) the list of sample point gdb's (by RSM region) - must run self.create_subpoints() to generate this object
        :return: a hex grid with z-scores and heat-scores stored in self.OutputDict
        """
        #-----------------------------#
        ## CREATE DICTIONARY ##

        self.OutputDict = {}

        #-----------------------------#
        ## SPATIAL JOINS ##

        # (1) Need to first obtain the aggregate footprint across all tickers in the sample!
        # Important: it is assumed that this point file is in AEA
        all_tickers_gdf = gpd.GeoDataFrame.from_file(self.sample_points)
        ticker_total = all_tickers_gdf.groupby(['Ticker']).size()

        """
        # retrieve the proj4 information for this layer:
        dataset = driver.Open(all_tickers_dir)
        layer = dataset.GetLayer()
        spatialRef = layer.GetSpatialRef()
        proj4_points = spatialRef.ExportToProj4()
        """

        # (2) Need to secondly obtain the aggregate footprint across all tickers in the known population!
        # Important: it is assumed that this point file is in WGS 1984
        # old_crs is automatically detected
        pop_tickers_gdf = gpd.read_file(self.population_points)
        # the first argument in .to_crs() could also be: gdf.to_crs(crs={'init' :'esri:102003'})
        # pop_tickers_gdf.to_crs(all_tickers_gdf.crs, inplace=True)
        if pop_tickers_gdf.crs != self.us_albers_equal_area:
            pop_tickers_gdf.to_crs(self.us_albers_equal_area, inplace=True)
        pop_ticker_total = pop_tickers_gdf.groupby(['Ticker']).size()

        # Loop over all elements in sub_files_points and sub_files_grid, which should be in alphabetical order:
        for region, grid_gdf in self.hex_list.iteritems():
            point = self.sample_regions[self.sample_regions['NAME'] == region].copy()
            poly = grid_gdf.copy()
            # use the reset-index on poly since id contains missing elements (they were ocean tiles):
            # rename index:
            # poly_ix = poly.reset_index()
            # poly_ix['polyid'] = .rename(columns={'index': 'polyid'})

            ##################
            #POPULATION JOINS#
            """
            Population Tickers - Select by Hex Subset:
            Analyst sample retail locations subset --> hex subset --> select by location the retail store population.
        
            Motivation: want to get aggregate counts of the population across grid subsets
            """
            # conduct a spatial join, with population points as targets:
            pop_pointInPolys = gpd.sjoin(pop_tickers_gdf, poly, how='left')
            # Get a pivot table (population):
            pop_pointSumByPoly = pop_pointInPolys.groupby(['polyid', 'Ticker']).size()
            # Transform to functional pd df (recast the "sized" column to 'total')
            pop_pointSumByPolyG = pd.DataFrame({'total': pop_pointSumByPoly}).reset_index()
            # pivot this table from long to wide on 'Ticker'
            pop_pivotG = pop_pointSumByPolyG.pivot(index='polyid', columns='Ticker', values='total')
            ##################
            point.drop('index_right', axis=1, inplace=True)
            ##################
            #SAMPLE JOINS#
            # conduct the spatial joins, with points as targets:
            pointInPolys = gpd.sjoin(point, poly, how='left')
            # note that polyid is equivalent to index_right from the sjoin

            # Get a pivot table (sample):
            pointSumByPoly = pointInPolys.groupby(['polyid', 'Ticker']).size()
            # Transform to functional pd df (recast the "sized" column to 'total')
            pointSumByPolyG = pd.DataFrame({'total': pointSumByPoly}).reset_index()
            # pivot this table from long to wide on 'Ticker'
            pivotG = pointSumByPolyG.pivot(index='polyid', columns='Ticker', values='total')
            ##################

            # re-index the pivot table so that 'polyid' is full-rank:
            # (a) create the range df:
            poly_rix = poly['polyid']
            # (b) reindex using poly_rix as the full range of possible polyid's
            pivotG_full = pivotG.reindex(poly_rix)
            # (c) replace NaN's with zeros
            pivotG_full = pivotG_full.fillna(0)

            #--#
            # Repeat reindexing for the population points
            # (b) reindex using poly_rix as the full range of possible polyid's
            pop_pivotG_full = pop_pivotG.reindex(poly_rix)
            # (c) replace NaN's with zeros
            pop_pivotG_full = pop_pivotG_full.fillna(0)

            #------------------------------------------------------------------------------------------------
            ####################
            ## Y VECTOR SCORE ##
            ####################

            # Create heat-scores vector
            # 1) take the row totals for each ticker in pivotG_full
            # Deprecated during grid segementation: pivotTot = pivotG_full.sum(numeric_only=True)

            # 2) for each row element, divide the ticker quantity by this row total
            # preallocate the output matrix space
            pivotRatios = pd.DataFrame(columns=pivotG_full.columns, index=np.arange(0, len(pivotG_full)))
            # don't do this as it will result in integer format (need float) pivotRatios = pivotRatios.fillna(0)
            # begin populating. This will take a long time.

            for index, row in pivotG_full.iterrows():
                for ticker, value in pivotG_full.iteritems():
                    # obtain the row total from pivotTot for this particular ticker
                    rowTot = ticker_total[ticker]
                    # obtain the row value for this particular ticker
                    tickerVal = pivotG_full[ticker][index]
                    # obtain the store count ratio
                    tickerRowRatio = tickerVal / rowTot

                    # now, for something a little different: obtain information from the population
                    pop_rowTot = pop_ticker_total[ticker]
                    pop_tickerVal = pop_pivotG_full[ticker][index]
                    pop_tickerRowRatio = pop_tickerVal / pop_rowTot
                    """
                    Sample Weight Logic (The Importance Quotient):
                    - We want to give bonuses to grid element tickerRowRatios that are smaller than the a-priori
                     known population tickerRowRatios.
                    - Method: divide the sample grid element's tickerRowRatio by that grid element's population
                    tickerRow Ratio
                    - Result: if 1/10 Dick's sporting goods are observed in hex 1 but we know that hex 1 contains 5/10
                    of Dick's sporting goods in reality, then we want to derive a weight that indicates that this hex
                    undersampled Dick's. Therefore (1/10)/(5/10) = 1/5.
                    """
                    # populate the n*m element of pivotRatios with the "importance quotient"
                    #### IMPORTANT: Check what this is as just tickerRowRatio, N/A values should not exist in this vector
                    # pivotRatios.loc[index][ticker] = tickerRowRatio / pop_tickerRowRatio
                    quotient = abs((abs(tickerRowRatio) - abs(pop_tickerRowRatio)) / abs(pop_tickerRowRatio))
                    if math.isnan(quotient) == False:
                        pivotRatios.set_value(index, ticker, quotient)
                    else:
                        pivotRatios.set_value(index, ticker, 0)

            # 3) for each row element, take the exponentiated sum of column elements
            pivotRatios["sum"] = pivotRatios.sum(axis=1)
            pivotRatios["exp"] = np.exp(pivotRatios["sum"])

            # 4) declare a new matrix that is just this exponentiated sum over all row elements of pivotG_full (just copy)
            heat_scores = pivotRatios.filter(['exp'], axis=1)   # note that this score is >= 1

            #------------------------------------------------------------------------------------------------
            ####################
            ## GRID S WEIGHTS ##
            ####################

            # Important: Class functions in pysal are at odds with classes in qgis-core. DO NOT do this in qgis-core
            grid_thresh = self.min_threshold_dist_from_points(poly)
            # the spatial weights matrix will yield greater agglomerations as the parameter on grid_thresh increases
            w = pysal.weights.DistanceBand.from_dataframe(poly, threshold=grid_thresh*3.0, alpha=-2.0, binary=False)
            w.transform = "R"   # row standardized weights (see pysal handbook pg. 171)

            # GETIS-ORD Z STATISTIC:
            heat_scores_array = heat_scores.values.ravel()
            # G() will only accept a flattened 1-D array. .Ravel() transforms a dictionary data-structure to np-array [x]
            # G(i): g = G_Local(heat_scores_array, w, transform='R')
            g = G_Local(heat_scores_array, w, transform='R', star=True)
            # Important Note: Large dimensions of w as args to G() will yield a MemoryError during processing.
            # Solution: will need to process the national footprint's w and heat_score matrices in segments!

            # Append the z-scores and heat_scores back to poly
            poly["Z_Scores"] = g.z_sim
            poly["Heat_Scores"] = heat_scores_array
            # Assign this iteration of g and heat_scores to the Outputs dictionary
            self.OutputDict[region] = g, heat_scores, poly

            """
            Inspect the CRS of the layers:
        
            driver = ogr.GetDriverByName('ESRI Shapefile')
            all_tickers_dataset = driver.Open(all_tickers_dir)
            layer_all_tickers = all_tickers_dataset.GetLayer()
            spatialRef_all_tickers = layer_all_tickers.GetSpatialRef()
            spatialRef_all_tickers.ExportToProj4()
        
            grid_dataset = driver.Open(grid_dir)
            layer_grid = grid_dataset.GetLayer()
            spatialRef_grid = layer_grid.GetSpatialRef()
            spatialRef_grid.ExportToProj4()
        
            stores_dataset = driver.Open(stores_dir)
            layer_stores = stores_dataset.GetLayer()
            spatialRef_stores = layer_stores.GetSpatialRef()
            spatialRef_stores.ExportToProj4()
            """

    #------------------------------------------------------------------------------------------------
    def min_distance_dirt(self, dataframe):

        # SOME SUBSET OF TICKERS
        sub_gdf = dataframe['geometry'].copy()
        out_distances = []
        for ndx_1, geom_1 in sub_gdf.iteritems():
            for ndx_2, geom_2 in sub_gdf.iteritems():
                dist = geom_1.distance(geom_2)
                out_distances.append(dist)
        max_dist = max(out_distances)
        return max_dist

    #------------------------------------------------------------------------------------------------

    def create_scores(self):
        """
        inputs:
        1) the population of retail points
        2) the list of sample point gdb's (by RSM region) - must run self.create_subpoints() to generate this object
        :return: a hex grid with z-scores and heat-scores stored in self.OutputDict
        """
        #-----------------------------#
        ## CREATE DICTIONARY ##

        self.OutputDict = {}

        #-----------------------------#
        ## SPATIAL JOINS ##

        # (1) Need to first obtain the aggregate footprint across all tickers in the sample!
        # Important: it is assumed that this point file is in AEA
        all_tickers_gdf = gpd.GeoDataFrame.from_file(self.sample_points)
        ticker_total = all_tickers_gdf.groupby(['Ticker']).size()   # the total over the non-region subset sample
        sample_PointSum = pd.DataFrame({'total': ticker_total}).reset_index()

        """
        # retrieve the proj4 information for this layer:
        dataset = driver.Open(all_tickers_dir)
        layer = dataset.GetLayer()
        spatialRef = layer.GetSpatialRef()
        proj4_points = spatialRef.ExportToProj4()
        """

        # (2) Need to secondly obtain the aggregate footprint across all tickers in the known population!
        # Important: it is assumed that this point file is in WGS 1984
        # old_crs is automatically detected
        pop_tickers_gdf = gpd.read_file(self.population_points)
        # the first argument in .to_crs() could also be: gdf.to_crs(crs={'init' :'esri:102003'})
        # pop_tickers_gdf.to_crs(all_tickers_gdf.crs, inplace=True)
        if pop_tickers_gdf.crs != self.us_albers_equal_area:
            pop_tickers_gdf.to_crs(self.us_albers_equal_area, inplace=True)
        pop_ticker_total = pop_tickers_gdf.groupby(['Ticker']).size()

        ####################
        # POPULATION SCORING#
        """
        Motivation: want to get aggregate counts of the population across grid subsets
        """
        # Transform to functional pd df (recast the "sized" column to 'total')
        pop_pointSum = pd.DataFrame({'total': pop_ticker_total}).reset_index()
        ##################

        # identify all unique regions in self.sample_regions
        s_regions = self.sample_regions['NAME'].unique()

        # Loop over all elements in sub_files_points, which should be in alphabetical order:
        for region in s_regions:
            point = self.sample_regions[self.sample_regions['NAME'] == region].copy()
            point.drop('index_right', axis=1, inplace=True)
            ##################

            ##################
            # SAMPLE JOINS#

            """
            Consideration: PY-CY Match Rate
                - The current sample points region subset needs to be further subsetted by PY/CY (under 'YEAR').
                - for each storeID, we want to see how many 1:1 matches there are between PY/CY
                - for each 1:1 match of 'YEAR'[0] and 'YEAR'[1], we will use this count, INSTEAD OF THE ABSOLUTE
                COUNT OF POINTS FOR THIS TICKER (WHICH INCLUDES ALL CY + PY TICKERS), AS A NUMERATOR MULTIPLIER
                TO THE TOTAL COUNT!

            Example: WMT has 500 stores let's say nation-wide. Therefore, the sample ticker-row-ratio will 
            be nominally 1/500. Hence, the more stores nationwide - the less salient of an importance score that
            ticker will have.
            """
            # Derive the sample's py-cy match rate
            point_cy = point[point['YEAR'] == 'CurrentYear']
            point_py = point[point['YEAR'] == 'PriorYear']
            # derive pivot tables with ticker as the row index
            point_cy_sum = point_cy.groupby(['Ticker']).size()
            point_cy_sumG = pd.DataFrame({'total': point_cy_sum}).reset_index()
            point_py_sum = point_py.groupby(['Ticker']).size()
            point_py_sumG = pd.DataFrame({'total': point_py_sum}).reset_index()

            # Get a pivot table (sample):
            pointSum = point.groupby(['Ticker']).size()
            # Transform to functional pd df (recast the "sized" column to 'total')
            pointSumG = pd.DataFrame({'total': pointSum}).reset_index()
            ##################

            # ------------------------------------------------------------------------------------------------
            ####################
            ## Y VECTOR SCORE ##
            ####################

            # Create heat-scores vector
            # 1) take the row totals for each ticker in pivotG
            # 2) for each row element, divide the ticker quantity by this row total
            # preallocate the output matrix space
            pivotRatios = pd.DataFrame(columns=pointSumG.columns, index=np.arange(0, len(pointSumG)))

            for index, row in pointSumG.iterrows():
                # obtain the row total from the sample for this particular ticker
                rowTot = row['total']
                # obtain the store count ratio
                regs_tickerRowRatio = 1 / float(rowTot)
                # obtain the ticker for population total lookup purposes
                ticker = row.Ticker
                sample_tickerRowRatio = 1/ float(sample_PointSum[sample_PointSum['Ticker'] == ticker]['total'].values[0])

                # Now, for something a little different: obtain information from the population
                pop_rowTot = pop_pointSum[pop_pointSum['Ticker'] == ticker]['total'].values[0]
                pop_tickerRowRatio = 1 / float(pop_rowTot)

                # PY-CY match rate information
                try:
                    cy_rowTot = point_cy_sumG[point_cy_sumG['Ticker'] == ticker]['total'].values[0]
                except:
                    print "The ticker: %s contains no CurrentYear data" % (ticker)
                    cy_rowTot = 1
                try:
                    py_rowTot = point_py_sumG[point_py_sumG['Ticker'] == ticker]['total'].values[0]
                except:
                    print "The ticker: %s contains no PriorYear data" % (ticker)
                    py_rowTot = 1
                # identify number of matches for this particular ticker over the py-cy span:
                if cy_rowTot == 0:
                    cy_rowTot = 1
                else:
                    pass
                if py_rowTot < cy_rowTot:
                    match_r = min(py_rowTot, cy_rowTot)
                    # calculate the match-rate statistic
                    ln_match_r = math.log(2 + float(rowTot / match_r))
                else:
                    ln_match_r = math.log(2 + float(rowTot / cy_rowTot))

                """
                Sample Weight Logic (The Importance Quotient):
                - We want to give bonuses to grid element tickerRowRatios that are smaller than the a-priori
                known population tickerRowRatios.
                - Method: divide the sample grid element's tickerRowRatio by that grid element's population
                tickerRow Ratio
                - Result: if 10 Dick's sporting goods are observed in sample but we know that 20
                of Dick's sporting goods in reality, then we want to derive a weight that that expresses how under
                or oversampled Dick's is. By using a quotient (see below), this weight can vary anywhere from 0 to
                infinity.

                Application of CY-PY Match-Weight:
                - we may want to apply an upward weight to a number between 0 and 1 or from 1 to infinity. 
                This would be a multiplicative weight. This weight is based off of the number of matches (py) to
                the number of cy observations for a given ticker.
                - If we express this premium being equal to Ln(2 + (total ticker count / # py-cy matches of ticker)),
                where the matches of the ticker is always less than the total ticker count, then we will achieve
                a number that is greater than 1 and therefore applies a percentage premium off of the original number
                to the quotient.
                """
                # populate the n*m element of pivotRatios with the "importance quotient"
                #### IMPORTANT: Check what this is as just tickerRowRatio, N/A values should not exist in this vector
                # pivotRatios.loc[index][ticker] = tickerRowRatio / pop_tickerRowRatio
                try:
                    quotient = abs((abs(regs_tickerRowRatio) - abs(pop_tickerRowRatio)) / (abs(sample_tickerRowRatio) - \
                                                                                           abs(pop_tickerRowRatio)))
                    quotient = quotient * ln_match_r  # ln_match_r is > 1, and likely less than 4
                    # on except, the denominator is likely 0
                except:
                    quotient = np.nan

                pivotRatios.set_value(index, 'total', quotient)
                pivotRatios.set_value(index, 'Ticker', ticker)
                """
                DEPRECATED:
                if math.isnan(quotient) == False:
                    pivotRatios.set_value(index, 'total', quotient)
                    pivotRatios.set_value(index, 'Ticker', ticker)
                else:
                    pivotRatios.set_value(index, 'total', 0)
                    pivotRatios.set_value(index, 'Ticker', ticker)
                """
            for index, row in pivotRatios.iterrows():
                ticker = row.Ticker
                total = row.total
                if math.isnan(total) == False:
                    pivotRatios.set_value(index, 'total', total)
                    pivotRatios.set_value(index, 'Ticker', ticker)
                else:
                    pivotRatios.set_value(index, 'total', max(pivotRatios.total))
                    pivotRatios.set_value(index, 'Ticker', ticker)

            # 3) for each row element, take the exponentiation of the quotient
            pivotRatios = pivotRatios.rename(columns={'total': 'quotient'})

            # 4) for each point in the original sample file, append a quotient value based on the ticker
            point["quotient"] = np.nan
            for i, row in point.iterrows():
                c_region = row['Ticker']
                v_quotient = pivotRatios[pivotRatios['Ticker']==c_region]['quotient'].values[0]
                point.set_value(i, 'quotient', v_quotient)

            #------------------------------------------------------------------------------------------------
            ####################
            ## GRID S WEIGHTS ##
            ####################

            # Important: Class functions in pysal are at odds with classes in qgis-core. DO NOT do this in qgis-core
            if len(point) < 200:
                grid_thresh = self.min_distance_dirt(point)
            else:
                grid_thresh = self.min_threshold_dist_from_points(point)
            # the spatial weights matrix will yield greater agglomerations as the parameter on grid_thresh increases
            point = point.reset_index()
            w = pysal.weights.DistanceBand.from_dataframe(point, threshold=grid_thresh, alpha=-1.5, binary=False)
            w.transform = "R"   # row standardized weights (see pysal handbook pg. 171)

            # GETIS-ORD Z STATISTIC:
            heat_scores_array = point.filter(['quotient'], axis=1)   # note that this score is >= 1
            # G() will only accept a flattened 1-D array. .Ravel() transforms a dictionary data-structure to np-array [x]
            # G(i): g = G_Local(heat_scores_array, w, transform='R')
            g = G_Local(heat_scores_array, w, transform='R', star=True)
            # Important Note: Large dimensions of w as args to G() will yield a MemoryError during processing.
            # Solution: will need to process the national footprint's w and heat_score matrices in segments!

            # Append the z-scores and heat_scores back to point
            point["Z_Scores"] = g.z_sim
            point["Heat_Scores"] = heat_scores_array
            # Assign this iteration of g and heat_scores to the Outputs dictionary
            self.OutputDict[region] = g, heat_scores_array, point


        ###########################################
        ## G Score Visualization and Aggregation ##
        ###########################################

        """
        Attributes of the g object in OutputDict are documented in the pysal developer's handbook:
        pg. 165 (161 page mark)
        We are interested in the attribute ".z_sim"
        """

        """
        Plot the gdf attributes:
        
        test = OutputDict['Tickers_Points_Sub_East'][2]
        # using gdf
        test_dir = os.path.join(cd, "test_star_east.shp")
        test.to_file(test_dir)
        # open in qgis and begin classifying
        
        test = OutputDict['Tickers_Points_Sub_West'][2]
        # using gdf
        test_dir = os.path.join(cd, "test_star_west.shp")
        test.to_file(test_dir)
        # open in qgis and begin classifying
        
        test = OutputDict['Tickers_Points_Sub_Central'][2]
        # using gdf
        test_dir = os.path.join(cd, "test_star_central.shp")
        test.to_file(test_dir)
        # open in qgis and begin classifying
        """

    #--------------------------------------------------------------------------------------------------------#
    #-----------------------#
    ### Main Routine IIb. ###
    #-----------------------#

    def append_classify_scores(self):
        """
        Usage: must be run after scores have been created. Will take each point file that was produced and
        stored in OutputDict and append to those tables a natural jenks bin classification to the z-scores vector.
        :return: A bin classification field to the hex elements of self.OutputDict[key]
        """
        # (1) Identify all dictionary names in self.OutputDict
        dict_names = [title for title in self.OutputDict.keys()]

        # (2) Loop through self.OutputDict gdb's
        for n, akey in enumerate(dict_names):
            sub_gdf = self.OutputDict[akey][2]
            # Obtain the vector of z scores
            z_scores = sub_gdf['Z_Scores']
            # ----------------------------------#
            # (3) Apply natural jenks (takes about 10 minutes per z-score vector)

            # Applying Jenks Algorithm:

            # create a np structured array object of the z-scores - to be used in getJenksBreaks()
            np_z_scores = np.array([z_scores[e] for e in range(0, len(z_scores))], dtype=[('z_scores', float)])
            # convert the structured array to a sparse np array
            to_class = np_z_scores.astype(np.float)
            # run jenks
            var_jenks = jenkspy.jenks_breaks(to_class, nb_class=7)
            # obtain the jenk breaks in list format. Delete duplicates (this occurs if there isn't enough variety)
            breaks = list(set([round(i, 1) for i in var_jenks]))
            """
            getJenksBreaks() does not handle values under 0. But this isn't an issue: z-scores below 0 are clearly
            cold zones. The first element of breaks should be the minimum observed z-score
            """
            breaks[0] = min(sub_gdf['Z_Scores'])
            """
            during rounding, getJenksBreaks() will inadvertently create an upper bin that might be a fraction smaller than
            the max Z_Score in sub_gdf. Therefore buffer that value by +1.
            """
            breaks[len(breaks) - 1] = max(sub_gdf['Z_Scores']) + 1

            # Append back-to sub_gdf designating the z-score's bin:
            # (a) declare the output classifier bin. Declare as numpy structured array
            class_bin = np.array([], dtype=np.dtype(np_z_scores.dtype))
            for index in range(len(z_scores)):
                # Resize schema to its full rank before performing match/fills
                class_bin.resize(class_bin.shape[0] + 1, refcheck=False)  # Add 1 null tuple-space ()
            # create a new column in class_bin
            new_col = np.array([], dtype=float)
            # append this new column to the original schema
            class_bin = append_fields(class_bin, 'z_bin', new_col, usemask=False, asrecarray=True)

            # (b) perform classifier matching
            for index in range(len(sub_gdf)):
                # Determine the z-score value for this variable
                obsvalue = sub_gdf['Z_Scores'][index]
                # for each observation in sub_gdf, determine bin, and append data
                # Determine this index observation's bin using if statements
                for j in range(1, len(breaks)):
                    if obsvalue <= breaks[j]:
                        if obsvalue >= breaks[j - 1]:
                            obsbin = breaks[j]
                # replace the null value in [index][bin_name] with the appropriate bin
                class_bin[index]['z_bin'] = obsbin
                class_bin[index]['z_scores'] = obsvalue

            # (c) append z_bin in class_bin back to sub_gdf
            sub_gdf['z_bin'] = class_bin['z_bin']
            # to inspect the histogram frequencies: sub_gdf_c.groupby('z_bin').size()


    #--------------------------------------------------------------------------------------------------------#
    #-----------------------#
    ### Main Routine IIc. ###
    #-----------------------#

    def create_seeds_OLD(self):
        """
        Usage: must be run after scores have been created at the hex grid level. The point file associated with each
        region-hex grid will be spatially joined with that hex grid. The resulting output has a multiplier calculation
        performed against it. The resulting field, "multiplier" will be appended to the spatially joined point file and
        used as an input to the AOI_growth work.
        :return: A multiplier field to a spatially joined point file (regional hex & regional points) in a dictionary 
        named "Growth_Seeds"
        """
        # Recall: The keys to regional hexes use title conventions from 'NAME' (RSM regions). self.OutputDict[regions][2]
        # Recall: The keys to point files use these same conventions. self.sample_points_region[regions, selection]

        # Initiate a holding dictionary:
        self.Growth_Seeds = {}

        # Identify the keys:
        dict_names = [title for title in self.OutputDict.keys()]

        # Loop through the sample points and the hex files
        for region, value in self.OutputDict.iteritems():
            region_hex_layer = self.OutputDict[region][2]
            region_point_layer = self.sample_regions[self.sample_regions['NAME'] == region].copy()
            ### SAMPLE JOINS###
            # conduct the spatial joins, with points as targets:
            region_point_layer.drop('index_right', axis=1, inplace=True)
            pointInPolys = gpd.sjoin(region_point_layer, region_hex_layer, how='left')
            # clean up any duplicate indices (there may be 1-2 of these for some reason!)
            pointInPolys['index'] = pointInPolys.index
            points_sjoin = pointInPolys.drop_duplicates(subset='index', keep='last')

            # drop all observations where index_right = NaN
            points_subdf = points_sjoin[np.isfinite(points_sjoin['index'])]
            # ------------------------------#
            # (2) Attribute the output spatial join with a multiplier column that is equal to the inverse of a groupby count
            s_ticker_totals = 1.0 / points_subdf.groupby(['Ticker']).size()
            # add a column to points_subdf for the multiplier
            """
            Logic: Hexagon-based agglomeration scoring leads to too much local homogeneity at the hex level. 
            Heterogenize by using store-specific bonuses.
            """
            points_subdf['multiplier'] = np.nan
            # loop through points_subdf
            for index, row in points_subdf.iterrows():
                # identify the current ticker
                c_ticker = row['Ticker'].encode('utf-8')
                # lookup the inverse count of this ticker in s_ticker_totals
                inv_count = s_ticker_totals[c_ticker]
                # attribute this count to the multiplier field
                points_subdf.loc[index, 'multiplier'] = inv_count

            self.Growth_Seeds[region] = points_subdf


    def create_seeds(self):
        """
        Usage: must be run after scores have been created at the hex grid level. The point file associated with each
        region-hex grid will be spatially joined with that hex grid. The resulting output has a multiplier calculation
        performed against it. The resulting field, "multiplier" will be appended to the spatially joined point file and
        used as an input to the AOI_growth work.
        :return: A multiplier field to a spatially joined point file (regional hex & regional points) in a dictionary 
        named "Growth_Seeds"
        """
        # Recall: The keys to regional hexes use title conventions from 'NAME' (RSM regions). self.OutputDict[regions][2]
        # Recall: The keys to point files use these same conventions. self.sample_points_region[regions, selection]

        # Initiate a holding dictionary:
        self.Growth_Seeds = {}

        # Identify the keys:
        dict_names = [title for title in self.OutputDict.keys()]

        # Loop through the sample points and the hex files
        for region, value in self.OutputDict.iteritems():
            region_point_layer = value[2]
            ### SAMPLE JOINS###
            # conduct the spatial joins, with points as targets:
            try:
                pointInPolys = region_point_layer.drop('index_righ', axis=1)
            except:
                pointInPolys = region_point_layer
            # clean up any duplicate indices (there may be 1-2 of these for some reason!)
            pointInPolys['index'] = pointInPolys.index
            points_sjoin = pointInPolys.drop_duplicates(subset='index', keep='last')
            self.test = points_sjoin
            # drop all observations where index_right = NaN
            points_subdf = points_sjoin[np.isfinite(points_sjoin['index'])]
            # ------------------------------#
            # (2) Attribute the output spatial join with a multiplier column that is equal to the inverse of a groupby count
            s_ticker_totals = 1.0 / points_subdf.groupby(['Ticker']).size()
            # add a column to points_subdf for the multiplier
            """
            Logic: Hexagon-based agglomeration scoring leads to too much local homogeneity at the hex level. 
            Heterogenize by using store-specific bonuses.
            """
            points_subdf['multiplier'] = np.nan
            # loop through points_subdf
            for index, row in points_subdf.iterrows():
                # identify the current ticker
                c_ticker = row['Ticker'].encode('utf-8')
                # lookup the inverse count of this ticker in s_ticker_totals
                inv_count = s_ticker_totals[c_ticker]
                # attribute this count to the multiplier field
                points_subdf.loc[index, 'multiplier'] = inv_count

            self.Growth_Seeds[region] = points_subdf


    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#

    ####################
    ### Methods III. ###
    ####################

    #-----------------------#
    ### Sub Routines III. ###
    #-----------------------#

    def geom_multi_to_single(self, in_geom):
        """
        Takes a Shapely polygon and converts multi-part polygons to single-part
        Returns a list of all parts of the polygon that was the input
        """
        if in_geom.type == 'MultiPolygon':
            out_geoms = [Polygon(p.exterior) for p in in_geom]
        elif in_geom.type == 'GeometryCollection':
            out_geoms = [Polygon(p.exterior) for p in in_geom if p.type == 'Polygon']
        elif in_geom.type == 'Polygon':
            out_geoms = [Polygon(in_geom.exterior)]
        return out_geoms

    #------------------------------#

    def clip_to_imagery(self, input_geoseries, imagery_geodataframe):
        """
        Clips input polygons to matching image based on ID
        Returns a GeoSeries
        """
        out_dict = {}
        for x, v in input_geoseries.iteritems():
            out_dict[x] = v.intersection(imagery_geodataframe[x])
        return gpd.GeoSeries(out_dict, crs=input_geoseries.crs)

    #------------------------------#

    def prep_geometries(self, input_geodataframe, imagery_geodataframe, simp_tol=None):
        """
        Unions all geometries together within intersecting imagery
        Clips unions to respective imagery
        Explodes multipart polygons to single part
        Convert modified geometries back to GeoDataFrame
        Appends area field
        """
        union = input_geodataframe.groupby('ALL_IMAGE')['geometry'].agg(shapely.ops.unary_union)
        union_geoseries = gpd.GeoSeries(union, crs=input_geodataframe.crs)
        union_clipped = self.clip_to_imagery(union_geoseries, imagery_geodataframe)
        polys_singlepart = union_clipped.explode()
        polys_single_gdf = gpd.GeoDataFrame(polys_singlepart.to_frame().reset_index(), crs=input_geodataframe.crs)
        polys_single_gdf.columns = ['ALL_IMAGE', 'AREA', 'geometry']
        if simp_tol:
            polys_single_gdf['geometry'] = polys_single_gdf['geometry'].map(lambda g: Polygon(g.exterior).simplify(simp_tol))
        else:
            polys_single_gdf['geometry'] = polys_single_gdf['geometry'].map(lambda g: Polygon(g.exterior))
        polys_single_gdf['AREA'] = polys_single_gdf['geometry'].area
        return polys_single_gdf

    #------------------------------#

    #--------------------------------------------------------------------------------------------------------#

    #-----------------------#
    ### Main Routine III. ###
    #-----------------------#

    def create_aois(self):
        """
        Usage:
        # imagery is accessible here: self.in_imagery
        # retail points with growth factors are accessible here: self.Growth_Seeds[region]
        region = [RSM West, RSM East, RSM Center, Alaska, Hawaii]; whatever is in 'NAME' of RSM Regions
        :return: a shapefile in the working directory 
        """

        if speedups.available:
            speedups.enable()
        start = time.time()

        """
        PROCESS:
            - Buffers points into unioned AOIs
            - First AOI to reach area limit is most important AOI based on buffer rate
            - More important AOIs saved to output shapefile before less important AOIs
            - Attempts to avoid ordering more imagery than needed by minimizing space in AOIs
            - Stops writing to output shapefile once AOI count is reached
    
        KNOWN BUGS:
            - None currently
        """

        #--SETTINGS----------------------------
        in_directory = self.cd
        # Use convex hull in place of buffer for polygons that are mostly empty area
        empty_area_max_ratio = 0.5  # percentage
        # Buffers at a rate of 1 meter to 100 meters based on "Buffer_Score"
        # Adjust higher for faster buffering - adjust lower for more accurate buffering
        buffer_meters_start = 1
        # Buffering stops after exceeding this variable
        area_max_limit = 28  # square kilometers
        area_min_limit = 6  # square kilometers
        # Max AOIs to keep
        # AOI accumulation will stop once it hits aoi limit or no AOIs remain
        aoi_limit = 2500
        #--------------------------------------
        # DATA PREP

        # Load data into geodataframe and project to US_Albers_Equal_Area
        in_gdf = pd.concat([gdf for gdf in self.Growth_Seeds.itervalues()], ignore_index=True)
        in_gdf = gpd.GeoDataFrame(in_gdf, crs=self.Growth_Seeds[self.Growth_Seeds.keys()[0]].crs)
        out_prj = '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs'
        in_gdf.to_crs(out_prj, inplace=True)

        # Load imagery into geodataframe
        imagery_gdf = gpd.GeoDataFrame.from_file(self.in_imagery)
        # Assign Image ID to index for quick lookup later
        imagery_lookup_gdf = imagery_gdf.set_index('ALL_IMAGE', drop=True, verify_integrity=True)
        # Subset imagery geodataframe to only contain Image ID and geometry
        imagery_gdf = imagery_gdf[['ALL_IMAGE', 'geometry']].copy()
        out_prj = '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs'
        imagery_gdf.to_crs(out_prj, inplace=True)
        # Only keep imagery that intersects retail locations
        imagery_gdf = imagery_gdf[imagery_gdf.intersects(in_gdf.unary_union)].copy()
        imagery = imagery_gdf.set_index('ALL_IMAGE', drop=True, verify_integrity=True).squeeze()

        # Calculate score from Z_Scores and multiplier
        score = in_gdf.apply(lambda row: row['Z_Scores'] * (1 + row['multiplier']), axis=1)
        # Add new field to geodataframe - interpolates score to percentage of 1% to 100%
        # This is the growth rate of the polygons
        in_gdf['Buffer_Score'] = np.interp(score.as_matrix(), [score.min(), score.max()], [1, 100])

        #--------------------------------------
        # MAIN

        """
        Reduction_gdf keeps track of all retail points that have yet to be buffered. It slowly gets truncated over time.
        It is cloned as pre_reduction_gdf (based on polys_single_gdf).
        """
        reduction_gdf = in_gdf[['Store_OID', 'ALL_IMAGE', 'Buffer_Score', 'geometry']].copy()
        # Union of original points before buffering - used to check intersections
        org_union = reduction_gdf.unary_union
        # Buffer that helps determine 'empty space' in polygons
        org_buffer = org_union.buffer(1400)
        # Function to convert Square Meters to Square Kilometers
        m_to_km = lambda p: p.area / 1000000
        # Function to convert Square Kilometers to Square Meters
        km_to_m = lambda p: p.area * 1000000
        # Initialize output geodataframe
        output_gdf = gpd.GeoDataFrame(crs=reduction_gdf.crs)
        # Used to break from loop once aoi limit is reached
        continue_loop = True
        aoi_count = 0
        while aoi_count < aoi_limit:
            if not reduction_gdf.empty:
                # Copy of data from previous trial if not first trial
                """
                Important: pre_reduction_gdf is the updated holding file for growing shapefiles
                """
                try:
                    pre_reduction_gdf = polys_single_gdf.copy()
                except NameError:
                    pre_reduction_gdf = gpd.GeoDataFrame()
                # Buffers geometry by buffer_meters_start * Buffer_Score
                buffer_func = lambda row: row['geometry'].buffer(buffer_meters_start * row['Buffer_Score']).simplify(0.5)
                reduction_gdf['geometry'] = reduction_gdf.apply(buffer_func, axis=1)
                # Union by aggregating all polygons within same image
                polys_single_gdf = self.prep_geometries(reduction_gdf, imagery, simp_tol=20)
                selection_func = lambda p: p / 1000000 > area_max_limit
                # Select all AOIs over area limit
                output_poly_gdf = polys_single_gdf[polys_single_gdf['AREA'].map(selection_func)].copy()
                # -------------------------------------
                if not output_poly_gdf.empty:
                    # Sort with largest AOIs first
                    output_poly_gdf.sort_values('AREA', ascending=False, inplace=True)
                    for primary_ndx, primary_row in output_poly_gdf.iterrows():
                        if continue_loop:
                            # Drop primary AOI from union
                            polys_single_gdf.drop(primary_ndx, inplace=True)
                            # Select from polygons from previous trial that intersects oversized AOI and is within the same imagery strip
                            # This should be the 'pre-overbuffered' AOIs that make up the oversized AOI
                            # e.g. if a large AOI is made of 3 smaller AOIs that buffer and union together - this returns those 3 parts
                            """
                            primary_row: the polygon that is oversized.
                            pre_reduction_gdf: satellite-confined buffered polygons from a previous iteration
                            """
                            primary_intersect_gdf = pre_reduction_gdf[
                                (pre_reduction_gdf.intersects(primary_row['geometry'])) & (
                                pre_reduction_gdf['ALL_IMAGE'] == primary_row['ALL_IMAGE'])].copy()
                            if not primary_intersect_gdf.empty:
                                # Sorts 'pre-overbuffered' AOIs with largest first
                                primary_intersect_gdf.sort_values('AREA', ascending=False, inplace=True)
                                # Appends all but largest AOI back to the dataset that still needs to continue growing (buffering)
                                """
                                polys_single_gdf: in iterations 1+, this is a copy of pre_reduction_gdf!
                                Important: all minor components go into the growth file. The largest component of primary_intersect_gdf
                                may get clipped by other polygons and be cut into segments.
                                """
                                polys_single_gdf = polys_single_gdf.append(primary_intersect_gdf.iloc[1:])
                                # Selects only largest AOI from 'pre-overbuffered' AOIs
                                polys_sorted_un_1 = gpd.GeoSeries(primary_intersect_gdf.iloc[0], crs=reduction_gdf.crs)
                                # If AOI is not the first AOI saved (no polygons in output to compare against first AOI)
                                if 'geometry' in output_gdf.columns and polys_sorted_un_1['ALL_IMAGE'] in output_gdf[
                                    'ALL_IMAGE'].unique():
                                    """
                                    If this is NOT the very first polygon being added to the output AND this polygon is in the same
                                    image as another polygon that is already in the output data. Note the output data gets refreshed
                                    after every iteration regardless of whether or not a threshold has been met. So we are really
                                    identifying the overgrown polygon against the universe of lower-growth polygons from a previous
                                    iteration.
                                    """
                                    # Union all geometries in saved output within same image - used to prevent buffering into already saved polygons
                                    """
                                    Using the largetest piece of the oversized polygon, intersect this with any geometry in a merged
                                    version of the output file.
                                    Any remaining geometry will become an AOI.
                                    """
                                    keep_union = output_gdf.groupby('ALL_IMAGE')['geometry'].agg(shapely.ops.unary_union)
                                    """
                                    Important: this clips current overgrown polygon against the merged growth shapefile. There's a
                                    possibility that a polygon might grow over the unioned main shapefile. That main shapefile would
                                    cut this polygon in half.
                                    """
                                    keep_un_poly = keep_union[polys_sorted_un_1['ALL_IMAGE']].buffer(0.1)
                                    keep_union[polys_sorted_un_1['ALL_IMAGE']] = keep_un_poly
                                    polys_sorted_un_1['geometry'] = polys_sorted_un_1['geometry'].difference(keep_un_poly)
                                    out_polys = gpd.GeoDataFrame(polys_sorted_un_1.to_frame().T, crs=reduction_gdf.crs)
                                else:
                                    keep_union = gpd.GeoSeries()
                                    out_polys = gpd.GeoDataFrame(polys_sorted_un_1.to_frame().T, crs=reduction_gdf.crs)
                                for out_ndx, out_row in out_polys.iterrows():
                                    # If polygon is multi-polygon - return largest single-part
                                    if out_row['geometry'].type == 'MultiPolygon':
                                        out_row_geom = [g for g in out_row['geometry'] if g.intersects(org_union)]
                                        if out_row_geom:
                                            out_row['geometry'] = out_row_geom[0]
                                        else:
                                            continue
                                    # Determines how much empty space is in output polygon - if empty space exceeds ratio then use a convex hull instead of buffered area
                                    empty_area_ratio = out_row['geometry'].difference(org_buffer).area / out_row['geometry'].area
                                    if empty_area_ratio < empty_area_max_ratio:
                                        # Select from starting dataset where AOI intersects and is in same image
                                        """
                                        out_row: an element of a multipolygon - also the largest polygon element of the overssized poly's members.
                                        reduction_gdf: the union of original retail locations
                                        """
                                        geom_intersect = reduction_gdf[(reduction_gdf.buffer(-10).intersects(out_row['geometry'])) & (
                                        reduction_gdf['ALL_IMAGE'] == out_row['ALL_IMAGE'])]
                                        output_gdf.set_value(aoi_count, 'AOI', aoi_count)
                                        output_gdf.set_value(aoi_count, 'ALL_IMAGE', out_row['ALL_IMAGE'])
                                        output_gdf.set_value(aoi_count, 'TYPE', 'FULL_POLY')
                                        output_gdf.set_value(aoi_count, 'geometry', out_row['geometry'])
                                        # Delete AOI from starting dataset
                                        reduction_gdf.drop(geom_intersect.index, inplace=True)
                                        aoi_count += 1
                                        print 'AOI Count: {}'.format(aoi_count)
                                        # Break from AOI creation if AOI limit reached
                                        if aoi_count == aoi_limit:
                                            continue_loop = False
                                            break
                                    else:
                                        # If too much 'empty space' in AOI:
                                        # If not first trial - no polygons in output file yet
                                        if not keep_union.empty:
                                            keep_un_geom = keep_union[out_row['ALL_IMAGE']]
                                        else:
                                            keep_un_geom = Polygon()
                                        hull_buffer = 1400  # starting buffer in meters for convex hull creation
                                        """
                                        Important:
                                        This process creates a convex hull. This hull could be cut in half by the growth shapefile,
                                        which creates a multipolygon.
                                        """
                                        out_poly_hull = org_union.intersection(out_row['geometry']).buffer(
                                            hull_buffer).convex_hull. \
                                            simplify(20).difference(keep_un_geom).intersection(imagery[out_row['ALL_IMAGE']])
                                        # If convex hull is < area_min_limit - buffer by 100m repeatedly until area_min_limit is reached
                                        hull_area = m_to_km(out_poly_hull)
                                        hull_start = 100
                                        while hull_area < area_min_limit:
                                            # This creates a convex hull as opposed to unary union + dissolve. See line 177
                                            """
                                            PROCESS:
                                            - Select original points that intersect AOI
                                            - Buffer to starting area - will be at least 6km2 if not clipped in any way
                                            - Created a convex hull of new polygons and simplify it
                                            - Difference it against polygons within same image that are already saved to output file to avoid overlap
                                            - Intersection it to associated image to avoid having polygon exist outside of image
                                            """
                                            out_poly_hull = org_union.intersection(out_row['geometry']).buffer(
                                                hull_buffer + hull_start).convex_hull. \
                                                simplify(20).difference(keep_un_geom).intersection(
                                                imagery[out_row['ALL_IMAGE']])
                                            hull_area = m_to_km(out_poly_hull)
                                            hull_start += 100
                                        # Convert possible multi-part polygons in convex hull to single-part
                                        """
                                        It's possible that convex hull may be a multipolygon. To handle this we turn the multipolygon
                                        into a single polygon. This pol
                                        """
                                        out_convex = self.geom_multi_to_single(out_poly_hull)
                                        for oc in out_convex:
                                            # Select from starting dataset where AOI intersects and is in same image
                                            """
                                            reduction_gdf: a layer of growth polygons in shapefiles. It will be truncated over time.
                                            """
                                            geom_intersect = reduction_gdf[(reduction_gdf.buffer(-10).intersects(oc)) & (
                                            reduction_gdf['ALL_IMAGE'] == out_row['ALL_IMAGE'])]
                                            """
                                            The following saves possible segements of the convex hull (oc in out_convex) to output_gdf, the shapefile that takes
                                            finishers of reduction_gdf in-growth.
                                            """
                                            output_gdf.set_value(aoi_count, 'AOI', aoi_count)
                                            output_gdf.set_value(aoi_count, 'ALL_IMAGE', out_row['ALL_IMAGE'])
                                            output_gdf.set_value(aoi_count, 'TYPE', 'CONVEX_HULL')
                                            output_gdf.set_value(aoi_count, 'geometry', oc)
                                            # Delete AOI from starting dataset
                                            reduction_gdf.drop(geom_intersect.index, inplace=True)
                                            aoi_count += 1
                                            print 'AOI Count: {}'.format(aoi_count)
                                            # Break from AOI creation if AOI limit reached
                                            if aoi_count == aoi_limit:
                                                continue_loop = False
                                                break
                            else:
                                raise Exception('Unexpected Empty GeoDataFrame')
            else:
                print '-No AOIs Remaining-'
                break

        # Add area field to output file
        output_gdf['AREA'] = output_gdf['geometry'].map(lambda geom: m_to_km(geom))
        # Append all imagery fields back to output file
        for img_col in imagery_lookup_gdf.columns:
            # Don't overwrite geometry
            if img_col != 'geometry':
                output_gdf[img_col] = output_gdf.apply(lambda row: imagery_lookup_gdf.loc[row['ALL_IMAGE']][img_col],
                                                       axis=1)
        # Save output to shapefile
        out_filename = os.path.join(self.cd, 'AOI.shp')
        output_gdf.to_file(out_filename)

        print 'Completed in {} Minutes'.format(round(((time.time() - start) / 60), 2))

    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#

    ##############################################################
    # DATA EJECTION Methods                                      #
    ##############################################################

    def eject_region_hex_grid(self):

        """
        Assumption: create_scores() has already been run
        :return: a shapefile in the working directory
        """

        for region in self.hex_list.iterkeys():
            hexes = self.OutputDict[region][2]
            out_dir = os.path.join(self.output_dir, "Hex_" + region + ".shp")
            hexes.to_file(out_dir)

    #--------------------------------------------------------------------------------------------------------#

    def eject_region_zscore_points(self):
        """
        Assumption: create_seeds() has already been run
        :return: a shapefile in the working directory
        """

        for region in self.hex_list.iterkeys():
            rpoints = self.Growth_Seeds[region]
            out_dir = os.path.join(self.output_dir, "Retail_ZScored_" + region + ".shp")
            rpoints.to_file(out_dir)

    #--------------------------------------------------------------------------------------------------------#

    def eject_region_zscore_points_combined(self):
        """
        Assumption: create_seeds() has already been run
        :return: a shapefile in the working directory
        """

        in_gdf = pd.concat([gdf for gdf in self.Growth_Seeds.itervalues()], ignore_index=True)
        in_gdf = gpd.GeoDataFrame(in_gdf, crs=self.Growth_Seeds[self.Growth_Seeds.keys()[0]].crs)
        out_dir = os.path.join(self.output_dir, "Combined_ZScored.shp")
        in_gdf.to_file(out_dir)

    #--------------------------------------------------------------------------------------------------------#

    def identify_regions(self):
        """
        
        :return: a list of regions. 
        """
        # BUG: NOT ALL REGIONS MAY BE IN CURRENT ORDER
        # reg_gpd = gpd.GeoDataFrame.from_file(self.rsm_regions)
        # regions = [r for r in reg_gpd['NAME']]
        regions = self.sample_regions['NAME'].unique()
        return regions


    # END SCRIPT
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
    #------------------------------#------------------------------#------------------------------#
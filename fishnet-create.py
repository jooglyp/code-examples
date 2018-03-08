
"""
Pseudo Algo for Creating Attributed Grids

* build a geodataframe based script (or pyshp/fiona)

for group in gdf[FIELD_NAME].unique():
	group_gdf = gdf[gdf[FIELD_NAME] == group].copy()
	group_bounds = group_gdf.bounds
	group_intersect_gdf = geodataframe_select_by_location(points_gdf, group_gdf)

1) Prepare subset point data
2) For each point subset,
	a) determine the bounding box extent
	b) use the bounding box extents to generate a local fishnet grid

"""

import sys
# 64bit anaconda architecture:
sys.path.append(r"C:\Anaconda2_64bit")
sys.path.append(r"C:\Anaconda2_64bit\Scripts")
sys.path.append(r"C:\Anaconda2_64bit\Library\bin")
sys.path.append(r"C:\Anaconda2_64bit\Lib\site-packages")
#---#
import os
import geopandas
from geopandas.tools import sjoin
import pysal
from pyproj import Proj, transform
from pysal.weights.Distance import DistanceBand
from pysal.esda.getisord import G
import shapely
from shapely.geometry import shape, base
from shapely.geometry import Polygon, Point, box, asPolygon, asPoint, MultiPoint
from shapely import wkt
import fiona
import ogr, osr
from osgeo import ogr, osr
import pandas as pd
import itertools
import numpy as np
import scipy
import math
from math import log
import shapefile
import re

#------------------------------------------------------------------------------------------------
#############
## Methods ##
#############

#---------------------------------------------

def xfrange(start, stop, step):
    # algorithm pulled from here:
    # https://github.com/DigitalGlobe/gbdxtools/blob/master/gbdxtools/catalog_search_aoi.py
    # range() but for float steps
    while start < stop:
        yield start
        start += step
    else:
        yield stop

#---------------------------------------------

def geoms_to_shp(in_geoms, out_shp, projection):
    # algorithm pulled from here:
    # https://github.com/DigitalGlobe/gbdxtools/blob/master/gbdxtools/catalog_search_aoi.py

    prj_name = '{}.prj'.format(out_shp.split('.')[0])
    with open(prj_name, 'w') as prj:
        prj.write(projection)
    shp_writer = shapefile.Writer(shapefile.POLYGON)
    out_fields = [
                    ['id', 'N']
                ]
    out_fields_names = [x[0] for x in out_fields]
    for name in out_fields:
        shp_writer.field(*name)
    #------------------------------
    for in_id, geom in enumerate(in_geoms, start=1):
        shp_writer.record(*[str(in_id)])
        shp_writer.poly(parts=[list(box(*geom).exterior.coords)])
    shp_writer.save(out_shp)

#---------------------------------------------
def create_fishnet(bbox, grid_size, output_name):
    """

    :param bbox: [w, s, e, n] list object
    :param grid_size: an integer in meters
    :param output_name: a string with a .shp file type ending (a full directory path)
    :return: void. Invokes geoms_to_shp() to output a shapefile to the output_name directory
    """
    # Create Fishnet (David's Method):

    # Latitude: 1 deg = 110.574 km
    # Longitude: 1 deg = 111.320*cos(latitude) km

    # We need 5 km:

    # shp = shapefile.Reader(file)
    # the following metadata is from the .prj file
    us_albers_equal_area = 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID\
    ["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],\
    PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],\
    PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]'

    wgs84 = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'

    # grid size in degrees or meters - depending on input projection
    # grid_size = 50000   # this is 5 km

    # w, s, e, n = shp.bbox
    w, s, e, n = bbox
    Ys = [i for i in xfrange(s, n, grid_size)]
    Xs = [i for i in xfrange(w, e, grid_size)]

    bb_li = []
    row = 0
    col = 0
    for y, y1 in zip(Ys, Ys[1:]):
        row += 1
        for x, x1 in zip(Xs, Xs[1:]):
            col += 1
            bbox = (x, y, x1, y1)
            bb_li.append(bbox)

    geoms_to_shp(bb_li, output_name, us_albers_equal_area)

#---------------------------------------------
##########################
## Directory Management ##
##########################

cd = r"C:\Users\joogl\OneDrive\Documents\GIS DataBase\Retailer_Grid"
prefix = "Tickers_Points_Sub_"

# loop through directory and identify all shapefiles with "prefix"
# Note: will deprecate this method later and instead create a new attribute ID that delineates region
sub_files = []
for file in os.listdir(cd):
    if file.startswith(prefix):
        if file.endswith(".shp"):
            sub_files.append(file)

# ---------------------------------------------
###################
## Grid Creation ##
###################

# For each of these shapefiles, open the shapefile, determine the bounding box extent, and generate a unique
# fishnet grid
for file in sub_files:
    sub_dir = os.path.join(cd, file)
    # instantiate a geopandas df object based on the points subset shapefile
    sub_gdf = geopandas.GeoDataFrame.from_file(sub_dir)
    # instantiate a shapefile object based on the points subset shapefile
    sub_shp = shapefile.Reader(sub_dir)
    # determine the bounding box extent using shapefile
    """
    Can easily do this with:
    pyshp, or ogr, or fiona, or geopandas, or by pulling bytes 36 through 60 from the
    header of the actual shapefile (fun fact. the bbox of a shapefile is stored in
    the header of the actual file)

    In geopandas:
    geopandas (in_gdf.total_bounds) or bounds of each feature (in_gdf.bounds)
    """
    shp_bounds = sub_shp.bbox
    # create an output file name
    # For Slashes Only: m = re.search(r"\[([A-Za-z0-9_]+)\]", file)
    m = re.search(r"^[^.]*", file)
    file_name = m.group(0)
    grid_out = os.path.join(cd, file_name+"_grid.shp")
    # # # Create the fishnet # # #
    create_fishnet(shp_bounds, 5000, grid_out)


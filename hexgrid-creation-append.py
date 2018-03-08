
"""
Algo for Creating Attributed Grids
operating assumption is that some analyst came up with some subsets of the retail point shapefile
 and that those points are projected in aea

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
from shapely.geometry import Polygon, Point, box, asPolygon, asPoint, MultiPoint, shape, base
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
import glob

#------------------------------------------------------------------------------------------------
#############
## Methods ##
#############

#---------------------------------------------

def calculate_polygons(startx, starty, endx, endy, radius):
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
                (p1x, p1y),
                (p2x, p2y),
                (p3x, p3y),
                (p4x, p4y),
                (p5x, p5y),
                (p6x, p6y),
                (p1x, p1y)]
            polygons.append(poly)
            counter += 1
            startx += w
        starty += yoffset
        row += 1
    return polygons

#---------------------------------------------

def geoms_to_hex_shp(in_geoms, out_shp, projection):
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
    #------------------------------
    for in_id, geom in enumerate(in_geoms, start=1):
        shp_writer.record(*[str(in_id)])
        shp_writer.poly(parts=[geom])
    shp_writer.save(out_shp)

#---------------------------------------------

def quadrantize(minx, miny, maxx, maxy):
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
    SubBoxes["b1"] = box1   # quadrant 3
    SubBoxes["b2"] = box2   # quadrant 1
    SubBoxes["b3"] = box3   # quadrant 2
    SubBoxes["b4"] = box4   # quadrant 4

    return SubBoxes

#---------------------------------------------
##########################
## Directory Management ##
##########################

cd = r"C:\Users\joogl\OneDrive\Documents\GIS DataBase\Retailer_Grid"
prefix = "Tickers_Points_Sub_"

# loop through directory and identify all shapefiles with "prefix"
# Note: will deprecate this method later and instead create a new attribute ID that delineates region
# STEPP: this is more concise and doesn't overwrite the built-in file function
sub_files = [f for f in os.listdir(cd) if f.startswith(prefix) and f.endswith(".shp")]

# ---------------------------------------------
#################
## Projections ##
#################

us_albers_equal_area = 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID\
["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],\
PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],\
PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]'

wgs84 = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'

###################
## Grid Creation ##
###################

# For each of these shapefiles, open the shapefile, determine the bounding box extent, and generate a unique
# fishnet grid
# STEPP: replaced "file" variable with "input_file" to avoid overwrite built-in file function
for input_file in sub_files:
    # IMPORTANT: The input point shapefiles are assumed to be in AEA .prj!about
    sub_dir = os.path.join(cd, input_file)
    # instantiate a geopandas df object based on the points subset shapefile
    sub_gdf = geopandas.GeoDataFrame.from_file(sub_dir)
    # instantiate a shapefile object based on the points subset shapefile
    sub_shp = shapefile.Reader(sub_dir)
    # determine the bounding box extent using shapefile
    """
    Can easily do this with:
    pyshp, or ogr, or fiona, or geopandas, or by pulling bytes 36 through 60 from the
    header of the actual shapefile (fun fact. the bbox of a shapefile is stored in
    the header of the actual input_file)

    In geopandas:
    geopandas (in_gdf.total_bounds) or bounds of each feature (in_gdf.bounds)
    """
    
    # create an output input_file name
    # For Slashes Only: m = re.search(r"\[([A-Za-z0-9_]+)\]", input_file)

    # STEPP: consider using os.path.splitext() as it is more clear what you are trying to do
    m = re.search(r"^[^.]*", input_file)
    file_name = m.group(0)
    grid_out = os.path.join(cd, file_name+"_hex.shp")

    # Identify extent of points
    # IMPORTANT: assume that the points and their extents were determined by an analyst
    shp_bounds = sub_shp.bbox
    w, s, e, n = shp_bounds # these coordinates are currently assumed to be in aea (datum centered in Kansas)
    # To ensure that quadrantize() works properly, these coordinates need to be in wgs84
    """
    TO DO:
    Create a shape from these shp_bounds. If the area of this bbox is smaller than a hex with radius = 5000 meters,
    then rescale the shape so that it is and then reobtain the shp_bounds.
    """
    extent_area = box(w, s, e, n).area
    # STEPP: consider using a variable and calculation to determine area of hexagon from a radius variable
    # STEPP: otherwise you have to replace "86602540.378" everywhere it exists if you decide to change the radius
    if extent_area < 86602540.378:  # 86602540.378 is the area of a hexagon with radius = 5000 metersin gen
        # begin rescaling the extent_area
        # (1) The following condition, box(a,b,c,d).area/box(w,s,e,n).area = xfact*yfact.
        # (2) want to know --> (86602540.378*1.1)/box(w,s,e,n).area --> sqrt(*)
        req_growth = (86602540.378*1.1)/box(w,s,e,n).area
        scale_factor = req_growth**0.5
        nshp_bounds = shapely.affinity.scale(box(w, s, e, n), xfact=scale_factor, yfact=scale_factor)
        # obtain new bounds
        w, s, e, n = nshp_bounds
    print "PASS 1"
    # initiate the list of dictionary objects
    in_mesh = {}
    # Once this entire hexgrid function is classed, make exogenous the factor of quadratization
    order = 1
    # Subdivide the bounding box into 16 quadrants, hence 4^n mesh orders
    for fractal in range(0, order + 1):
        # for 2^exp, there is 1 box at exp=0/i=0, 4 boxes at exp=2/i=1, and 16 boxes at exp=4/i=2
        target_dim = 2**((2*fractal)+2)    # this is the dimension that the output "quadruple" will take
        origin_dim = 2**(2*fractal)    # this is the dimension that the input quadruple will take
        if fractal >= 1:
            if in_mesh[0].area < 86602540.378:  # 86602540.378 is the area of a hexagon with radius = 5000 metersin gen
                pass
            else:
                print "N=" + str(fractal)
                out_mesh = {}
                for m in range(0, origin_dim):
                    # in_mesh contains shapefile objects. Need to unzip these into coordinates
                    # (a) obtain the dictionary of quadrants for each quadrant element of in_mesh
                    in_quadrants = in_mesh[m]
                    # (b) find the bounds of each sub-quadrant and store them according to the sub-quadrant index
                    in_bounds = in_quadrants.bounds
                    w, s, e, n = in_bounds
                    print "Bounding Boxes:"
                    print w, s, e, n
                    out_mesh[m] = quadrantize(w, s, e, n)
                    # unzip each 4-set of m sub-quadrant indices (4 elements per out_mesh[q]) into an unzipped dictionary
                    unzip_mesh = {}
                    num = 0
                    for key in out_mesh:
                        for sub_key in out_mesh[key]:
                            shape = out_mesh[key][sub_key]
                            unzip_mesh[num] = shape
                            num = num + 1
                # set the in_mesh to the out_mesh. In_mesh will once again contain shapefile objects.
                in_mesh = unzip_mesh
        else:
            in_mesh[0] = quadrantize(w, s, e, n)
            unzip_mesh = {}
            num = 0
            for key in in_mesh:
                for sub_key in in_mesh[key]:
                    shape = in_mesh[key][sub_key]
                    unzip_mesh[num] = shape
                    num = num + 1
            in_mesh = unzip_mesh

    # For order = 1, 16 sub-divisions will be created. For order = 2, 64 subdivisions would be created.
    # Begin looping through the final out_mesh. For each subdivision, create a hex grid:

    print "PASS 2"
    out_mesh = in_mesh
    for i, rectangle in enumerate(out_mesh):
        grid_out_sub = os.path.join(cd, file_name + "_hex_" + str(i) + ".shp")
        shape_coords = out_mesh[rectangle].bounds
        w, s, e, n = shape_coords
        # # # Create the fishnet # # #
        vertices = calculate_polygons(w, s, e, n, 5000)

        # convert the list of tuples to a list of lists so that it can be interfaced with pyshp
        list_of_list = []
        for list_of_tuples in vertices:
            unravel = map(list, list_of_tuples)
            list_of_list.append(unravel)

        # Create the hex shapefile
        geoms_to_hex_shp(list_of_list, grid_out_sub, us_albers_equal_area)

    print "PASS 3"
    # Begin stitching together the shapefiles into one shapefile (using glob and shapefile)
    input_files = os.path.join(cd, file_name + "_hex_*" + ".shp")
    hex_files = glob.glob(input_files)
    w = shapefile.Writer()
    # create a prj file
    prj_name = '{}.prj'.format(grid_out.split('.')[0])
    with open(prj_name, 'w') as prj:
        prj.write(us_albers_equal_area)
    # merge the hexes
    for f in hex_files:
        r = shapefile.Reader(f)
        w._shapes.extend(r.shapes())
        w.records.extend(r.records())
    w.fields = list(shapefile.Reader(hex_files[1]).fields[1:])
    w.save(grid_out)

# ---------------------------------------------

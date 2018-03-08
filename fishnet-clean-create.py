
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

#------------------------------------------------------------------------------------------------
#############
## METHODS ##
#############

def getXY(pt):
    return (pt.x, pt.y)

#---------------------------------------------

# algorithm pulled from here:
# https://github.com/DigitalGlobe/gbdxtools/blob/master/gbdxtools/catalog_search_aoi.py

def geoms_to_shp(in_geoms, out_shp, projection):
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

# algorithm pulled from here:
# https://github.com/DigitalGlobe/gbdxtools/blob/master/gbdxtools/catalog_search_aoi.py

# range() but for float steps
def xfrange(start, stop, step):
    while start < stop:
        yield start
        start += step
    else:
        yield stop

#---------------------------------------------

#------------------------------------------------------------------------------------------------
##############################
## PRELIMINARY DATA HANDLES ##
##############################

# Directory:

cd = r"C:\Users\joogl\OneDrive\Documents\GIS DataBase\Retailer_Grid"
grid = "Retailer_Grid_Subset2_aea.shp"
grid_dir = os.path.join(cd, grid)
grid_gdf = geopandas.GeoDataFrame.from_file(grid_dir)
stores = "Tickers_Points_Subset2_aea.shp"
stores_dir = os.path.join(cd, stores)
stores_gdf = geopandas.GeoDataFrame.from_file(stores_dir)

# Tupled x,y coordinates:
xylist = map(getXY, grid_gdf['geometry'])
# Alternative Method 1: gdf['geometry'].applymap(getXY)
# Alternative Method 2: gdf.apply(lambda row: (row['geometry'].x, row['geometry'].y))
# gdf's can be plotted: gdf.plot()

#------------------------------------------------------------------------------------------------
###################
## GRID CREATION ##
###################

# METHOD 1:

# get the extent in centimeters (converting from UTM meters)
minx,maxx,miny,maxy = min(x_list), max(x_list), min(y_list), max(x_list)
dx = 5000 # these are meters. This number reflects a 5 km/sq box length
dy = 5000 # these are meters. This number reflects a 5 km/sq box length

nx = int(math.ceil(abs(maxx - minx)/dx))
ny = int(math.ceil(abs(maxy - miny)/dy))

# Invoking shapefile module
w = shapefile.Writer(shapefile.POLYGON)
w.autoBalance = 1
w.field("ID")
id=0

for i in range(ny):
    for j in range(nx):
        id+=1
        vertices = []
        parts = []
        vertices.append([min(minx+dx*j,maxx),max(maxy-dy*i,miny)])
        vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*i,miny)])
        vertices.append([min(minx+dx*(j+1),maxx),max(maxy-dy*(i+1),miny)])
        vertices.append([min(minx+dx*j,maxx),max(maxy-dy*(i+1),miny)])
        parts.append(vertices)
        w.poly(parts)
        w.record(id)

fishnet_name = 'polygon_grid'
w.save(os.path.join(cd, fishnet_name))

#---------------------------------------------
# METHOD 2:

# Latitude: 1 deg = 110.574 km
# Longitude: 1 deg = 111.320*cos(latitude) km

# We need 5 km:

D = float(1/22.1148)  # the size in degrees of the side of a square that we will search
"""
Note:
It is assumed that shapes is not in epsg_4326 (WGS 1984), but in albers equal area, which is meter-based.
The following code in shapely assumes that the coordinate data are northing/easting points.
"""
W, S, E, N = MultiPoint(xylist).bounds

# Conversion Process:
# bng = Proj(spatialRef.ExportToProj4())  # pyproj module
bng = Proj(init='epsg:102003')
wgs84 = Proj(init='epsg:4326')  #pyproj module
Wlon,Slat = transform(bng,wgs84, W, S)   # pyproj module
Elon,Nlat = transform(bng,wgs84, E, N)   # pyproj module

Ys = [i for i in xfrange(Slat,Nlat,D)]
Xs = [i for i in xfrange(Wlon,Elon,D)]

bb_li = []
row = 0
col = 0
for y, y1 in zip(Ys, Ys[1:]):
    row += 1
    for x, x1 in zip(Xs, Xs[1:]):
        col += 1
        bbox = (x, y, x1, y1)
        bb_li.append(bbox)
        #print bbox

geoms_to_shp(bb_li, 'Test.shp')

#---------------------------------------------
# METHOD 3 (David's Method):

# Latitude: 1 deg = 110.574 km
# Longitude: 1 deg = 111.320*cos(latitude) km

# We need 5 km:

shp = shapefile.Reader(file)
# the following metadata is from the .prj file
us_albers_equal_area = 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID\
["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],\
PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],\
PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]'

wgs84 = 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]'

# grid size in degrees or meters - depending on input projection
grid_size = 50000   # this is 5 km

w, s, e, n = shp.bbox
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

geoms_to_shp(bb_li, 'Grid.shp', us_albers_equal_area)

#---------------------------------------------
"""
Running Windows 10

This script is run in PyQGIS (th python shell of the OSGEO4W command line)
QGIS 2.18.3
Grass7
TauDem
- download TauDem with MS MPI Setup and TauDem537_setup.exe
- see gis.stackexchange.com/questions/164935/running-taudem-inqgis

READ ME:
- run all scripts except for getFlowlineElev-touch.py in the PYQGIS environment
- getFlowlineElev-touch.py should be executed in Python 2.7.13
- Ensure that Python 2.7.13 has a geopandas dependency
    * pip install geopandas
- Ensure that all vector files are initially projected as EPSG 3720 (Zone 17N)
"""
import sys
from qgis.utils import iface
sys.path.append('C:\Users\joogl\PycharmProjects\Watershed_Final')
import mergeElevData
import clipElevData
import calcUpstream
import getFlowlineElev

workspace = r"C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"
rasters = ['n29_w095_1arc_v3.tif', 'n29_w096_1arc_v3.tif', 'n30_w096_1arc_v3.tif']
vector = 'county_boundary.shp'
flowlines = 'county_flowline.shp'
pour_points = 'pour_point_utm.shp'

# (1) merge elevation data
mergeElevData.instructions()
m = mergeElevData.raster_merging(rasters, workspace)
merged_raster = m['USER_GRID']
iface.addRasterLayer(merged_raster, "merged_raster")

# (2) clip elevation data using county boundary
clipElevData.instructions()
rprj, crast = clipElevData.clip_the_raster(merged_raster, vector, workspace)
clipped_raster = crast['OUTPUT']
iface.addRasterLayer(clipped_raster, "clipped_raster")

# (3) watershed analysis
calcUpstream.instructions()
wshed, drainage, watershed_upstream = calcUpstream.watershed_analysis(pour_points, clipped_raster, flowlines, workspace)

# (4) get flowline elevations
getFlowlineElev.instructions()
dem_points = getFlowlineElev.get_dem_points(flowlines, wshed, workspace)
# start a Python 2.7.13 environment outside of QGIS, cd to script directory, and execute script by typing:
# python getFlowlineElev-touch.py
# the output of this file is the polyline file with elevation attributes. It can be visualized in qgis
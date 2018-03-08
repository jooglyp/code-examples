"""
Purpose:
- Get a sampled points from a polyline with dem elevation attributes and polyline ID attributes
"""

import os
from PyQt4.QtCore import *
import processing
from qgis.utils import iface

#-------------------------#

def instructions():
    prompt = """
    Parameters
    ----------
      arg1: the flowlines shapefile
      arg2: the dem file
      arg3: the working directory
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:
    Note: please ensure that all files in this operation reside in the same directory.

    >>> flowlines = "county_flowline.shp"
    >>> geography = "RGB_byte_masked.tif"
    >>> workspace = r"C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"

    Returns (path of) points-with-dem-samples
    """
    print(prompt_example)
    print("-----------------------------------")

#--------------------------------------------------------------------#

def get_dem_points(flowlines, dem, workspace):
    os.chdir(workspace)

    # sample the line and create a point layer
    sample_nodes = processing.runalg("qgis:extractnodes",str(os.path.join(workspace, flowlines)),None)
    n_nodes = sample_nodes['OUTPUT']
    #iface.addVectorLayer(n_nodes, "n_nodes","ogr")

    # ensure that the points and raster are in the same coordinate system
    sample_nodes_reproj = processing.runalg("qgis:reprojectlayer",n_nodes,"EPSG:4269",None)
    reproj_n_nodes = sample_nodes_reproj['OUTPUT']
    #iface.addVectorLayer(reproj_n_nodes, "reproj_n_nodes","ogr")

    # join the raster dem data to the sampled points
    rlayer = QgsRasterLayer(dem, u'OUTPUT')
    ext = rlayer.extent()
    xmin = ext.xMinimum()
    xmax = ext.xMaximum()
    ymin = ext.yMinimum()
    ymax = ext.yMaximum()

    coords = "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax)  # this is a string that stores the coordinates

    dem_nodes = processing.runalg("grass7:v.sample",reproj_n_nodes,"COMID",dem,1,0,coords,-1,0.0001,0,None)
    dem_nodes_sampled = dem_nodes['output']
    #iface.addVectorLayer(dem_nodes_sampled, "dem_nodes_sampled","ogr")
    dns_prj = processing.runalg("qgis:reprojectlayer",dem_nodes_sampled,"EPSG:4269",None)
    dns_reproj = dns_prj['OUTPUT']
    #iface.addVectorLayer(dns_reproj, "dns_reproj","ogr")

    # intersect the sampled points with dem data with the polyline in order to obtain lineID's in the point attributes
    dem_nodes_lineID = processing.runalg("qgis:intersection",dns_reproj,os.path.join(workspace, flowlines),False,None)

    # export this file
    dem_nodes_dir = dem_nodes_lineID['OUTPUT']
    iface.addVectorLayer(dem_nodes_dir, "sampled_points", "ogr")
    _vlayer = QgsMapLayerRegistry.instance().mapLayersByName("sampled_points")[0]
    _writer = QgsVectorFileWriter.writeAsVectorFormat(_vlayer, os.path.join(workspace,"sampled_points.shp"), \
                                                      "utf-8", None, "ESRI Shapefile")

    print("Done.")
    return os.path.join(workspace,"sampled_points.shp")
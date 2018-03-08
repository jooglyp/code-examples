"""
Purpose:
User specifies a shapefile as a mask to be applied against a raster for purpose of clipping
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
      arg1: the target tif file to be clipped
      arg2: the mask file (.shp) to be used as a mask
      arg3: workspace (full path directory to workspace)
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:
    Note: please ensure that all files in this operation reside in the same directory.

    >>> raster = 'out.tif'
    >>> vector = "county_boundary.shp"
    >>> workspace = "C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"
    
    Returns reprojected_county, clipped_raster
    """
    print(prompt_example)
    print("-----------------------------------")

#--------------------------------------------------------------------#

def clip_the_raster(raster, vector, workspace):
    os.chdir(workspace)

    # need to project the county to the same projection system as the raster
    reproj_county = processing.runalg("qgis:reprojectlayer", \
                      str(os.path.join(workspace, vector)), \
                      "EPSG:4326", None)
    reproj = reproj_county['OUTPUT']
    iface.addVectorLayer(reproj, "reproj_county","ogr")
    print "Projection Complete..."

    clipped_raster = processing.runalg("saga:clipgridwithpolygon",
                        str(os.path.join(workspace, raster)), \
                        str(reproj), \
                      None)

    print("Done.")
    return reproj, clipped_raster


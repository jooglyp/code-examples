"""
Purpose:
- Given a target grid-cell (given as a raster subset of the elevation-raster), return 
 the upstream watershed (also as a raster subset) by using the flowline (.shp) vector data
- requirements => (1) clipped elevation raster, (2) flowlines vector, (3) downstream raster 
grid cell
- Aside: requires a DEM of the input raster data
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
      arg1: the target downstream grid-cell .shp format (should be in EPSG 3720 UTM 13N coordinates)
      arg2: the analysis area tif file that represents the geography's elevation data
      arg3: the flowlines vector (.shp) to be used as a watershed identifier
      arg4: workspace (full path directory to workspace)
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:
    Note: please ensure that all files in this operation reside in the same directory.

    >>> downstream = 'pour_point_utm.shp'
    >>> geography = "RGB_byte_masked.tif"
    >>> flowlines = "county_flowline.shp"
    >>> workspace = r"C:\Users\joogl\One Concern Assessment\jp_outputs_report"
    
    Returns filled-dem, drainage-directions, upstream-watershed
    """
    print(prompt_example)
    print("-----------------------------------")

#--------------------------------------------------------------------#

def watershed_analysis(points, dem, flowlines, workspace):
    os.chdir(workspace)

    # fill the sinks. **input raster should be in UTM Zone 13N (EPSG 3720) - should be done as a save-as op in qgis
    #*********#
    # assuming that dem is a full path
    ous = processing.runalg("taudem:pitremove", str(dem), None)
    #*********#
    wshed = ous['-fel']
    iface.addRasterLayer(wshed, "Filled DEM")

    # -----------------------------------------------#
    # construct a watershed analysis. **input raster should have projection defined as Nad 27 EPSG 32041 for taudem routines
    #*********#
    results = processing.runalg("taudem:d8flowdirections", wshed, None, None)
    #*********#
    drainage = results['-p']
    iface.addRasterLayer(drainage, "drainage")

    #-----------------------------------------------#
    # identify upstream watershed. **rasters should be projected/reprojected to UTM Zone 13N (EPSG 3720)
    # -95.620693, 29.965358

    #*********#
    watershed = processing.runalg("taudem:dinfinitycontributingarea", drainage, points, None, True, None)
    #*********#
    watershed_upstream = watershed['-sca']
    iface.addRasterLayer(watershed_upstream, "watershed_upstream")

    #-----------------------------------------------#
    # clip the dem file using the vectorization of this upstream watershed

    watershed_vec = processing.runalg("gdalogr:polygonize", watershed_upstream, "DN", None)
    mask = watershed_vec['OUTPUT']

    mask_reproj = processing.runalg("qgis:reprojectlayer", mask, "EPSG:3720", None)
    mask_prj = mask_reproj['OUTPUT']
    iface.addVectorLayer(mask_prj, "mask_prj","ogr")

    # mask file's projection should be the projection used by the raster layers
    final = processing.runalg("saga:clipgridwithpolygon", str(dem), mask_prj, None)
    raster_final = final['OUTPUT']
    iface.addRasterLayer(raster_final, "raster_final")

    return wshed, drainage, raster_final

    print("Done.")
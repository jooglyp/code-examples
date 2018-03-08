"""
Purpose:
User supplies a LIST of .tif files. Script merges these .tif files into 1 tif file. Outputs into user elected dir.
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
      arg1: list of tif files (comma separated list vector)
      arg2: workspace (full path directory to workspace)
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:

    >>> file_list = ['n29_w095_1arc_v3.tif', 'n29_w096_1arc_v3.tif', 'n30_w096_1arc_v3.tif']
    >>> workspace = "C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"
    
    Returns Merged_raster
    """
    print(prompt_example)
    print("-----------------------------------")

#--------------------------------------------------------------------#
def raster_merging(file_list, workspace):
    os.chdir(workspace)

    x1_l = []
    x2_l = []
    y1_l = []
    y2_l = []

    for n, im in enumerate(file_list):
        nf = os.path.join(workspace, file_list[n])
        iface.addRasterLayer(nf, "raster" + "_" + str(n))
        layer = iface.activeLayer()
        ext = layer.extent()
        xmin = ext.xMinimum()
        xmax = ext.xMaximum()
        ymin = ext.yMinimum()
        ymax = ext.yMaximum()
        x1_l.append(xmin)
        x2_l.append(xmax)
        y1_l.append(ymin)
        y2_l.append(ymax)

    print(x1_l)
    print(x2_l)
    print(y1_l)
    print(y2_l)

    coords = "%f,%f,%f,%f" % (min(x1_l), max(x2_l), min(y1_l), max(y2_l))  # this is a string that stores the coordinates

    merged_raster = processing.runalg("saga:mosaickrasterlayers",
                      str(file_list[0] + ";" + \
                      file_list[1] + ";" + \
                      file_list[2]), None, 7, 0, 1, 10, 0, 0, coords, None)
    # 0,100,0,100
    print("Done.")
    return merged_raster

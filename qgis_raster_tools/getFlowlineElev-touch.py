"""
Purpose:
- Get a polyline that has dem elevation attributes 
"""

import geopandas as gpd
import os

#-------------------------#
# Main
if __name__ == '__main__':

    prompt = """
    Parameters
    ----------
      arg1: the flowlines shapefile
      arg2: sampled points
      arg3: the working directory
    """
    print(prompt)
    print("-----------------------------------")

    # Start Params and Custom Scripts:
    prompt_example = """
    [EXAMPLE INPUT]:

    >>> flowlines = "county_flowline.shp"
    >>> sampled_points = "sampled_points.shp"
    >>> workspace = "C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"
    """
    print(prompt_example)
    print("-----------------------------------")

    flowlines = input('file_list: ')
    sampled_points = input('workspace: ')
    workspace = input('workspace: ')
    workspace = workspace.replace("\"", "")

    #-----------------------------------------------#
    os.chdir(workspace)

    #workspace = r"C:\Users\joogl\One Concern Assessment\gis_challenge\gis_challenge"
    #flowlines = "county_flowline.shp"
    #sampled_points = 'sampled_points.shp'

    point_lineID_dem_gpd = gpd.read_file(os.path.join(workspace, sampled_points))
    flow_lines_gpd = gpd.read_file(os.path.join(workspace, flowlines))

    source = point_lineID_dem_gpd.groupby('COMID', as_index=False)['rast_val'].mean()

    rejoin = flow_lines_gpd.merge(source, on='COMID')

    out_dir = os.path.join(workspace, "lines_dem_sampled.shp")
    rejoin.to_file(out_dir)

    print("Done.")
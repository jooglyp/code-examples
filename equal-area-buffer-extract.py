"""
Purpose:
Obtain total population and number of households within 3/5/10 miles. Use assumption that these statistics
are proportional to land area.
"""

# special
import matplotlib.pyplot as plt
import pysal as ps

# basic
import os
import sys
import pandas as pd
import geopandas as gpd
import shapely
from shapely import geometry
from shapely.geometry import Polygon
from shapely.validation import explain_validity

# set file
directory_stores = "<<Point File Here Path>>"
directory_dems = "<<ACS2015_ShapeFile Path>>"

stores_layer = "<<Point File Shapefile>>"
dem_layer = "<<ACS Shapefile>>"
dem_dir = os.path.join(directory_dems, dem_layer)

# create directory
# dem_dir = os.path.join(directory_stores, dem_layer)
stores_dir = os.path.join(directory_stores, stores_layer)

# create files
dem_gdf = gpd.read_file(dem_dir)
stores_gdf = gpd.read_file(stores_dir)

# set projection to AEA
out_prj = '+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs'
if dem_gdf.crs != out_prj:
    dem_gdf.to_crs(out_prj, inplace=True)
if stores_gdf.crs != out_prj:
    stores_gdf.to_crs(out_prj, inplace=True)

#-------------------------------------------------------------------------------#
def prep_geometries(input_geodataframe, imagery_geodataframe, simp_tol=None):
   """
   Unions all geometries together within intersecting imagery
   Clips unions to respective imagery
   Explodes multipart polygons to single part
   Convert modified geometries back to GeoDataFrame
   Appends area field
   """
   union = input_geodataframe.groupby('ALL_IMAGE')['geometry'].agg(shapely.ops.unary_union)
   union_geoseries = gpd.GeoSeries(union, crs=input_geodataframe.crs)
   union_clipped = clip_to_imagery(union_geoseries, imagery_geodataframe)
   polys_singlepart = union_clipped.explode()
   polys_single_gdf = gpd.GeoDataFrame(polys_singlepart.to_frame().reset_index(), crs=input_geodataframe.crs)
   polys_single_gdf.columns = ['ALL_IMAGE', 'AREA', 'geometry']
   if simp_tol:
       polys_single_gdf['geometry'] = polys_single_gdf['geometry'].map(lambda g: Polygon(g.exterior).simplify(simp_tol))
   else:
       polys_single_gdf['geometry'] = polys_single_gdf['geometry'].map(lambda g: Polygon(g.exterior))
   polys_single_gdf['AREA'] = polys_single_gdf['geometry'].area
   return polys_single_gdf

#-------------------------------------------------------------------------------#
def geodataframe_intersection(target_gdf, source_gdf, simp_tol=0):
    """
    Intersects target geodataframe to source geodataframe
    Optionally simplifies target geodataframe to reduce computation time


    Parameters
    ----------
    target_gdf: target geodataframe
        GeoDataFrame of features to be intersected
    source_gdf: source geodataframe
        GeoDataFrame of features to intersect to
    simp_tol: simplification tolerance
        Larger value equals greater simplifications
        Value of 0 will produce no simplification

    Returns
    -------
    geodataframe
        GeoDataFrame of intersected features
    """
    target_simp_gdf = target_gdf.copy()
    target_simp_gdf['geometry'] = target_simp_gdf.simplify(simp_tol)
    out_gdf = gpd.GeoDataFrame(columns=target_simp_gdf.columns, crs=target_simp_gdf.crs)
    target_sindex = target_simp_gdf.sindex
    for geom in source_gdf['geometry']:
        possible_matches_index = list(target_sindex.intersection(geom.bounds))
        possible_matches = target_simp_gdf.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(geom)].copy()
        precise_matches['geometry'] = precise_matches.intersection(geom)
        out_gdf = out_gdf.append(precise_matches)
    out_gdf.reset_index(drop=True, inplace=True)
    return out_gdf

#-------------------------------------------------------------------------------#
def geodataframe_select_by_location(target_gdf, source_gdf, return_indices=False, reverse_selection=False):
   if all(source_gdf.geom_type == 'Point'):
       source_un = source_gdf.unary_union
       if reverse_selection:
           out_gdf = target_gdf[~target_gdf.intersects(source_un)].copy()
       else:
           out_gdf = target_gdf[target_gdf.intersects(source_un)].copy()
       if return_indices:
           return out_gdf.index.tolist()
       else:
           return out_gdf
   else:
       out_ndx = []
       target_sindex = target_gdf.sindex
       for geom in source_gdf['geometry']:
           possible_matches_index = list(target_sindex.intersection(geom.bounds))
           possible_matches = target_gdf.iloc[possible_matches_index]
           precise_matches = possible_matches[possible_matches.intersects(geom)].index.tolist()
           out_ndx.extend(precise_matches)
       out_ndx = sorted(list(set(out_ndx)))
       if return_indices:
           if reverse_selection:
               target_indices = target_gdf.index.tolist()
               out_ndx = [n for n in target_indices if n not in out_ndx]
           return out_ndx
       else:
           if reverse_selection:
               reverse_ndx = [n for n in target_gdf.index if n not in out_ndx]
               out_gdf = target_gdf.loc[reverse_ndx].copy()
           else:
               out_gdf = target_gdf.loc[out_ndx].copy()
           return out_gdf

#-------------------------------------------------------------------------------#
# Simplify Polygons

# dem_gdf['geometry'] = dem_gdf.simplify(0.0005)

#-------------------------------------------------------------------------------#

"""
3 miles: 4828.032
5 miles: 8046.72
10 miles: 16093.44
"""

# Function to convert Square Meters to Square Kilometers
m_to_km = lambda p: p.area / 1000000
# Function to convert Square Kilometers to Square Meters
km_to_m = lambda p: p.area * 1000000

# Add area field to dems file (will be denominator to 'CLIP_AREA' see below)
dem_gdf['AREA'] = dem_gdf['geometry'].map(lambda geom: m_to_km(geom))
#----------------------------------- BEGIN ANALYSIS -----------------------------------#

"""
# Plot
fig, ax = plt.subplots(1, figsize=(3.5,7))
base = dem_gdf.plot(ax=ax, color='gray')
buffer_3 = store_buffer_3_mile.plot(ax=ax, color='yellow')
stores_gdf.plot(ax=base, marker="o",
                markersize=5,
                alpha=0.5)
_ = ax.axis('off')
ax.set_title("3 mile buffer example")
"""

#----------#
# Part 1. Re-join stores_gdf attributes to store_buffers

store_buffer_3_mile_gdp = stores_gdf.copy()
store_buffer_3_mile_gdp['geometry'] = stores_gdf.buffer(4828.032)

store_buffer_5_mile_gdp = stores_gdf.copy()
store_buffer_5_mile_gdp['geometry'] = stores_gdf.buffer(8046.72)

store_buffer_10_mile_gdp = stores_gdf.copy()
store_buffer_10_mile_gdp['geometry'] = stores_gdf.buffer(16093.44)

#----------#
# Help simplify search with a Select by Location

#----------#
# Conduct Unary Unions. Do not use overlay, as that retains areas beyond the circumference. Use Intersect

Clips_3mile = geodataframe_intersection(dem_gdf, store_buffer_3_mile_gdp, simp_tol=0.0005)
Clips_5mile = geodataframe_intersection(dem_gdf, store_buffer_5_mile_gdp, simp_tol=0.0005)
Clips_10mile = geodataframe_intersection(dem_gdf, store_buffer_10_mile_gdp, simp_tol=0.0005)

#---#

Clips_3mile['CLIP_AREA'] = Clips_3mile['geometry'].map(lambda geom: m_to_km(geom))
Clips_5mile['CLIP_AREA'] = Clips_5mile['geometry'].map(lambda geom: m_to_km(geom))
Clips_10mile['CLIP_AREA'] = Clips_10mile['geometry'].map(lambda geom: m_to_km(geom))

#--#
# Part 2b. Merge the 3/5/10 mile intersects into one layer to calculate the geographic totals
# applying normal Pandas patterns and using Shapely functions to aggregate.
union_3m = Clips_3mile.groupby('ZCTA5CE10')['geometry'].agg(shapely.ops.unary_union)
union_geoseries_3m = gpd.GeoSeries(union_3m, crs=Clips_3mile.crs)
# New Clip Area needs to be calculated for this new layer. To be used for attribute totals!
Clips_3m_tot = Clips_3mile.copy()
Clips_3m_tot['NEW_AREA'] = Clips_3mile['ZCTA5CE10'].map(m_to_km(union_geoseries_3m).to_dict())
# Clips_3m_tot[['Population', 'AREA', 'CLIP_AREA', 'NEW_AREA']]

union_5m = Clips_3mile.groupby('ZCTA5CE10')['geometry'].agg(shapely.ops.unary_union)
union_geoseries_5m = gpd.GeoSeries(union_5m, crs=Clips_3mile.crs)
# New Clip Area needs to be calculated for this new layer. To be used for attribute totals!
Clips_5m_tot = Clips_5mile.copy()
Clips_5m_tot['NEW_AREA'] = Clips_5mile['ZCTA5CE10'].map(m_to_km(union_geoseries_5m).to_dict())

union_10m = Clips_3mile.groupby('ZCTA5CE10')['geometry'].agg(shapely.ops.unary_union)
union_geoseries_10m = gpd.GeoSeries(union_10m, crs=Clips_10mile.crs)
# New Clip Area needs to be calculated for this new layer. To be used for attribute totals!
Clips_10m_tot = Clips_10mile.copy()
Clips_10m_tot['NEW_AREA'] = Clips_10mile['ZCTA5CE10'].map(m_to_km(union_geoseries_10m).to_dict())

#----------#
# Part 3. Spatial Join M:M, stores as target and dems as source (this is the default setting of an M:M spatial join)
sjoin_store3m = gpd.sjoin(store_buffer_3_mile_gdp, Clips_3mile, how='left')
sjoin_store5m = gpd.sjoin(store_buffer_5_mile_gdp, Clips_5mile, how='left')
sjoin_store10m = gpd.sjoin(store_buffer_10_mile_gdp, Clips_10mile, how='left')

#----------#
# Part 4. For each row, calculate ['CLIP_AREA']/['AREA'] and multiply ['Population'] and ['B11002e1']
Pop_Shares_3m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in sjoin_store3m.iterrows()]
Households_3m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in sjoin_store3m.iterrows()]
# merge back to s_join layers
Pop_Shares_3m_pdf = pd.DataFrame(Pop_Shares_3m, columns=['Pop_Share'])
Households_3m_pdf = pd.DataFrame(Households_3m, columns=['HH_Share'])

final_df_3m = sjoin_store3m.reset_index().merge(Pop_Shares_3m_pdf, left_index=True, right_index=True)
final_df_3m = final_df_3m.merge(Households_3m_pdf, left_index=True, right_index=True)
#--#

Pop_Shares_5m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in sjoin_store5m.iterrows()]
Households_5m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in sjoin_store5m.iterrows()]
# merge back to s_join layers
Pop_Shares_5m_pdf = pd.DataFrame(Pop_Shares_5m, columns=['Pop_Share'])
Households_5m_pdf = pd.DataFrame(Households_5m, columns=['HH_Share'])

final_df_5m = sjoin_store5m.reset_index().merge(Pop_Shares_5m_pdf, left_index=True, right_index=True)
final_df_5m = final_df_5m.merge(Households_5m_pdf, left_index=True, right_index=True)
#--#

Pop_Shares_10m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in sjoin_store10m.iterrows()]
Households_10m = [(x[1]['CLIP_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in sjoin_store10m.iterrows()]
# merge back to s_join layers
Pop_Shares_10m_pdf = pd.DataFrame(Pop_Shares_10m, columns=['Pop_Share'])
Households_10m_pdf = pd.DataFrame(Households_10m, columns=['HH_Share'])

final_df_10m = sjoin_store10m.reset_index().merge(Pop_Shares_10m_pdf, left_index=True, right_index=True)
final_df_10m = final_df_10m.merge(Households_10m_pdf, left_index=True, right_index=True)

#----------#
# Part 5. group-by Store_OID and sum newly created fields 'Pop_Share' and 'HH_Share'
store_pop_share_3m = final_df_3m.groupby(by=['Store_OID'])['Pop_Share'].sum()
store_hh_share_3m = final_df_3m.groupby(by=['Store_OID'])['HH_Share'].sum()
store_pop_share_3m = pd.DataFrame(store_pop_share_3m).reset_index()
store_hh_share_3m = pd.DataFrame(store_hh_share_3m).reset_index()
#--#

store_pop_share_5m = final_df_5m.groupby(by=['Store_OID'])['Pop_Share'].sum()
store_hh_share_5m = final_df_5m.groupby(by=['Store_OID'])['HH_Share'].sum()
store_pop_share_5m = pd.DataFrame(store_pop_share_5m).reset_index()
store_hh_share_5m = pd.DataFrame(store_hh_share_5m).reset_index()
#--#

store_pop_share_10m = final_df_10m.groupby(by=['Store_OID'])['Pop_Share'].sum()
store_hh_share_10m = final_df_10m.groupby(by=['Store_OID'])['HH_Share'].sum()
store_pop_share_10m = pd.DataFrame(store_pop_share_10m).reset_index()
store_hh_share_10m = pd.DataFrame(store_hh_share_10m).reset_index()

#--#
# Part 6. Create totals

Pop_Shares_3m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in Clips_3m_tot.iterrows()]
Households_3m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in Clips_3m_tot.iterrows()]

Pop_Shares_5m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in Clips_5m_tot.iterrows()]
Households_5m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in Clips_5m_tot.iterrows()]

Pop_Shares_10m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Population']) for x in Clips_10m_tot.iterrows()]
Households_10m_tot = [(x[1]['NEW_AREA']/float(x[1]['AREA']))*(x[1]['Households']) for x in Clips_10m_tot.iterrows()]

# set total values
store_pop_share_3m.set_value(len(store_pop_share_3m) + 1, 'Pop_Share', sum([x for x in Pop_Shares_3m_tot if str(x) != 'nan']))
store_hh_share_3m.set_value(len(store_hh_share_3m) + 1, 'HH_Share', sum([x for x in Households_3m_tot if str(x) != 'nan']))

store_pop_share_5m.set_value(len(store_pop_share_5m) + 1, 'Pop_Share', sum([x for x in Pop_Shares_5m_tot if str(x) != 'nan']))
store_hh_share_5m.set_value(len(store_hh_share_5m) + 1, 'HH_Share', sum([x for x in Households_5m_tot if str(x) != 'nan']))

store_pop_share_10m.set_value(len(store_pop_share_10m) + 1, 'Pop_Share', sum([x for x in Pop_Shares_10m_tot if str(x) != 'nan']))
store_hh_share_10m.set_value(len(store_hh_share_10m) + 1, 'HH_Share', sum([x for x in Households_10m_tot if str(x) != 'nan']))
#----------#

# save-out
out_dir_3m_pop = os.path.join(directory_stores, "3m_buffer_pop.csv")
store_pop_share_3m.to_csv(out_dir_3m_pop)

out_dir_3m_hh = os.path.join(directory_stores, "3m_buffer_hh.csv")
store_hh_share_3m.to_csv(out_dir_3m_hh)
#--#

out_dir_5m_pop = os.path.join(directory_stores, "5m_buffer_pop.csv")
store_pop_share_5m.to_csv(out_dir_5m_pop)

out_dir_5m_hh = os.path.join(directory_stores, "5m_buffer_hh.csv")
store_hh_share_5m.to_csv(out_dir_5m_hh)
#--#

out_dir_10m_pop = os.path.join(directory_stores, "10m_buffer_pop.csv")
store_pop_share_10m.to_csv(out_dir_10m_pop)

out_dir_10m_hh = os.path.join(directory_stores, "10m_buffer_hh.csv")
store_hh_share_10m.to_csv(out_dir_10m_hh)
#--#

# END SCRIPT
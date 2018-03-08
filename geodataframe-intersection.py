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
    target_sindex = target_simp_gdf.sindex      # spatial index for faster geoprocessing (like shx)
    for geom in source_gdf['geometry']:
        possible_matches_index = list(target_sindex.intersection(geom.bounds))  # intersection with sindex returns a .index
        possible_matches = target_simp_gdf.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(geom)].copy()
        # use .intersection(geom) to return a series of dems zip codes that is only where there was a .intersect with the pt buf
        # and then an actual shapely .intersection is performed
        precise_matches['geometry'] = precise_matches.intersection(geom)    # intersection NOT intersect. .intersection is shapely
        out_gdf = out_gdf.append(precise_matches)
    out_gdf.reset_index(drop=True, inplace=True)
    return out_gdf


# EXAMPLE:
# out_gdf = geodataframe_intersection(zip_gdf, cost_gdf, simp_tol=0.0005)
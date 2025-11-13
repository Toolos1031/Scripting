"""
import geopandas as gpd
from sklearn.cluster import DBSCAN
from shapely import Point
import pandas as pd
from shapely.ops import unary_union
import os

#poly_path = r"D:\test\1_Cybinka_Jemiola_zaznaczenia.shp"
folder_path = r"D:\___Lasy\sprawdzanie\laczenie_zaznaczen"

distance = 8

for i in os.listdir(folder_path):
    if i.endswith(".shp"):
        poly_path = os.path.join(folder_path, i)
        out_path = os.path.join(folder_path, "out", i)

        #Import shapefile
        poly = gpd.read_file(poly_path)


        temp_list = []

        #Create lists with coordinates separately
        for index, rows in poly.iterrows():
            if rows["geometry"] == None:
                pass
            else:
                temp_list.append({
                    "geometry" : Point(rows["geometry"].centroid.bounds[0], rows["geometry"].centroid.bounds[1])
                })

                temp_list.append({
                    "geometry" : Point(rows["geometry"].bounds[0], rows["geometry"].bounds[1])
                })

                temp_list.append({
                    "geometry" : Point(rows["geometry"].bounds[0], rows["geometry"].bounds[3])
                })

                temp_list.append({
                    "geometry" : Point(rows["geometry"].bounds[2], rows["geometry"].bounds[3])
                })

                temp_list.append({
                    "geometry" : Point(rows["geometry"].bounds[2], rows["geometry"].bounds[1])
                }) 

        #Create new geodataframe from the list
        my_gdf = gpd.GeoDataFrame(temp_list)

        my_gdf["xcoord"] = my_gdf.geometry.x
        my_gdf["ycoord"] = my_gdf.geometry.y

        #Create a numpy array
        coords = my_gdf[['xcoord', 'ycoord']].values

        #Cluster the points
        db = DBSCAN(eps = distance, min_samples = 5).fit(coords)

        #Extract cluster labels
        cluster_labels = pd.Series(db.labels_).rename("cluster")

        #Add them to the points
        df = pd.concat([my_gdf, cluster_labels], axis=1)

        hulls = []

        for clusterid, frame in df.loc[df["cluster"] != -1].groupby("cluster"):
            geom = unary_union(frame.geometry.tolist()).convex_hull
            hulls.append([clusterid, geom])

        df2 = pd.DataFrame.from_records(data = hulls, columns = ["cluster", "geometry"])
        df2 = gpd.GeoDataFrame(data = df2, geometry = df2["geometry"], crs = poly.crs)
        
        try:
            df2.to_file(out_path, engine = "fiona")
        except Exception as e:
            print(f"{i} FAILED for {e}")

"""

import os
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import unary_union
from sklearn.cluster import DBSCAN

folder_path = r"V:\ROBOCZY\RDLP_Zielona Gora 2025\zlaczone_zaznaczenia"
distance = 8.0  # CRS units (meters if projected)

out_dir = os.path.join(folder_path, "out")
os.makedirs(out_dir, exist_ok=True)

def sample_line_evenly(line, step):
    """Return points sampled every 'step' along a shapely LineString."""
    L = line.length
    if L == 0:
        return []
    n = max(2, int(np.floor(L / step)) + 1)
    dists = np.linspace(0, L, n, endpoint=False)
    return [line.interpolate(d) for d in dists]

def sample_polygon_boundary(poly, step):
    """Sample polygon exterior and holes at even spacing."""
    pts = []
    if poly.is_empty:
        return pts
    # exterior
    if poly.exterior:
        pts.extend(sample_line_evenly(poly.exterior, step))
    # interiors (holes)
    for ring in poly.interiors:
        pts.extend(sample_line_evenly(ring, step))
    return pts

for name in os.listdir(folder_path):
    if not name.lower().endswith(".shp"):
        continue

    in_path  = os.path.join(folder_path, name)
    out_path = os.path.join(out_dir, name)

    try:
        gdf = gpd.read_file(in_path)
        if gdf.crs is None:
            raise ValueError(f"{name}: layer has no CRS; reproject to a metric CRS.")

        # Densify boundaries -> points
        step = max(0.001, distance / 2.0)  # ensure >0
        rows = []
        for pid, geom in gdf.geometry.items():
            if geom is None or geom.is_empty:
                continue
            # handle MultiPolygons
            geoms = getattr(geom, "geoms", [geom])
            for part in geoms:
                for pt in sample_polygon_boundary(part, step):
                    rows.append({"poly_idx": pid, "geometry": pt})

        if not rows:
            print(f"{name} -> no geometries to process")
            continue

        pts_gdf = gpd.GeoDataFrame(rows, crs=gdf.crs)
        coords = np.column_stack([pts_gdf.geometry.x, pts_gdf.geometry.y])

        # DBSCAN: set min_samples=1 so single polygons are never dropped
        db = DBSCAN(eps=distance, min_samples=1).fit(coords)
        pts_gdf["cluster"] = db.labels_

        # Map clusters -> original polygons -> convex hull of union
        out_geoms = []
        for cid, frame in pts_gdf.groupby("cluster"):
            poly_ids = frame["poly_idx"].unique().tolist()
            union = unary_union(gdf.loc[poly_ids, "geometry"].tolist())
            out_geoms.append(union.convex_hull)

        result = gpd.GeoDataFrame(geometry=gpd.GeoSeries(out_geoms, crs=gdf.crs))

        # Optional: remove duplicates (can happen if two clusters collapse to same hull)
        result = result.dissolve().explode(index_parts=False).reset_index(drop=True)

        result.to_file(out_path, driver="ESRI Shapefile")
        print(f"{name} -> OK ({len(result)} cluster polygon(s))")

    except Exception as e:
        print(f"{name} FAILED: {e}")
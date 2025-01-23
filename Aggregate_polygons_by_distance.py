import geopandas as gpd
from sklearn.cluster import DBSCAN
from shapely import Point
import pandas as pd
from shapely.ops import unary_union
import os

#poly_path = r"D:\test\1_Cybinka_Jemiola_zaznaczenia.shp"
folder_path = input("Enter directory \n \n")

distance = 9

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
        except:
            print(f"{i} FAILED")
import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

root_folder = r"Y:\______Wody_Polskie\Dane\Geodeci\2_NW_Ostrzeszow\Kobyla_Gora\3_Roboczy\csv"

csv_files = [f for f in os.listdir(root_folder) if f.endswith(".csv")]

gdfs = []

for file in csv_files:
    file_path = os.path.join(root_folder, file)

    columns = ["id", "kod", "y", "x", "h", "time", "fix"]
    df = pd.read_csv(file_path)

    df.columns = columns
    
    geometry = [Point(xy) for xy in zip(df["x"], df["y"])]
    gdf = gpd.GeoDataFrame(df, geometry = geometry, crs = "EPSG:2180")
    gdfs.append(gdf)

merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index = True), crs = "EPSG:2180")

merged_gdf.to_file(os.path.join(root_folder, "out.shp"))
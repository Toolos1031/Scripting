import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

root_folder = r"Y:\______Wody_Polskie\Dane\Geodeci\4_NW_Trzebnica\2025_08_01_Trzebnica\csv"

csv_files = [f for f in os.listdir(root_folder) if f.endswith(".csv")]

gdfs = []

for file in csv_files:
    file_path = os.path.join(root_folder, file)

    df = pd.read_csv(file_path, header = None, delimiter = ",", encoding = "cp1250")
    
    gdf = pd.DataFrame(df)
    gdfs.append(gdf)

merged_gdf = pd.DataFrame(pd.concat(gdfs, ignore_index = True))

merged_gdf.to_csv(os.path.join(root_folder, "out.csv"))
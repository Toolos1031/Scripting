import laspy
import numpy as np
import geopandas as gpd
import os

input_path = r"D:\TerraSolid\chc\test\chc_linie_class_sub.las"
point_path = r"D:\TerraSolid\chc\poles\poles.shp"
output_path = r"D:\TerraSolid\chc\export\poles_class.las"
temp_path = r"D:\TerraSolid\chc\temp"

las = laspy.read(input_path)
shapefile = gpd.read_file(point_path)

a = 0

for index, rows in shapefile.iterrows():
    x = rows["geometry"].bounds[0]
    y = rows["geometry"].bounds[1]

    dim = 4
    xy = (las.x >= (x-dim)) & (las.x <= (x+dim)) & (las.y >= (y-dim)) & (las.y <= (y+dim))
    classi = las.classification == 5
    
    las.classification[(xy) & (classi)] = 11

    print(a)
    a += 1
    #name = os.path.join(temp_path, f"{a}.las")


las.write(output_path)
import laspy
import numpy as np
import geopandas as gpd
import os
from shapely.geometry import box

input_path = r"D:\Atlasus\Naloty\Dane\Dzien_5_6\kot-ser\Mateusz\4_Terra\9.las"
point_path = r"D:\Atlasus\Naloty\Dane\Dzien_5_6\poles.shp"
output_path = r"D:\Atlasus\Naloty\Dane\Dzien_5_6\kot-ser\Mateusz\5_Poles\9.las"


las = laspy.read(input_path)
shapefile = gpd.read_file(point_path)

a = 0

min_x, max_x = las.header.min[0], las.header.max[0]
min_y, max_y = las.header.min[1], las.header.max[1]

las_bbox = box(min_x, min_y, max_x, max_y)

filtered_shapefile = shapefile[shapefile.geometry.within(las_bbox)]

print(f"Filtering {len(filtered_shapefile)} poles")

for index, rows in filtered_shapefile.iterrows():
    x = rows["geometry"].bounds[0]
    y = rows["geometry"].bounds[1]

    dim = 4
    xy = (las.x >= (x-dim)) & (las.x <= (x+dim)) & (las.y >= (y-dim)) & (las.y <= (y+dim))
    classi = las.classification == 5
    
    las.classification[(xy) & (classi)] = 11

    print(a)
    a += 1


las.write(output_path)
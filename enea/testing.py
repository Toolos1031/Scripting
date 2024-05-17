import laspy
import numpy as np
import geopandas as gpd
import os

input_path = r"D:\TerraSolid\chc\chc_linie_class_sub.las"
point_path = r"D:\TerraSolid\chc\poles\poles.shp"
output_path = r"D:\TerraSolid\chc\export\poles_class.las"
temp_path = r"D:\TerraSolid\chc\temp"

las = laspy.read(input_path)

high_veg = las.classification == 5
veg = laspy.LasData(las.header)
veg.points = las.points[np.array(high_veg)]

the_rest = las.classification != 5
rest = laspy.LasData(las.header)
rest.points = las.points[np.array(the_rest)]

shapefile = gpd.read_file(point_path)

a = 0

for index, rows in shapefile.iterrows():
    x = rows["geometry"].bounds[0]
    y = rows["geometry"].bounds[1]

    dim = 4
    xy = (las.x >= (x-dim)) & (las.x <= (x+dim)) & (las.y >= (y-dim)) & (las.y <= (y+dim))
    classi = las.classification == 5
    """
    inside_points = (las.x >= (x-2)) & (las.x <= (x+2)) & (las.y >= (y-2)) & (las.y <= (y+2)) & (las.classification == 5)
    print(inside_points)
    inside = laspy.LasData(las.header)
    inside.points = las.points[np.array(inside_points)]
    """

    las.classification[(xy) & (classi)] = 11

    print(a)
    a += 1
    #name = os.path.join(temp_path, f"{a}.las")


las.write(output_path)
import laspy
import geopandas as gpd
import os
from shapely.geometry import box

directory = r"C:\Atlasus\Zur_jezewo"
poles = "14_zur_jezewo_poles_2000.shp"

input_path = os.path.join(directory, "4_Terra")
point_path = os.path.join(directory, "5_Poles", poles)
output_path = os.path.join(directory, "5_Poles")

def pole_class(scan):
    las_path = os.path.join(input_path, scan)

    las = laspy.read(las_path)
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

    las_out = os.path.join(output_path, scan)
    las.write(las_out)

for i in os.listdir(input_path):
    pole_class(i)
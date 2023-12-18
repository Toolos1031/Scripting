import laspy
import geopandas as gpd
import time
import os
from tqdm import tqdm

start = time.time()

def clip_las(las_file_path, shapefile_path, output_path):
    #read LAS file

    las = laspy.read(las_file_path)

    #read Shapefile
    shapefile = gpd.read_file(shapefile_path)

    for index, rows in tqdm(shapefile.iterrows(), total=len(shapefile)):
        
        x1 = rows['geometry'].bounds[0]
        x2 = rows['geometry'].bounds[2]
        y1 = rows['geometry'].bounds[1]
        y2 = rows['geometry'].bounds[3]
        
        
        inside = (las.x >= x1) & (las.x <= x2) & (las.y >= y1) & (las.y <= y2)
        inside_points = las.points[inside].copy()

        #print(f"Started clipping {index}.las")
        
        
        output_file = laspy.LasData(las.header)
        output_file.points = inside_points
        end = f"{index}.las"
        output = os.path.join(output_path, end)
        output_file.write(output)
        

las_file_path = r"D:\Spychowo\CLIPPING\flights.las"
shapefile_path = r"D:\Spychowo\CLIPPING\clip_6.shp"
output_path = r"D:\Spychowo\CLIPPING\out"

clip_las(las_file_path, shapefile_path, output_path)
end = time.time()
print("It took: ", end - start)

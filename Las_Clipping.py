import laspy
import geopandas as gpd
import time
import os
from tqdm import tqdm
import random

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

        print(type(inside_points))
        #print(f"Started clipping {index}.las")
        

        output_file = laspy.LasData(las.header)
        output_file.points = inside_points
        if output_file.header.point_count != 0:
            end = f"{index}.las"
            output = os.path.join(output_path, end)
            if os.path.exists(output):
                number = random.randint(1, 40)
                end = f"{index}dupl{number}.las"
                output = os.path.join(output_path, end)
                output_file.write(output)
            else:
                output_file.write(output)
        else:
            print("EMPTY")


las_file_path = r"D:\DJI Terra\PCGSPRO_1699970954\bzbuas.zlecenia@gmail.com\Razem\lidars\terra_las\15.las"
shapefile_path = r"D:\Kolej\las clipping\clip.shp"
output_path = r"D:\Kolej\las clipping\out"

clip_las(las_file_path, shapefile_path, output_path)
end = time.time()
print("It took: ", end - start)

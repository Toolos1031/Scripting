import laspy
import os

input_path = r"D:\TerraSolid\atlasus\out\2\out"
output_path = r"D:\TerraSolid\atlasus\out\out"

all_files = []

for file in os.listdir(input_path):
    if file.endswith(".las"):
        all_files.append(file)

for file1 in all_files:
    path = os.path.join(input_path, file1)
    output = os.path.join(output_path, file1)
    las = laspy.read(path)

    roads = las.classification == 11
    road_points = las.points[roads].copy()

    new_file = laspy.LasData(las.header)
    new_file.points = road_points

    output = os.path.join(output_path, file1)

    new_file.write(output)
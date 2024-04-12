import laspy
import os
import CSF
import numpy as np
import subprocess

input_path = r"D:\Atlasus\2_Agi_export\export"
output_path = r"D:\Atlasus\3_ground_class"

all_files = []

def classify(cloud):
    las = laspy.read(cloud)
    points = las.points
    xyz = np.vstack((las.x, las.y, las.z)).transpose()

    csf = CSF.CSF()

    csf.params.bSloopSmooth = True
    csf.params.cloth_resolution = 0.5
    csf.params.iterations = 500
    csf.params.class_threshold = 0.5

    csf.setPointCloud(xyz)
    ground = CSF.VecInt()
    non_ground = CSF.VecInt()

    csf.do_filtering(ground, non_ground)

    ground_las = laspy.LasData(las.header)
    ground_las.points = points[np.array(ground)]

    non_ground_las = laspy.LasData(las.header)
    non_ground_las.points = points[np.array(non_ground)]

    ground_las.classification[:] = 2
    non_ground_las.classification[:] = 1

    return ground_las, non_ground_las

for file in os.listdir(input_path):
    if file.endswith(".las"):
        all_files.append(file)

for file1 in all_files:
    path = os.path.join(input_path, file1)
    output = os.path.join(output_path, file1)
    las = laspy.read(path)

    roads = las.classification == 11
    road_points = laspy.LasData(las.header)
    road_points = las.points[roads].copy()

    rest = las.classification != 11
    rest_points = laspy.LasData(las.header)
    rest_points = las.points[rest].copy()

    rest.classification[:] = 0

    ground, non_ground = classify(rest)

    ground.classification[:] = 2
    non_ground.classification[:] = 1

    roads.write("D:\Atlasus\3_ground_class\temp")

    i1 = ""
    i2
    i3

    cmd = "las2las -i 
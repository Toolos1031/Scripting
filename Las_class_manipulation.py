import laspy
import os
import CSF
import numpy as np
import subprocess

input_path = r"D:\Atlasus\2_Agi_export\export"
output_path = r"D:\Atlasus\3_ground_class"

all_files = []

def classify(cloud):
    print("STARTED CLASSIFING")
    
    print(cloud.header)

    xyz = np.vstack((cloud.x, cloud.y, cloud.z)).transpose()

    csf = CSF.CSF()

    csf.params.bSloopSmooth = True
    csf.params.cloth_resolution = 0.5
    csf.params.iterations = 500
    csf.params.class_threshold = 0.5

    csf.setPointCloud(xyz)
    ground = CSF.VecInt()
    non_ground = CSF.VecInt()

    csf.do_filtering(ground, non_ground)

    print(ground)

    ground_las = laspy.LasData(cloud.header)
    ground_las.points = cloud.points[np.array(ground)]

    non_ground_las = laspy.LasData(cloud.header)
    non_ground_las.points = cloud.points[np.array(non_ground)]

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
    print(las.header)
    print("IMPORTED LAS")

    roads = (las.classification == 11)
    road = laspy.LasData(las.header)
    #road.points = las.points[roads].copy()
    road.points = las.points[np.array(roads)]
    print("FILTERED ROADS")

    the_rest = (las.classification != 11)
    rest = laspy.LasData(las.header)
    #rest.points = las.points[the_rest].copy()
    rest.points = las.points[np.array(the_rest)]
    print(rest.header)
    print("FILTERED REST")


    rest.classification[:] = 0
    ground, non_ground = classify(rest)

    ground.classification[:] = 2
    non_ground.classification[:] = 1

    r = r"D:\Atlasus\3_ground_class\temp\roads.las"
    g = r"D:\Atlasus\3_ground_class\temp\ground.las"
    ng = r"D:\Atlasus\3_ground_class\temp\non_ground.las"

    road.write(r)
    ground.write(g)
    non_ground.write(ng)

    cmd = f"las2las -i {r} {g} {ng} -merged -o {output}"

    os.popen(cmd)

    #os.remove(r)
    #os.remove(g)
    #os.remove(ng)
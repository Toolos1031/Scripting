import laspy
import os
import CSF
import numpy as np
import subprocess

#input_path = r"D:\Atlasus\2_Agi_export\export"
#output_path = r"D:\Atlasus\3_ground_class"

directory = r"C:\Atlasus\zur_laskowice"

input_path = os.path.join(directory, "2_Agi_Export\Export")
output_path = os.path.join(directory, "3_Ground")

all_files = []

fraction = 0.30

def classify(cloud):
    print("STARTED CLASSIFING")
    
    print(cloud.header)

    xyz = np.vstack((cloud.x, cloud.y, cloud.z)).transpose()

    csf = CSF.CSF()

    csf.params.bSloopSmooth = False
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
    road.classification[:] = 14


    total_points = len(ground.points)
    sample_size = int(total_points * fraction)

    random_indices = np.random.choice(total_points, sample_size, replace = False)

    subsampled_points = ground.points[random_indices]

    subsampled_ground = laspy.LasData(las.header)
    subsampled_ground.points = subsampled_points


    #r = r"D:\Atlasus\3_ground_class\temp\roads.las"
    #g = r"D:\Atlasus\3_ground_class\temp\ground.las"
    #ng = r"D:\Atlasus\3_ground_class\temp\non_ground.las"

    r = os.path.join(directory, r"3_Ground\temp\roads.las")
    g = os.path.join(directory, r"3_Ground\temp\ground.las")
    ng = os.path.join(directory, r"3_Ground\temp\non_ground.las")

    road.write(r)
    subsampled_ground.write(g)
    non_ground.write(ng)

    #ground.write(g)

    cmd = f"las2las -i {r} {g} {ng} -merged -o {output}"

    os.popen(cmd)

    #os.remove(r)
    #os.remove(g)
    #os.remove(ng)
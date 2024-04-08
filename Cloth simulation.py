import laspy
import numpy as np
import CSF
import os

input_path = r"D:\TerraSolid\atlasus"
out = r"D:\TerraSolid\atlasus\out\2"

all_files = []

for file in os.listdir(input_path):
    all_files.append(file)

for file in all_files:
    name = os.path.join(input_path, file)

    las = laspy.read(name)
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

    split = os.path.splitext(file)
    ground_out = f"{split[0]}_ground.las"
    non_ground_out = f"{split[0]}_non_ground.las"

    out1 = os.path.join(out, ground_out)
    out2 = os.path.join(out, non_ground_out)
    
    ground_las.write(out1)
    non_ground_las.write(out2)

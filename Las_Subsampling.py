import laspy
import os
import numpy as np

input_path = r"D:\Kolej\las clipping\Classified"
output_path = r"D:\Kolej\las clipping\subsampled2"

fraction = 0.4

all_files = []

for file in os.listdir(input_path):
    all_files.append(file)

for file in all_files:
    name = os.path.join(input_path, file)

    las = laspy.read(name)

    total_points = len(las.points)
    sample_size = int(total_points * fraction)

    random_indices = np.random.choice(total_points, sample_size, replace=False)

    subsampled_points = las.points[random_indices]

    subsampled_las = laspy.LasData(las.header)
    subsampled_las.points = subsampled_points

    output = os.path.join(output_path, file)

    subsampled_las.write(output)
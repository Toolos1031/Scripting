import laspy
import os
import numpy as np

input_path = r"C:\Atlasus\Zur_jezewo\wip"
output_path = r"C:\Atlasus\Zur_jezewo\wip"

fraction = 0.4

all_files = []

#2 i 14
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

    out_name = "sub" + file

    output = os.path.join(output_path, out_name)

    subsampled_las.write(output)
import laspy
import numpy as np
from collections import defaultdict
from tqdm import tqdm
import os

root_folder = r"D:\___WodyPolskie\3_Milicz\przetwarzanie"

las_folder = os.path.join(root_folder, "las")
sample_folder = os.path.join(root_folder, "sampled")

folder_list = [las_folder, sample_folder]


def check_root():
    if os.path.isdir(root_folder): # Check if the root path, and other dirs exits
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder): # If not we can create them
                os.mkdir(folder)
                print(f"Created folder for {name}")
            else:
                print(f"Folder for {name} found")
    else:
        input("Root folder does not exist, PRESS ENTER TO EXIT") # When missing the root folder, exit
        raise SystemExit(0)


def process_scans(x, y):
    # Floor coordinates to create 1x1 m tile indices
    tile_x = np.floor(x).astype(int)
    tile_y = np.floor(y).astype(int)

    # Build a mapping from (tile_x, tile_y) to point indices 
    tile_index_dict = defaultdict(list)
    for i, (tx, ty) in enumerate(zip(tile_x, tile_y)):
        tile_index_dict[(tx, ty)].append(i)


    max_pts_per_tile = 100
    sampled_indices = []

    for indices in tqdm(tile_index_dict.values(), desc = "Downsampling"):
        if len(indices) > max_pts_per_tile:
            sampled_indices.extend(np.random.choice(indices, max_pts_per_tile, replace = False))
        else:
            sampled_indices.extend(indices)

    sampled_indices = np.array(sampled_indices)

    return sampled_indices

def main_work(scan):
    scan_file = os.path.join(las_folder, scan)
    las = laspy.read(scan_file)

    ground_only = las.classification == 2 # Take only the ground and create a new entity
    ground = laspy.LasData(las.header)
    ground.points = las.points[np.array(ground_only)]

    x, y = ground.x, ground.y

    sampled_indices = process_scans(x, y)

    downsampled_ground_points = ground.points[sampled_indices].array

    non_ground_only = las.classification != 2 # Take only the ground and create a new entity
    non_ground = laspy.LasData(las.header)
    non_ground.points = las.points[np.array(non_ground_only)]

    x, y = non_ground.x, non_ground.y

    sampled_indices = process_scans(x, y)

    non_ground_points = non_ground.points[sampled_indices].array

    combined_array = np.concatenate((downsampled_ground_points, non_ground_points))
    combined_points = laspy.ScaleAwarePointRecord(
        combined_array,
        las.header.point_format,
        las.header.scales,
        las.header.offsets
    )

    new_las = laspy.LasData(las.header)
    new_las.points = combined_points

    out_file = os.path.join(sample_folder, scan)
    new_las.write(out_file)

if __name__ == "__main__":
    check_root()
    las_files = [f for f in os.listdir(las_folder) if f.endswith(".las")]

    for scan in tqdm(las_files, total = len(las_files), desc = "Iterating over files"):
        main_work(scan)

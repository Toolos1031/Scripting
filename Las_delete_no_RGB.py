import laspy
import numpy as np
import os
from tqdm import tqdm

scan_folder = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\Sosnie\scans"
out_folder = os.path.join(scan_folder, "No_RGB")

if not os.path.isdir(out_folder):
    os.makedirs(out_folder, exist_ok = True)

scans = [f for f in os.listdir(scan_folder) if f.endswith(".las")]

for scan in tqdm(scans, total = len(scans)):
    scan_path = os.path.join(scan_folder, scan)
    scan_out = os.path.join(out_folder, scan)

    las = laspy.read(scan_path)

    points = np.vstack((las.x, las.y)).T

    red = las.red
    blue = las.blue
    green = las.green


    mask = (red != 0) | (blue != 0) | (green != 0)

    color_only = (red != 0) & (blue != 0) & (green != 0)
    colored_points = las.points[color_only].copy()
    color = laspy.LasData(las.header)
    color.points = colored_points

    color.write(scan_out)

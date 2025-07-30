import laspy
import numpy as np
import alphashape
import geopandas as gpd
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

root_folder = r"D:\1111Przetwarzanie\JOINING\sampled"
las_files = [os.path.join(root_folder, f) for f in os.listdir(root_folder) if f.endswith(".las")]

"""
for dirpath, dirnames, filenames in os.walk(root_folder):
    for file in filenames:
        if file.lower().endswith(".las"):
            print(file)
            full_path = os.path.join(dirpath, file)
            las_files.append(full_path)
"""
def process_scan(scan):
    file = os.path.split(scan)[1]
    print(f"sampling {file}")
    out_folder = os.path.join(root_folder, "outline_new")

    las = laspy.read(scan)
    points = np.vstack((las.x, las.y)).T

    sample_size = int(points.shape[0] * 0.001)

    subsample = np.random.choice(points.shape[0], size = sample_size, replace = False)

    sample = points[subsample]

    alpha = 0.05
    hull = alphashape.alphashape(sample, alpha) 

    file_start = file.split(".")[0]
    file_shp = file_start + ".shp"

    out = os.path.join(out_folder, file_shp)
    try:
        gdf = gpd.GeoDataFrame(geometry = [hull], crs = "EPSG:2180")
        gdf.to_file(out)
    except:
        print(f"skipped {file_shp}")

def main():
    with ProcessPoolExecutor(max_workers = 15) as executor:
        executor.map(process_scan, las_files)

if __name__ == "__main__":
    main()

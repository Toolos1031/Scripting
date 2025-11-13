import laspy
import numpy as np
import alphashape
import geopandas as gpd
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor

root_folder = r"E:\Krotoszyn_Chmury"
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
    out_folder = os.path.join(root_folder, "outline")

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
    with ProcessPoolExecutor(max_workers = 10) as executor:
        futures = {executor.submit(process_scan, scan): scan for scan in las_files}

        for future in tqdm(as_completed(futures), total = len(futures), desc = "Calculating outline"):
            fname = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"Worker failed on outline for {fname}: {e}")

if __name__ == "__main__":
    main()

import os
from osgeo import gdal
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil

root_folder = r"D:\1111Przetwarzanie\JOINING_TIF\naprawa\joined_tif"
old_folder = r"D:\1111Przetwarzanie\JOINING_TIF\raw\together"
#old_folder = os.path.join(root_folder, "old")
merged_folder = r"D:\1111Przetwarzanie\JOINING_TIF\naprawa\merged"
#merged_folder = os.path.join(root_folder, "merged")

gdal.TermProgress = gdal.TermProgress_nocb

files = [f for f in os.listdir(root_folder) if f.endswith(".tif")]

def merge_clouds(file, file_list, out):

    print(f"Merging {file}")

    warp_options = gdal.WarpOptions(
        format = "GTiff",
        multithread = True,
        creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES"],
        warpOptions = ["NUM_THREADS=5"],
        dstSRS = "EPSG:2180",
        callback = gdal.TermProgress
    )

    warp = gdal.Warp(out, file_list, options = warp_options)
    warp = None


def main():
    futures = []
    with ProcessPoolExecutor(max_workers = 10) as executor:
        for file in files:
            file_list = []
            if os.path.isfile(os.path.join(old_folder, file)):
                f1 = os.path.join(root_folder, file)
                f2 = os.path.join(old_folder, file)

                file_list.append(f1)
                file_list.append(f2)

                out = os.path.join(merged_folder, file)
                futures.append(executor.submit(merge_clouds, file, file_list, out))
            else:
                shutil.copyfile(os.path.join(root_folder, file), os.path.join(os.path.join(merged_folder, file)))

        for f in tqdm(as_completed(futures), total = len(futures), desc = "Merging"):
            f.result()

if __name__ == "__main__":
    main()
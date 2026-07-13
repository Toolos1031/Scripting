import os
from osgeo import gdal
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import shutil

root_folder = r"D:\___WodyPolskie\clipping_rastry\Krotoszyn\out"
old_folder = r"D:\___WodyPolskie\clipping_rastry\wypelnianie\joined_tif"
#old_folder = os.path.join(root_folder, "old")
merged_folder = r"D:\___WodyPolskie\clipping_rastry\Krotoszyn\wypelnione2"
#merged_folder = os.path.join(root_folder, "merged")

files = [f for f in os.listdir(root_folder) if f.endswith(".tif")]

def merge_tiffs(file, file_list, out):

    print(f"Merging {file}")

    ref_path = file_list[0]
    ref_ds = gdal.Open(ref_path, gdal.GA_ReadOnly)
    if ref_ds is None:
        raise RuntimeError(f"Failed to open reference dataset: {ref_path}")
    
    gt = ref_ds.GetGeoTransform()
    xres = abs(gt[1])
    yres = abs(gt[5])

    xmin = gt[0]
    ymax = gt[3]
    xmax = xmin + ref_ds.RasterXSize * xres
    ymin = ymax - ref_ds.RasterYSize * yres

    ref_ds = None

    warp_options = gdal.WarpOptions(
        format = "GTiff",
        multithread = True,
        creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES"],
        warpOptions = ["NUM_THREADS=5"],
        dstSRS = "EPSG:2180",

        xRes = xres,
        yRes = yres,
        outputBounds = (xmin, ymin, xmax, ymax),
        srcNodata = 0,
    )

    warp = gdal.Warp(out, file_list, options = warp_options)
    warp = None


def main():
    futures = []
    with ProcessPoolExecutor(max_workers = 10) as executor:
        for file in files:
            file_list = []

            f1 = os.path.join(root_folder, file)
            f2 = os.path.join(old_folder, file)

            if os.path.isfile(f2):

                file_list.append(f1)
                file_list.append(f2)

                out = os.path.join(merged_folder, file)
                futures.append(executor.submit(merge_tiffs, file, file_list, out))

            else:
                file_list.append(f1)

                out = os.path.join(merged_folder, file)
                futures.append(executor.submit(merge_tiffs, file, file_list, out))

        for f in tqdm(as_completed(futures), total = len(futures), desc = "Merging"):
            f.result()

if __name__ == "__main__":
    main()
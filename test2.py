import os
import shutil
from osgeo import gdal
from concurrent.futures import ProcessPoolExecutor, as_completed

# ==== CONFIGURATION ====
folder1 = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\__Przycinanie_godlo\joined_tif\1"
folder2 = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\__Przycinanie_godlo\joined_tif\2"
output_folder = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\__Przycinanie_godlo\joined_tif"
max_workers = 8  # Adjust based on your hardware


# Collect TIFFs
tifs1 = {f for f in os.listdir(folder1) if f.endswith(".tif")}
tifs2 = {f for f in os.listdir(folder2) if f.endswith(".tif")}

all_files = tifs1.union(tifs2)
common_files = tifs1.intersection(tifs2)


def handle_file(filename):
    path1 = os.path.join(folder1, filename)
    path2 = os.path.join(folder2, filename)
    output_path = os.path.join(output_folder, filename)

    try:
        if filename in common_files:
            print(f"Merging: {filename}")
            warp_options = gdal.WarpOptions(
                format="GTiff",
                multithread=True,
                creationOptions=["COMPRESS=DEFLATE", "BIGTIFF=YES", "TILED=YES"],
                dstSRS = "EPSG:2180",
                warpOptions=["NUM_THREADS=5"]
            )
            warp = gdal.Warp(output_path, [path1, path2], options=warp_options)
            warp = None

        elif filename in tifs1:
            print(f"Copying from folder1: {filename}")
            shutil.copyfile(path1, output_path)

        elif filename in tifs2:
            print(f"Copying from folder2: {filename}")
            shutil.copyfile(path2, output_path)

        return f"✅ Done: {filename}"

    except Exception as e:
        return f"❌ Error processing {filename}: {e}"


if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(handle_file, fname) for fname in all_files]
        for f in as_completed(futures):
            print(f.result())

    print("✅ All files merged or copied.")
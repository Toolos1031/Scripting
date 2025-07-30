import os
from osgeo import gdal
from tqdm import tqdm
import laspy
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

root_folder = r"D:\1111Przetwarzanie\joined"
#old_folder = os.path.join(root_folder, "old")
old_folder = r"D:\1111Przetwarzanie\JOINING\sampled"
merged_folder = os.path.join(root_folder, "merged")

gdal.TermProgress = gdal.TermProgress_nocb

files = [f for f in os.listdir(root_folder) if f.endswith(".las")]

def merge_clouds(file, file_list, out):

    print(f"Merging {file}")

    cmd = ['lasmerge', '-i'] + file_list + ['-o', out]
    subprocess.run(cmd)

def main():
    futures = []
    with ProcessPoolExecutor(max_workers = 10) as executor:
        for file in files:
            file_list = []
            f1 = os.path.join(root_folder, file)
            f2 = os.path.join(old_folder, file)

            file_list.append(f1)
            file_list.append(f2)

            out = os.path.join(merged_folder, file)
            futures.append(executor.submit(merge_clouds, file, file_list, out))

        for f in tqdm(as_completed(futures), total = len(futures), desc = "Merging"):
            f.result()

if __name__ == "__main__":
    main()
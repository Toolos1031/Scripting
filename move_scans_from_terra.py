import os
import shutil
from tqdm import tqdm

terra_folder = r"C:\Terra\PCGSPRO_1722851465\bzbuas.zlecenia@gmail.com"
dest_folder = r"C:\__Wody_Polskie\las"
raw_file = "cloud_merged.las"

folders = [f for f in os.listdir(terra_folder) if os.path.isdir(os.path.join(terra_folder, f))]

inside_folder = r"lidars\terra_las"

for i in tqdm(folders, total = len(folders)):
    try:
        las_folder = os.path.join(terra_folder, i, inside_folder)

        raw_scan = os.path.join(las_folder, raw_file)
        changed_file = os.path.join(las_folder, i + ".las")
        file = i + ".las"

        dest_file = os.path.join(dest_folder, file)

        os.rename(raw_scan, changed_file)

        print(f"Name changed {i}")

        shutil.copyfile(changed_file, dest_file)
    except Exception as e:
        print(f"Failed for file {i}: {e}")
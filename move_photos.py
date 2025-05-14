import os
import shutil
from tqdm import tqdm

root_path = r"Y:\______Wody_Polskie\Dane\Naloty\Surowe_Dane\Ostrzeszów\Przygodzice"
dst_path = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\photo"

folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]

for folder in tqdm(folders, total = len(folders)):
    src_folder = os.path.join(root_path, folder)
    dst_folder = os.path.join(dst_path, folder)

    os.makedirs(dst_folder, exist_ok = True)

    for file in tqdm(os.listdir(src_folder), total = len(os.listdir(src_folder))):
        if file.endswith(".JPG"):
            src_file_path = os.path.join(src_folder, file)
            dst_file_path = os.path.join(dst_folder, file)

            shutil.copy2(src_file_path, dst_file_path)

print(input("AAAA"))
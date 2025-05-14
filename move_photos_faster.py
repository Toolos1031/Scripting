import os
from tqdm import tqdm
import shutil

#root_path = r"Y:\______Wody_Polskie\Dane\Naloty\Surowe_Dane\Ostrzeszów\Mikstat"
#dst_path = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\photo\Mikstat"
root_path = input("SRC DIR")
dst_path = input("DST DIR")

folders = [f for f in os.listdir(root_path) if os.path.isdir(os.path.join(root_path, f))]

for folder in tqdm(folders, total = len(folders)):
    src_folder = os.path.join(root_path, folder)
    dst_folder = os.path.join(dst_path, folder)

    os.makedirs(dst_folder, exist_ok = True)

    files = [f for f in os.listdir(src_folder) if f.endswith(".JPG")]

    for file in tqdm(files, total = len(files)):
        try:
            shutil.copy2(os.path.join(src_folder, file), os.path.join(dst_folder, file))
        except:
            print(f"Failed to move: {file}")

print(input("AAAA"))
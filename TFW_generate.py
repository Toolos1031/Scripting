import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import subprocess


folder_path = r"D:\LK310\GOTOWE\Ortofotomapa"
target_folder = r"D:\LK310\GOTOWE\Ortofotomapa\converted"

 

files = [f for f in os.listdir(folder_path) if f.endswith(".tif")]


def convert(file):
    source = os.path.join(folder_path, file)
    target = os.path.join(target_folder, file)

    cmd = f'gdal_translate -of Gtiff -co "TFW=YES" "{source}" "{target}"'
    subprocess.run(cmd, shell = True, check = True)

if __name__ == "__main__":

    with ThreadPoolExecutor(max_workers = 5) as executor:
        futures = [executor.submit(convert, file) for file in files]

        for f in tqdm(as_completed(futures), total = len(futures), desc = "Converting"):
            f.result()

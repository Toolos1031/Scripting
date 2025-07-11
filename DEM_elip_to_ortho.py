import os
import subprocess
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor


folder = r"W:\ROBOCZY\3_NW_Milicz\NMT\zmigrod"
out_folder = os.path.join(folder, "geo")

os.makedirs(out_folder, exist_ok = True)


dem_files = [f for f in os.listdir(folder) if f.endswith("tif")]

gdalwarp_path = r"C:\Program Files\QGIS 3.34.9\bin\gdalwarp.exe"

def process_raster(file):
    input = os.path.join(folder, file)
    output = os.path.join(out_folder, file)

    cmd = [
        gdalwarp_path,
        "-t_srs", "EPSG:2180+9651",
        "-co", "COMPRESS=LZW", "-co", "PREDICTOR=2",
        input,
        output
    ]

    subprocess.run(cmd, shell = True, check = True)


def main():
    with ProcessPoolExecutor(max_workers = 10) as executor:
        executor.map(process_raster, dem_files)

if __name__ == "__main__":
    main()
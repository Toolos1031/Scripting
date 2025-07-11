import geopandas as gpd
import os
from tqdm import tqdm
import requests

folder = r"D:\___WodyPolskie\NMT\2"

shp = os.path.join(folder, "do_pobrania_2023.shp")

out_folder = os.path.join(folder, "out")

shapefile = gpd.read_file(shp)

ulrs = []

for rows, cols in shapefile.iterrows():
    ulrs.append(cols["url_do_pob"])

for url in tqdm(ulrs, total = len(ulrs)):
    filename = os.path.basename(url)
    out_path = os.path.join(out_folder, filename)

    try:
        response = requests.get(url, stream = True, timeout = 60)
        response.raise_for_status()

        with open(out_path, "wb") as f:
            for chunk in response.iter_content(chunk_size = 8192):
                f.write(chunk)

    except Exception as e:
        print(f"Failed to download {filename}")
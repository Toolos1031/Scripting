import geopandas as gpd
import os
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

folder = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie"

shp = os.path.join(folder, "url.gpkg")

out_folder = os.path.join(folder, "pobrane")

shapefile = gpd.read_file(shp)

ulrs = []

downloaded = [f for f in os.listdir(r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\pobrane")]
print(downloaded)

for rows, cols in shapefile.iterrows():
    ulrs.append(cols["url"])

def download(url):
    filename = os.path.basename(url)
    out_path = os.path.join(out_folder, filename)

    if filename not in downloaded:
        try:
            response = requests.get(url, stream = True, timeout = 60)
            response.raise_for_status()

            with open(out_path, "wb") as f:
                for chunk in response.iter_content(chunk_size = 8192):
                    f.write(chunk)

        except Exception as e:
            print(f"Failed to download {filename}")

def main():

    with ThreadPoolExecutor(max_workers = 60) as executor:

        futures = []

        for url in ulrs:
            futures.append(executor.submit(download, url))

        for f in tqdm(as_completed(futures), total = len(ulrs), desc = "Downloading"):
            f.result()

main()
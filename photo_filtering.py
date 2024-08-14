import pandas as pd
import os
import shutil
from tqdm import tqdm

photo_path = r"C:\Atlasus\ZDJECIA\zur_jezewo\MAP"
log_path = r"C:\Atlasus\ZDJECIA\zur_jezewo\gpslog_MAP.txt"
sorted_path = r"C:\Atlasus\ZDJECIA\zur_jezewo\MAP_SORTED"

columns = ["Filename", "Easting", "Northing", "H-MSL", "Roll", "Pitch", "Heading"]
log = pd.read_csv(log_path, sep = ";", header = None, skiprows = 4)
log.columns = columns
log["Filename"] = log["Filename"] + ".jpg"

photos = log["Filename"].tolist()
in_list = [f for f in os.listdir(photo_path) if f in photos]

for i in tqdm(in_list, total = len(in_list)):
    unsorted = os.path.join(photo_path, i)
    sorted = os.path.join(sorted_path, i)

    shutil.copyfile(unsorted, sorted)









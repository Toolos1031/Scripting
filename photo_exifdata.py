from GPSPhoto import gpsphoto
from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point
from tqdm import tqdm


folder = Path(r"V:\ROBOCZY\7_NW_Krotoszyn\surowe - naloty")

images = [str(p.resolve()) for p in folder.rglob("*") if p.is_file()]

geometries = []
paths = []

for image in tqdm(images, total = len(images)):
    if image.endswith(".JPG"):

        data = gpsphoto.getGPSData(image)

        paths.append(image)
        geometries.append(Point(data["Longitude"], data["Latitude"]))

input_data = {"paths": paths, "geometry": geometries}
gdf = gpd.GeoDataFrame(input_data, crs = "EPSG:4326")
gdf.to_file(r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\foto_2.shp")
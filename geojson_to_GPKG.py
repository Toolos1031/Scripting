import json
import geopandas as gpd

path = r"D:\___WodyPolskie\POWIERZCHNIA_CHMUR\KROTOSZYN\KROTOSZYN_footprint_control.geojson"

# 1) Check that it’s valid JSON
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)   # <-- if this fails, the file is malformed JSON

# 2) Build GeoDataFrame from features
gdf = gpd.GeoDataFrame.from_features(data["features"])
gdf = gdf.set_crs(epsg=2180)

gdf.to_file(r"D:\___WodyPolskie\POWIERZCHNIA_CHMUR\KROTOSZYN\KROTOSZYN_footprint_control.gpkg", driver = "GPKG")
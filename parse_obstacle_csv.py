import geopandas as gpd
import math

gdf = gpd.read_file(r"C:\Users\bartosz.skrabanek\Downloads\obstacles.csv", encoding = "utf-8")


def dmm_to_dd(coord_str):

    value = coord_str[:-1]
    degrees = float(value.split(".")[0]) // 100
    minutes = float(value.split(".")[0]) % 100 + float("0." + value.split(".")[1])

    decimal_deg = degrees + (minutes / 60)

    return decimal_deg

new_data_for_gdf = {}

for rows, cols in gdf.iterrows():
    latitude = dmm_to_dd(cols["lat"])
    longitude = dmm_to_dd(cols["lon"])

    new_data_for_gdf[rows] = {
        "description" : cols["desc"],
        "latitude" : latitude,
        "longitude" : longitude,
        "elevation" : cols["elev"]
    }

new_gdf = gpd.GeoDataFrame.from_dict(new_data_for_gdf, orient = "index")
new_gdf["geometry"] = gpd.points_from_xy(new_gdf["longitude"], new_gdf["latitude"])
new_gdf.set_crs("EPSG:4326", inplace = True)
new_gdf.to_file(r"C:\Users\bartosz.skrabanek\Downloads\obstacles.shp")
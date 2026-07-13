import geopandas as gpd
import math

gdf = gpd.read_file(r"D:\przeszkody\obstacles2.csv", encoding = "utf-8", sep = ";")


def dmm_to_dd(coord_str):
    try:
        value = coord_str[:-1]
        print(value)
        degrees = float(value.split(".")[0]) // 10000
        minutes = float(value.split(".")[0]) // 100 - (degrees * 100)
        seconds = float(value.split(".")[0][-2:])
        #minutes = float(value.split(".")[0]) % 100 + float("0." + value.split(".")[1])

        print(f"Degrees: {degrees}, Minutes: {minutes}, Seconds: {seconds}")

        decimal_deg = degrees + (minutes / 60) + (seconds / 3600)

        return decimal_deg
    
    except:
        print(f"Error converting coordinate: {coord_str}")
        coord_str = float(coord_str) + 0.001
        value = str(coord_str)[:-1]
        print(f"New value: {value}")
        degrees = float(value.split(".")[0]) // 10000
        minutes = float(value.split(".")[0]) // 100 - (degrees * 100)
        seconds = float(value.split(".")[0][-2:])
        #minutes = float(value.split(".")[0]) % 100 + float("0." + value.split(".")[1])

        decimal_deg = degrees + (minutes / 60) + (seconds / 3600)

        return decimal_deg


new_data_for_gdf = {}

for rows, cols in gdf.iterrows():
    latitude = dmm_to_dd(cols["lat"])
    longitude = dmm_to_dd(cols["lon"])

    new_data_for_gdf[rows] = {
        "desc" : cols["desc"],
        "lat" : latitude,
        "lon" : longitude,
        "elev" : cols["elev"]
    }

new_gdf = gpd.GeoDataFrame.from_dict(new_data_for_gdf, orient = "index")
new_gdf["geometry"] = gpd.points_from_xy(new_gdf["lon"], new_gdf["lat"])
new_gdf.set_crs("EPSG:4326", inplace = True)
new_gdf.to_file(r"D:\przeszkody\obstacles.shp")
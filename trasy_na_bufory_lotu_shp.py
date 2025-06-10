import os
import geopandas as gpd


root_folder = r"Y:\______Wody_Polskie\Dane\Naloty\Trasy\1_NW_Gora"
out_folder = r"Y:\______Wody_Polskie\Dane\Naloty\Trasy\1_NW_Gora\__Calosc"

kml_files = []

for dirpath, dirnames, filenames in os.walk(root_folder):
    for file in filenames:
        if file.lower().endswith(".kml"):
            full_path = os.path.join(dirpath, file)
            kml_files.append(full_path)


for file in kml_files:
    kml = gpd.read_file(file, driver = "KML")
    kml = kml.to_crs(epsg = 2180)

    kml["geometry"] = kml.buffer(100)
    kml["geometry"] = kml["geometry"].simplify(tolerance = 2)
    kml = kml[["geometry"]]

    out_file = os.path.split(file)[1].split(".")[0] + ".shp"
    out_path = os.path.join(out_folder, out_file)

    kml.to_file(out_path, driver = "ESRI Shapefile")
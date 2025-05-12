import geopandas as gpd
from shapely.geometry import Point
import os

columns = ["what", "id", "oznaczenie", "distance", "angle", "full_name", "Left X", "Left Y", "Left Z", "Mid X", "Mid Y", "Mid Z", "Right X", "Right Y", "Right Z", "Comment", "Mean X", "Mean Y", "RGS X", "RGS Y", "RGS Z", "RDS X", "RDS Y", "RDS Z", "RD X", "RD Y", "RD Z", "RDS_X", "RDS_Y", "RDS_Z", "RGS_X", "RGS_Y", "RGS_Z"]

csv_folder = r"D:\___WodyPolskie\Gora\geodeci\01_02.04.2025\przygotowane_dane\csv"
csv_files = [csv for csv in os.listdir(csv_folder) if csv.endswith(".csv")]

skipped = []
records = []
file = []

for csv_file in csv_files:
    csv_path = os.path.join(csv_folder, csv_file)

    data = gpd.read_file(csv_path, columns = columns)

    for cols, rows in data.iterrows():
        if rows["Comment"] == "Completed":
            kod = "RGS"
            point = Point(rows["RGS X"], rows["RGS Y"], rows["RGS Z"])
            records.append({"id": rows["what"], "KOD": kod, "geometry": point})
            
            kod = "RDS"
            point = Point(rows["RDS X"], rows["RDS Y"], rows["RDS Z"])
            records.append({"id": rows["what"], "KOD": kod, "geometry": point})

            kod = "RD"
            point = Point(rows["RD X"], rows["RD Y"], rows["RD Z"])
            records.append({"id": rows["what"], "KOD": kod, "geometry": point})

            kod = "RDS"
            point = Point(rows["RDS_X"], rows["RDS_Y"], rows["RDS_Z"])
            records.append({"id": rows["what"], "KOD": kod, "geometry": point})

            kod = "RGS"
            point = Point(rows["RGS_X"], rows["RGS_Y"], rows["RGS_Z"])
            records.append({"id": rows["what"], "KOD": kod, "geometry": point})

            point = Point(rows["RD X"], rows["RD Y"])
            file.append({"id": rows["what"], "geometry": point})

        if rows["Comment"] == "Skipped":
            point_skipped = Point(rows["Mean X"], rows["Mean Y"])
            skipped.append({"id": rows["what"], "geometry": point_skipped})



measured_shape = gpd.GeoDataFrame(records, crs = "EPSG:2180")
skipped_shape = gpd.GeoDataFrame(skipped, crs = "EPSG:2180")
gps_shape = gpd.GeoDataFrame(file, crs = "EPSG:2180")
 

measured_shape.to_file(r"D:\___WodyPolskie\Gora\geodeci\01_02.04.2025\przygotowane_dane\pomierzone.shp")
skipped_shape.to_file(r"D:\___WodyPolskie\Gora\geodeci\01_02.04.2025\przygotowane_dane\skipped.shp")
gps_shape.to_file(r"D:\___WodyPolskie\Gora\geodeci\01_02.04.2025\przygotowane_dane\GPS.shp")
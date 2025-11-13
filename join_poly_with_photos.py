import os
import pandas as pd
import geopandas as gpd


poly_path = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\paczki_single.gpkg"
braki_path = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\braki_buffered.gpkg"
point_path = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\foto_2_2000.shp"
out_csv = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\csv.csv"
out_csv2 = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\csv2.csv"
out_csv3 = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\merged.csv"
polygon_id_field = "fid"


polys = gpd.read_file(poly_path, columns = ("fid", "name"))
points = gpd.read_file(point_path)
braki = gpd.read_file(braki_path, columns = ("fid", "braki_name"))


j = gpd.sjoin(
    points,
    #polys.reset_index().rename(columns={"index": "_poly_idx"}),
    polys,
    how = "inner",
    predicate = "intersects"
)[["paths", "name"]]

k = gpd.sjoin(
    braki,
    polys,
    how = "inner",
    predicate = "intersects"
)[["name", "braki_name"]]

"""
if polygon_id_field and polygon_id_field in polys.columns:
    keymap = polys.reset_index().set_index("_poly_idx")[polygon_id_field].to_dict()
    j["polygon_id"] = j["_poly_idx"].map(keymap)
else:
    j["polygon_id"] = j["_poly_idx"]

# Clean & de-duplicate
j["paths"] = j["paths"].astype(str).str.strip()
j = j[(j["paths"] != "") & j["paths"].notna()]
j = j.drop_duplicates(subset=["polygon_id", "paths"])
"""

j2 = (
    j.groupby("name")["paths"]
    .apply(lambda x: ",".join(map(str, sorted(x))))
    .reset_index()
)

k2 = (
    k.groupby("name")["braki_name"]
    .apply(lambda x: ",".join(map(str, sorted(x))))
    .reset_index()
)

merged = pd.merge(j2, k2, on = "name", how = "left")

#j[["name", "paths"]].to_csv(out_csv, index = False, sep = ";", encoding = "cp1250")
#k2[["name", "braki_name"]].to_csv(out_csv2, index = False, sep = ";", encoding = "cp1250")
merged[["name", "braki_name", "paths"]].to_csv(out_csv3, index = False, sep = ";", encoding = "cp1250")
import geopandas as gpd
import pandas as pd

### script to count numbers of features with specific attribute in "rodzaj_det" column for "fid" column

shape_path = r"V:\ROBOCZY\ORLEN_Rurociag\Bufory_z_obiektami\OP_detekcje_bufory.shp"


gdf = gpd.read_file(shape_path)

#empty dictionary to store counts
attribute_counts = {}


for rows, cols in gdf.iterrows():
    fid_value = cols["fid"]
    rodzaj_det_value = cols["rodzaj_det"]

    #initialize fid in dictionary if not already present
    if fid_value not in attribute_counts:
        attribute_counts[fid_value] = {
            "km": cols["km"],
            "Mauzer": 0,
            "Kanister": 0,
            "Wąż": 0,
            "Inne": 0,
            "Obiekt budowlany": 0,
            "Wegetacja": 0,
            "Potencjalna ingerencja": 0,
            "Potencjalny wyciek": 0,
            "Zbiornik wodny": 0
        }

    #increment count for the specific attribute
    if rodzaj_det_value in attribute_counts[fid_value]:
        attribute_counts[fid_value][rodzaj_det_value] += 1


columns = ["fid", "km", "Mauzer", "Kanister", "Wąż", "Inne", "Obiekt budowlany", "Wegetacja", "Potencjalna ingerencja", "Potencjalny wyciek", "Zbiornik wodny"]
new_gdf = pd.DataFrame(columns=columns)

for fid, counts in attribute_counts.items():
    object_list = [fid] + [counts[attr] for attr in columns[1:]]
    new_gdf.loc[len(new_gdf)] = object_list

new_gdf.to_csv(r"V:\ROBOCZY\ORLEN_Rurociag\Bufory_z_obiektami\OP_detekcje_bufory_counts.csv", index = False)
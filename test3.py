import geopandas as gpd
import pandas as pd

### script to count numbers of features with specific attribute in "rodzaj_det" column for "fid" column

#shape_path = r"V:\ROBOCZY\ORLEN_Rurociag\Bufory_z_obiektami\OP_detekcje_bufory.shp"
shape_path = r"D:\__ORLEN\detekcje\do_atl_zmiany.shp"


gdf = gpd.read_file(shape_path)

#empty dictionary to store counts
attribute_counts = {}


for rows, cols in gdf.iterrows():
    fid_value = cols["fid"]
    rodzaj_det_value = cols["rodzaj_det"]

    detekcja = cols["rodzaj_det"]
    rozdzielone = detekcja.split(",") if pd.notna(detekcja) else []

    zmiana = cols["Zmiana_pop"]
    rozdzielone_zmiana = zmiana.split(",") if pd.notna(zmiana) else []

    for item in rozdzielone:
        item_position = rozdzielone.index(item)

        #remove leading and trailing whitespace from item
        item = item.strip()

        #initialize fid in dictionary if not already present
        if fid_value not in attribute_counts:
            attribute_counts[fid_value] = {
                "km": cols["km_buf"],
                "Mauzer_Bez zmian": 0,
                "Mauzer_Nieprawidłowość usunięta": 0,
                "Mauzer_Wykryto nową nieprawidłowość": 0,
                "Kanister_Bez zmian": 0,
                "Kanister_Nieprawidłowość usunięta": 0,
                "Kanister_Wykryto nową nieprawidłowość": 0,
                "Wąż_Bez zmian": 0,
                "Wąż_Nieprawidłowość usunięta": 0,
                "Wąż_Wykryto nową nieprawidłowość": 0,
                "Inne_Bez zmian": 0,
                "Inne_Nieprawidłowość usunięta": 0,
                "Inne_Wykryto nową nieprawidłowość": 0,
                "Obiekt budowlany_Bez zmian": 0,
                "Obiekt budowlany_Nieprawidłowość usunięta": 0,
                "Obiekt budowlany_Wykryto nową nieprawidłowość": 0,
                "Wegetacja_Bez zmian": 0,
                "Wegetacja_Nieprawidłowość usunięta": 0,
                "Wegetacja_Wykryto nową nieprawidłowość": 0,
                "Potencjalna ingerencja_Bez zmian": 0,
                "Potencjalna ingerencja_Nieprawidłowość usunięta": 0,
                "Potencjalna ingerencja_Wykryto nową nieprawidłowość": 0,
                "Potencjalny wyciek_Bez zmian": 0,
                "Potencjalny wyciek_Nieprawidłowość usunięta": 0,
                "Potencjalny wyciek_Wykryto nową nieprawidłowość": 0,
                "Zbiornik wodny_Bez zmian": 0,
                "Zbiornik wodny_Nieprawidłowość usunięta": 0,
                "Zbiornik wodny_Wykryto nową nieprawidłowość": 0
            }

        #increment for the specific attribute with change status from "Zmiana_pop" column, with specific position corresponding to the attribute in "rodzaj_det" column
        if item_position < len(rozdzielone_zmiana):
            change_status = rozdzielone_zmiana[item_position].strip()
            key = f"{item}_{change_status}"
            if key in attribute_counts[fid_value]:
                attribute_counts[fid_value][key] += 1

        #check if item exists in the dictionary for the specific fid and increment the corresponding change status
        #if item in attribute_counts[fid_value]:
        #    attribute_counts[fid_value][item] += 1


columns = ["fid", "km", "Mauzer_Bez zmian", "Mauzer_Nieprawidłowość usunięta", "Mauzer_Wykryto nową nieprawidłowość", "Kanister_Bez zmian", "Kanister_Nieprawidłowość usunięta", "Kanister_Wykryto nową nieprawidłowość", "Wąż_Bez zmian", "Wąż_Nieprawidłowość usunięta", "Wąż_Wykryto nową nieprawidłowość", "Inne_Bez zmian", "Inne_Nieprawidłowość usunięta", "Inne_Wykryto nową nieprawidłowość", "Obiekt budowlany_Bez zmian", "Obiekt budowlany_Nieprawidłowość usunięta", "Obiekt budowlany_Wykryto nową nieprawidłowość", "Wegetacja_Bez zmian", "Wegetacja_Nieprawidłowość usunięta", "Wegetacja_Wykryto nową nieprawidłowość", "Potencjalna ingerencja_Bez zmian", "Potencjalna ingerencja_Nieprawidłowość usunięta", "Potencjalna ingerencja_Wykryto nową nieprawidłowość", "Potencjalny wyciek_Bez zmian", "Potencjalny wyciek_Nieprawidłowość usunięta", "Potencjalny wyciek_Wykryto nową nieprawidłowość", "Zbiornik wodny_Bez zmian", "Zbiornik wodny_Nieprawidłowość usunięta", "Zbiornik wodny_Wykryto nową nieprawidłowość"]
new_gdf = pd.DataFrame(columns=columns)

for fid, counts in attribute_counts.items():
    object_list = [fid] + [counts[attr] for attr in columns[1:]]
    new_gdf.loc[len(new_gdf)] = object_list

#new_gdf.to_csv(r"V:\ROBOCZY\ORLEN_Rurociag\Bufory_z_obiektami\OP_detekcje_bufory_counts.csv", index = False)
new_gdf.to_csv(r"D:\__ORLEN\detekcje\atl_counts_zmiany.csv", index = False)
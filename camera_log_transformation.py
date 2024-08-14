import os
import pandas as pd
from pyproj import Transformer


directory_path = r"C:\Atlasus\ZDJECIA\zur_jezewo"

front = os.path.join(directory_path, "FRONT_raw_3.txt") #ZMIENIC NAZWE PLIKU
rear = os.path.join(directory_path, "REAR_raw_3.txt") #ZMIENIC NAZWE PLIKU
map = os.path.join(directory_path, "MAP_raw.txt") #Z REGULY MAMY JEDEN TO ZOSTAWIAMY

koncowka = "_3"

out_rear = os.path.join(directory_path, "gpslog_REAR_3.txt")
out_front = os.path.join(directory_path, "gpslog_FRONT_3.txt")
out_map = os.path.join(directory_path, "gpslog_MAP.txt")

#Columns in input file
columns = ["Filename", "Northing", "Easting", "H-MSL", "Roll", "Pitch", "Heading", "XY Acc", "H Acc"]

#Columns for raw map file
columns1 = ["Filename", "Timestamp", "Easting", "Northing", "H-MSL", "Heading", "Pitch", "Roll"]

front_df = pd.read_csv(front, sep = ",", header = None)
front_df.columns = columns
#Drop unnecesary columns
front_df = front_df.drop("XY Acc", axis = 1)
front_df = front_df.drop("H Acc", axis = 1)
#Rearange columns
front_df = front_df[["Filename", "Easting", "Northing", "H-MSL", "Roll", "Pitch", "Heading"]]

#Same for rear
rear_df = pd.read_csv(rear, sep = ",", header = None)
rear_df.columns = columns
#Drop unnecesary columns
rear_df = rear_df.drop("XY Acc", axis = 1)
rear_df = rear_df.drop("H Acc", axis = 1)
#Rearange columns
rear_df = rear_df[["Filename", "Easting", "Northing", "H-MSL", "Roll", "Pitch", "Heading"]]

#Map
map_df = pd.read_csv(map, sep = ",", header = None, skiprows = 1)
map_df.columns = columns1
#Drop unnecesary columns
map_df = map_df.drop("Timestamp", axis = 1)
#Rearange columns
map_df = map_df[["Filename", "Easting", "Northing", "H-MSL", "Roll", "Pitch", "Heading"]]

#Changing data in map df
map_df["Pitch"] = 0
#map_df["Heading"] = front_df["Heading"]
map_df["H-MSL"] = map_df["H-MSL"] - 40.5

#Changing data in front df
front_df["Filename"] = front_df["Filename"].str.replace(r'\.JPG$', '', regex=True)
front_df["Filename"] = front_df["Filename"] + koncowka 
front_df["H-MSL"] = rear_df["H-MSL"]

#Chaning data in rear df
#rear_df["Roll"] = front_df["Roll"]
#rear_df["Pitch"] = front_df["Pitch"] * -1
#rear_df["Heading"] = front_df["Heading"] + 180
rear_df["Filename"] = rear_df["Filename"].str.replace(r'\.JPG$', '', regex=True)
rear_df["Filename"] = rear_df["Filename"] + koncowka 
#rear_df["H-MSL"] = map_df["H-MSL"]

for i in range(front_df.shape[0]):
    #XY Coords
    
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2177")
    point_front = transformer.transform(front_df["Northing"][i], front_df["Easting"][i])

    front_df["Northing"][i] = point_front[0]
    front_df["Easting"][i] = point_front[1]

    #Convert heading
    if front_df["Heading"][i] > 180:
        diff = front_df["Heading"][i] - 180
        front_df["Heading"][i] = -(180-diff)

for i in range(rear_df.shape[0]):
    #XY Coords
    
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2177")
    point_rear = transformer.transform(rear_df["Northing"][i], rear_df["Easting"][i])

    rear_df["Northing"][i] = point_rear[0]
    rear_df["Easting"][i] = point_rear[1]


    #Convert heading
    if rear_df["Heading"][i] > 180:
        diff1 = rear_df["Heading"][i] - 180
        rear_df["Heading"][i] = -(180-diff1)

for i in range(map_df.shape[0]):
    if map_df["Roll"][i] < 0:
        map_df["Roll"][i] = (180 + map_df["Roll"][i])
    else:
        map_df["Roll"][i] = -(180 - map_df["Roll"][i])

    if map_df["Heading"][i] > 0:
        map_df["Heading"][i] = map_df["Heading"][i] - 180
    else:
        map_df["Heading"][i] = map_df["Heading"][i] + 180

    #if map_df["Heading"][i] < 0:
        #diff2 = map_df["Heading"][i] + 180
        #map_df["Heading"][i] = -(180-diff2)
        #map_df["Heading"][i] = map_df["Heading"][i] + 180


#add a template at the head for front and rear
template = """Defined grid: PUWG2000s6
Focal length: 55mm
Sensor size: 35.9x24.0mm
"""

#add a template at the head for map
template2 = """Defined grid: PUWG2000s6
Focal length: 21mm
Sensor size: 35.9x24.0mm
"""

rear_df.to_csv(out_rear, sep = ";", index=False)
front_df.to_csv(out_front, sep = ";", index=False)
map_df.to_csv(out_map, sep = ";", index=False)

with open(out_rear, "r") as file:
    data = file.read()

with open(out_rear, "w") as modified:
    modified.write(template + data)

with open(out_front, "r") as file1:
    data1 = file1.read()

with open(out_front, "w") as modified1:
    modified1.write(template + data1)

with open(out_map, "r") as file2:
    data2 = file2.read()

with open(out_map, "w") as modified2:
    modified2.write(template2 + data2)
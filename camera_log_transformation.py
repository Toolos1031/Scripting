import os
import pandas as pd

directory_path = r"D:\Atlasus\FOTO\06_06_2024"

front = os.path.join(directory_path, "gpslog_front.txt")
back = os.path.join(directory_path, "gpslog_back.txt")

columns = ["Image", "Lat", "Lon", "AGL", "Roll", "Pitch", "Yaw", "XY Acc", "H Acc"]

front_df = pd.read_csv(front, sep = ",", header = None)
front_df.columns = columns

back_df = pd.read_csv(back, sep = ",", header = None)
back_df.columns = columns

#Chaning data in back df
back_df["Roll"] = front_df["Roll"]
back_df["Pitch"] = front_df["Pitch"] * -1
back_df["Yaw"] = front_df["Yaw"] + 180

for i in range(front_df.shape[0]):
    if back_df["Yaw"][i] >= 360:
        back_df["Yaw"][i] = front_df["Yaw"][i] - 180

back_df.to_csv(back, sep = ",", index=False)
front_df.to_csv(front, sep = ",", index=False)
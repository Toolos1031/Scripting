import pandas as pd
import os
import numpy as np


csv_files = []
name = r"E:\Orlen\Cloud\RAW"

column_names = ["Time", "Latitude", "Longitude", "Altitude", "Vel-Xb", "Vel-Yb", "Vel-Zb", "Roll", "Pitch", "Yaw", "Wander", "Accel-Xb", "Accel-Yb", "Accel-Zb", "ARate-Xb", "ARate-Yb", "ARate-Zb"]
df = pd.DataFrame(columns = column_names)

directory = os.listdir(name)

for file in directory:
    if file.endswith(".csv"):
        csv_files.append(file)


for files in csv_files:
    path = os.path.join(name, files)

    df = pd.read_csv(path, delim_whitespace = True, header = None, skiprows = 2)
    df.columns = column_names

    df["Latitude"] = np.degrees(df["Latitude"])
    df["Longitude"] = np.degrees(df["Longitude"])
    df["Roll"] = np.degrees(df["Roll"])
    df["Pitch"] = np.degrees(df["Pitch"])
    df["Yaw"] = np.degrees(df["Yaw"])

    df.to_csv(fr"E:\Orlen\Cloud\RAW\{files}_conv.csv", index=False)

    #df = pd.concat([df, df1], ignore_index = True)








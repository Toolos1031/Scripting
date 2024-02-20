import laspy
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime


# LOAD FILES
file_path = r'D:\Python\cloud.las'
las = laspy.read(file_path)

column_names = ["Time", "Latitude", "Longitude", "Altitude", "Vel-Xb", "Vel-Yb", "Vel-Zb", "Roll", "Pitch", "Yaw", "Wander", "Accel-Xb", "Accel-Yb", "Accel-Zb", "ARate-Xb", "ARate-Yb", "ARate-Zb"]
csv_path = r"D:\Python\sbet.csv"
trajectory = pd.read_csv(csv_path, delim_whitespace= True, header=None, skiprows=2)
trajectory.columns = column_names

trajectory["Latitude"] = np.degrees(trajectory["Latitude"])
trajectory["Longitude"] = np.degrees(trajectory["Longitude"])
trajectory["Roll"] = np.degrees(trajectory["Roll"])
trajectory["Pitch"] = np.degrees(trajectory["Pitch"])
trajectory["Yaw"] = np.degrees(trajectory["Yaw"])

trajectory.to_csv(r"D:\Python\sbet_conv.csv")

# CONVERT GPS TO UTC
gps_epoch = datetime(1980, 1, 6)
my_date = datetime(2024, 1, 5)

difference = my_date - gps_epoch
gps_week_number = difference.days // 7

seconds_in_week = 604800
time_offset = 18 #Offest between UTC and GPS

SOW_time = gps_week_number * seconds_in_week + time_offset - 1000000000

# CONVERT TIME
time_SOW_start = las["gps_time"].min() - SOW_time #Time from start of the week
time_SOW_end = las["gps_time"].max() - SOW_time

# CONVERT TRAJECTORY DATAFRAMES
new_df = trajectory[(trajectory["Time"] >= (time_SOW_start + time_offset)) & (trajectory["Time"] <= (time_SOW_end + time_offset))] #Trajectory with scans only

start_yaw = (new_df.iloc[0, 9]) #Pick a starting yaw value
second_yaw = start_yaw + 180

if second_yaw > 180:
    second_yaw = second_yaw - 360

yaw_deviation = 6

first_direction = new_df[(new_df["Yaw"] >= (start_yaw - yaw_deviation)) & (new_df["Yaw"] <= (start_yaw + yaw_deviation))]

second_direction = new_df[(new_df["Yaw"] >= (second_yaw - yaw_deviation)) & (new_df["Yaw"] <= (second_yaw + yaw_deviation))]



"""
fig, axs = plt.subplots(1, 3, figsize = (18, 6), sharex = True, sharey = True)


axs[0].plot(new_df["Longitude"], new_df["Latitude"], "r-", label = "Original")
axs[0].scatter(new_df["Longitude"], new_df["Latitude"], c="red", label = "Original")
axs[1].plot(first_direction["Longitude"], first_direction["Latitude"], "b-", label = "first_direction")
axs[1].scatter(first_direction["Longitude"], first_direction["Latitude"], c="blue", label = "first_direction")
axs[2].plot(second_direction["Longitude"], second_direction["Latitude"], "g-", label = "second_direction")
axs[2].scatter(second_direction["Longitude"], second_direction["Latitude"], c="green", label = "second_direction")

plt.tight_layout()
plt.show()

"""

# FIND BREAKPOINTS IN TRAJECTORY
a = first_direction.iloc[0, 0] #Pick the first point in the trajectory
gap_first = []
for row in first_direction["Time"]: #For each row compare it to the previous one and check the time difference
    if row - a > 3:
        gap_first.append(row)
        gap_first.append(a)
    a = row
gap_first.append(first_direction.iloc[0, 0]) #For good measure add the first and last point
gap_first.append(first_direction.iloc[-1, 0])

b = second_direction.iloc[0, 0]
gap_second = []
for row in second_direction["Time"]:
    if row - b > 3:
        gap_second.append(row)
        gap_second.append(b)
    b = row
gap_second.append(second_direction.iloc[0, 0])
gap_second.append(second_direction.iloc[-1, 0])

gaps = [new_df.iloc[0, 0], new_df.iloc[-1, 0]] #Add first and the last point of the main trajectory as well
gaps = gaps + gap_first + gap_second

# CLEAN UP COLLECTED BREAKPOINTS
no_dupes = []

for item in gaps: #Delete duplicates
    if item not in no_dupes:
        no_dupes.append(item)

no_dupes.sort()

# CLIP POINT CLOUD USING BREAKPOINTS
for time_loc in range(len(no_dupes)):
    try:
        start = no_dupes[time_loc] + SOW_time - time_offset
        end = no_dupes[time_loc + 1] + SOW_time - time_offset
    except:
        continue
    
    swath = las.points[(las.gps_time >= start) & (las.gps_time <= end)]
    swath_las = laspy.LasData(las.header)
    swath_las.points = swath

    output_path = r"D:\Python\out"
    extension = f"{int(time_loc)}.las"
    output = os.path.join(output_path, extension)

    swath_las.write(output)


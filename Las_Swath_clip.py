import laspy
import pandas as pd
import matplotlib.pyplot as plt
import os


# Load your LAS file
file_path = r'D:\woodfast\staszow\staszow_2000.las'
las = laspy.read(file_path)

csv_path = r"D:\woodfast\staszow\sbet.csv"
trajectory = pd.read_csv(csv_path, sep=";")

# Display a summary of the LAS file
#print("File Summary:")
#print(f"Point Format: {las.header.point_format}")
#print(f"Number of points: {las.header.point_count}")
#print(f"Available dimensions: {las.point_format.dimension_names}")

# Optionally, display some statistics for each dimension
"""
print("\nSome statistics for each dimension:")
for dimension in las.point_format.dimension_names:
    min_val = las[dimension].min()
    max_val = las[dimension].max()
    print(f"{dimension}: Min = {min_val}, Max = {max_val}")
"""


time = las["gps_time"].max() - las["gps_time"].min()
time_SOW_start = las["gps_time"].min() - 390435218
time_SOW_end = las["gps_time"].max() - 390435218
#print(time)
#print(time_SOW_start, time_SOW_start + 18)
#print(time_SOW_end, time_SOW_end + 18)

#print(trajectory.iloc[0])
#print(trajectory["Time"])

new_df = trajectory[(trajectory["Time"] >= (time_SOW_start + 18)) & (trajectory["Time"] <= (time_SOW_end + 18))]
print(new_df)

start_yaw = (new_df.iloc[0, 6])
second_yaw = start_yaw + 180

first_direction = new_df[(new_df["Yaw"] >= (start_yaw - 6)) & (new_df["Yaw"] <= (start_yaw + 6))]
print(first_direction)

second_direction = new_df[(new_df["Yaw"] >= (second_yaw - 6)) & (new_df["Yaw"] <= (second_yaw + 6))]
print(second_direction)



fig, axs = plt.subplots(1, 3, figsize = (18, 6), sharex = True, sharey = True)


axs[0].plot(new_df["Longitude"], new_df["Latitude"], "r-", label = "Original")
axs[0].scatter(new_df["Longitude"], new_df["Latitude"], c="red", label = "Original")
axs[1].plot(first_direction["Longitude"], first_direction["Latitude"], "b-", label = "first_direction")
axs[1].scatter(first_direction["Longitude"], first_direction["Latitude"], c="blue", label = "first_direction")
axs[2].plot(second_direction["Longitude"], second_direction["Latitude"], "g-", label = "second_direction")
axs[2].scatter(second_direction["Longitude"], second_direction["Latitude"], c="green", label = "second_direction")

plt.tight_layout()
#plt.show()

#new_df.to_csv(r"D:\woodfast\staszow\sbet_clip.csv")

a = first_direction.iloc[0, 0]
gap_first = []
for row in first_direction["Time"]:
    if row - a > 3:
        gap_first.append(row)
        gap_first.append(a)
    a = row
gap_first.append(first_direction.iloc[0, 0])
gap_first.append(first_direction.iloc[-1, 0])
print("Gaps in first direction", gap_first)

b = second_direction.iloc[0, 0]
gap_second = []
for row in second_direction["Time"]:
    if row - b > 3:
        gap_second.append(row)
        gap_second.append(b)
    b = row
gap_second.append(second_direction.iloc[0, 0])
gap_second.append(second_direction.iloc[-1, 0])
print("Gaps in second direction", gap_second)


gaps = [new_df.iloc[0, 0], new_df.iloc[-1, 0]]
gaps = gaps + gap_first + gap_second

no_dupes = []

for item in gaps:
    if item not in no_dupes:
        no_dupes.append(item)

no_dupes.sort()

print(no_dupes)

for time_loc in range(len(no_dupes)):
    try:
        start = no_dupes[time_loc] + 390435218 - 18
        end = no_dupes[time_loc + 1] + 390435218 - 18
    except:
        continue
    
    swath = las.points[(las.gps_time >= start) & (las.gps_time <= end)]
    swath_las = laspy.LasData(las.header)
    swath_las.points = swath

    output_path = r"D:\woodfast\staszow\PY"
    extension = f"{int(time_loc)}.las"
    output = os.path.join(output_path, extension)

    swath_las.write(output)


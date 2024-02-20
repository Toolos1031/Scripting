import pandas as pd
import numpy as np
from datetime import datetime

column_names = ["Time", "Latitude", "Longitude", "Altitude", "Vel-Xb", "Vel-Yb", "Vel-Zb", "Roll", "Pitch", "Yaw", "Wander", "Accel-Xb", "Accel-Yb", "Accel-Zb", "ARate-Xb", "ARate-Yb", "ARate-Zb"]
csv_path = r"D:\woodfast\staszow\PY\sbet.csv"
trajectory = pd.read_csv(csv_path, delim_whitespace= True, header=None, skiprows=2)
trajectory.columns = column_names

trajectory["Latitude"] = np.degrees(trajectory["Latitude"])
trajectory["Longitude"] = np.degrees(trajectory["Longitude"])
trajectory["Roll"] = np.degrees(trajectory["Roll"])
trajectory["Pitch"] = np.degrees(trajectory["Pitch"])
trajectory["Yaw"] = np.degrees(trajectory["Yaw"])


print(trajectory)


gps_epoch = datetime(1980, 1, 6)

my_date = datetime(2024, 1, 31)

difference = my_date - gps_epoch

gps_week_number = difference.days // 7

seconds_in_week = 604800

print("GPS Week Number: ", gps_week_number)
#390435218
print("GPS time: ", gps_week_number * seconds_in_week + 18 - 1000000000)
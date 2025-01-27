
import matplotlib.pyplot as plt
import laspy
import numpy as np
import os
import pandas as pd
from mpl_point_clicker import clicker
import pickle

end = False

folder_name = r"D:\WODY_testy\clipping\out"

with open(r"D:\WODY_testy\clipping\dictionary.pkl", "rb") as pick:
    dict = pickle.load(pick)

data = pd.DataFrame(dict)

scans = [os.path.join(folder_name, i) for i in os.listdir(folder_name) if i.endswith(".las")]

measured_points = pd.DataFrame(columns = ["id", "Pomiar", "X_coord", "Y_coord", "Z_coord"])

def mean(value):
    return((max(value) + min(value))/2)

def onkeypress(event):
    global end
    if event.key == "n":
        plt.close()

    if event.key == "`":
        end = True
        plt.close()

def onclick(event):
    if event.inaxes == ax:
        cont, ind = scatter.contains(event)
        if cont:
            idx = ind["ind"][0]
            print(f"Clicked on point number: {idx}")
            print(f"Coord X: {x[idx]}, Coord Y: {y[idx]}, Coord Z: {z[idx]}")

for file in scans:

    if end:
        break

    filename = "_".join(file.split("_")[-4:])

    matching_row = data[data["full_name"] == filename]

    if not matching_row.empty:
        angle = matching_row["angle"].iloc[0]

    scan = laspy.read(file)

    x = []
    y = []
    z = []

    for i in scan.x:
        x.append(i)

    for i in scan.y:
        y.append(i)

    for i in scan.z:
        z.append(i)


    fig = plt.figure(figsize = (4,4))
    ax = fig.add_subplot(111, projection = "3d")
    fig.subplots_adjust(top = 1.3, bottom = -0.3)

    scatter = ax.scatter(x, y, z, s = 1)

    scatter.set_picker(1)

    ax.view_init(azim=-angle+90, elev=0)

    plt.xlim(mean(x)-5, mean(x)+5)
    plt.ylim(mean(y)-5, mean(y)+5)

    fig.canvas.mpl_connect("key_press_event", onkeypress)
    fig.canvas.mpl_connect("button_press_event", onclick)

    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()

    plt.show()
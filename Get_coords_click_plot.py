
import matplotlib.pyplot as plt
import laspy
import os
import pandas as pd
import pickle
from matplotlib.widgets import Button, Slider
import numpy as np

### IMPORTING ###

folder_name = r"D:\WODY_testy\clipping\out" # Folder with cross-sections

with open(r"D:\WODY_testy\clipping\dictionary.pkl", "rb") as pick: # File with cross-section metadata
    dict = pickle.load(pick)

### SETUPS ###

end = False # Global flag for breaking the loop

data = pd.DataFrame(dict) # Conversion from dict to pd.DF

scans = [os.path.join(folder_name, i) for i in os.listdir(folder_name) if i.endswith(".las")] # List of all cross-sections in the input folder

out_data = pd.DataFrame(columns = ["id", "oznaczenie", "distance", "Left X", "Left Y", "Left Z", "Mid X", "Mid Y", "Mid Z", "Right X", "Right Y", "Right Z", "Comment"])

### FUNCTIONS ###

def mean(value): # Function to calculate mean value. Used for limits in mpl plot
    return((max(value) + min(value))/2)

def onkeypress(event): # Function to grab key press events from the plot
    global end
    if event.key == "n":
        plt.close()

    if event.key == "`":
        end = True
        plt.close()

def onclick(event): # Function to handle click events on the plot
    if event.inaxes == ax:
        cont, ind = scatter.contains(event)
        if cont:
            idx = ind["ind"][0]
            clicked_point = f"Coord X: {round(x[idx], 2)}, Coord Y: {round(y[idx], 2)}, Coord Z: {round(z[idx], 2)}"
            print(f"Clicked on point number: {idx}")

            clicks.append((x[idx], y[idx], z[idx]))

            colors[idx] = (1, 0, 0, 1) # Set colors on picked points
            scatter.set_color(colors)

            sizes[idx] = 20 # Set size on picked points
            scatter.set_sizes(sizes)

            update_text(clicked_point)

def save_clicks(proper):
    filename = "_".join(file.split("_")[-4:])
    matching_row = data[data["full_name"] == filename]

    if proper == 0:
        dict_temp = {}
        dict_temp = {
            "id" : matching_row["id"].iloc[0],
            "oznaczenie" : matching_row["oznaczenie"].iloc[0],
            "distance" : matching_row["distance"].iloc[0],
            "Left X" : clicks[0][0],
            "Left Y" : clicks[0][1],
            "Left Z" : clicks[0][2],
            "Right X" : clicks[1][0],
            "Right Y" : clicks[1][1],
            "Right Z" : clicks[1][2],
            "Mid X" : clicks[2][0],
            "Mid Y" : clicks[2][1],
            "Mid Z" : clicks[2][2]
        }

    if proper == 1:
        dict_temp = {}
        dict_temp = {
            "id" : matching_row["id"].iloc[0],
            "oznaczenie" : matching_row["oznaczenie"].iloc[0],
            "distance" : matching_row["distance"].iloc[0],
            "Comment" : "SKIPPED"
        }
        
    return dict_temp

def update_text(text):
    existing_text = coord_text.get_text() # Update text with coordinates
    updated_text = existing_text + f"\n{text}" if existing_text != "Click a point" else text
    coord_text.set_text(updated_text)
    fig.canvas.draw_idle()    

def reset(event): # Reset button logic
    coord_text.set_text("Click a point")
    colors[:] = default_colors
    scatter.set_color(colors)
    sizes[:] = default_sizes
    scatter.set_sizes(sizes)
    fig.canvas.draw_idle()

def next(event): # Next button logic
    coord_text.set_text("Click a point")
    colors[:] = default_colors
    scatter.set_color(colors)
    sizes[:] = default_sizes
    scatter.set_sizes(sizes)
    out_data.loc[len(out_data)] = save_clicks(proper = 0)
    plt.close()

def skip(event): # Skip button logic
    coord_text.set_text("Click a point")
    colors[:] = default_colors
    scatter.set_color(colors)
    sizes[:] = default_sizes
    scatter.set_sizes(sizes)
    out_data.loc[len(out_data)] = save_clicks(proper = 1)
    plt.close()

def end_task(event):
    global end
    end = True
    plt.close()

def update_point_size(val): # Slider logic
    sizes[:] = val
    scatter.set_sizes(sizes)
    fig.canvas.draw_idle()

def angle(file): # Function to grab angle value from the cross-section metadata, based on the name of the section
    filename = "_".join(file.split("_")[-4:])
    matching_row = data[data["full_name"] == filename]

    if not matching_row.empty:
        angle = matching_row["angle"].iloc[0]
        return angle
    return 0

### MAIN LOOP ###

for file in scans:

    clicks = []
    proper = 0

    if end:
        break

    scan = laspy.read(file)

    x = list(scan.x)
    y = list(scan.y)
    z = list(scan.z)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection = "3d")
    fig.subplots_adjust(top = 1.3, bottom = -0.2)

    default_colors = np.array([(0, 0, 1, 1)] * len(x))
    colors = default_colors.copy()

    default_sizes = np.full(len(x), 1)
    sizes = default_sizes.copy()

    scatter = ax.scatter(x, y, z, s = sizes, c = colors)

    scatter.set_picker(1)

    ax.view_init(azim=-angle(file)+90, elev=0)

    plt.xlim(mean(x)-5, mean(x)+5)
    plt.ylim(mean(y)-5, mean(y)+5)

    coord_text = fig.text(0, 0.95, "Click a point", fontsize = 12, color = "blue", va = "top")

    ax_reset = fig.add_axes([0.1, 0.05, 0.2, 0.075])
    reset_button = Button(ax_reset, "Reset")
    reset_button.on_clicked(reset)

    ax_next = fig.add_axes([0.7, 0.05, 0.2, 0.075])
    next_button = Button(ax_next, "Next")
    next_button.on_clicked(next)

    ax_skip = fig.add_axes([0.4, 0.05, 0.2, 0.075])
    skip_button = Button(ax_skip, "Skip")
    skip_button.on_clicked(skip)

    ax_end = fig.add_axes([0.7, 0.92, 0.2, 0.075])
    end_button = Button(ax_end, "End")
    end_button.on_clicked(end_task)

    ax_slider = fig.add_axes([0.2, 0.15, 0.6, 0.03])
    point_size_slider = Slider(ax_slider, "Point Size", 1, 20, valinit = 1, valstep = 1)
    point_size_slider.on_changed(update_point_size)

    fig.canvas.mpl_connect("key_press_event", onkeypress)
    fig.canvas.mpl_connect("button_press_event", onclick)

    manager = plt.get_current_fig_manager()
    manager.window.showMaximized()

    plt.show()

print(out_data)
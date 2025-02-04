import matplotlib.pyplot as plt
import laspy
import os
import pandas as pd
import pickle
from matplotlib.widgets import Button, Slider
import numpy as np
import tkinter as tk
from tkinter import filedialog
from matplotlib.cbook import get_sample_data


### IMPORTING ###

root = tk.Tk()

root.withdraw()

file_types = [("Pickle Files", "*.pkl")]

pickle_name = filedialog.askopenfilename(filetypes = file_types, title = "Select pickle file") # Folder with cross-sections
#pickle_name = r"D:\WODY_testy\clipping\dictionary.pkl" # Folder with cross-sections

folder_name = filedialog.askdirectory(title = "Select directory with scans") # Folder with cross-sections
#folder_name = r"D:\WODY_testy\clipping\out" # Folder with cross-sections

photo_folder = filedialog.askdirectory(title = "Select directory with photos")
#photo_folder = r"D:\WODY_testy\clipping\atlas"

with open(pickle_name, "rb") as pick: # File with cross-section metadata
    dict = pickle.load(pick)

### SETUPS ###

end = False # Global flag for breaking the loop

data = pd.DataFrame(dict) # Conversion from dict to pd.DF

scans = [os.path.join(folder_name, i) for i in os.listdir(folder_name) if i.endswith(".las")] # List of all cross-sections in the input folder

label_dict = {
    "1" : "RGS",
    "2" : "RDS",
    "3" : "RD",
    "4" : "RDS",
    "5" : "RGS"
}

val = 1

point_list = []

### FUNCTIONS ###

def mean(value): # Function to calculate mean value. Used for limits in mpl plot
    return(round((max(value) + min(value))/ 2, 2))

def onkeypress(event): # Function to grab key press events from the plot
    global end
    if event.key == "n":
        plt.close()

    if event.key == "`":
        end = True
        plt.close()

def onclick(event): # Function to handle click events on the plot
    global point_list
    if event.inaxes == ax:
        cont, ind = scatter.contains(event)
        if cont:
            idx = ind["ind"][0]
            clicked_point = f"Coord X: {round(x[idx], 2)}, Coord Y: {round(y[idx], 2)}, Coord Z: {round(z[idx], 2)}"
            print(f"Clicked on point number: {idx}")

            clicks.append((x[idx], y[idx], z[idx]))

            colors[idx] = (1, 0, 0, 1) # Set colors on picked points
            scatter.set_color(colors)

            sizes[idx] = 30 # Set size on picked points
            scatter.set_sizes(sizes)

            try:
                label = label_dict[str(len(clicks))]

                point_label = ax.text(x[idx], y[idx], z[idx], label, fontsize = 10, color = "red")

                point_list.append(point_label)
            except:
                pass

            update_text(clicked_point)

def save_clicks(trench_visible):
    filename = "_".join(file.split("_")[-4:])

    condition = (data["full_name"] == filename)

    if trench_visible == 0:
        data.loc[condition, "Left X"] = round(clicks[0][0], 2)
        data.loc[condition, "Left Y"] = round(clicks[0][1], 2)
        data.loc[condition, "Left Z"] = round(clicks[0][2], 2)
        data.loc[condition, "Mid X"] = round(clicks[1][0], 2)
        data.loc[condition, "Mid Y"] = round(clicks[1][1], 2)
        data.loc[condition, "Mid Z"] = round(clicks[1][2], 2)
        data.loc[condition, "Right X"] = round(clicks[2][0], 2)
        data.loc[condition, "Right Y"] = round(clicks[2][1], 2)
        data.loc[condition, "Right Z"] = round(clicks[2][2], 2)
        data.loc[condition, "Comment"] = "Completed"
        
    if trench_visible == 1:
        data.loc[condition, "Comment"] = "Skipped"
        data.loc[condition, "Mean X"] = mean(x)
        data.loc[condition, "Mean Y"] = mean(y)

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
    warning_text.set_text("")
    for text in point_list:
        text.remove()
    point_list.clear()
    clicks.clear()
    fig.canvas.draw_idle()

def next(event): # Next button logic
    coord_text.set_text("Click a point")
    colors[:] = default_colors
    scatter.set_color(colors)
    sizes[:] = default_sizes
    scatter.set_sizes(sizes)
    if len(clicks) == 5:
        save_clicks(trench_visible = 0)
        plt.close()
    else:
        warning_text.set_text("Wrong amount of points \n click 'RESET'")
        fig.canvas.draw_idle()

def skip(event): # Skip button logic
    coord_text.set_text("Click a point")
    colors[:] = default_colors
    scatter.set_color(colors)
    sizes[:] = default_sizes
    scatter.set_sizes(sizes)
    save_clicks(trench_visible = 1)
    plt.close()

def end_task(event):
    global end
    end = True
    plt.close()

def photo(event):
    os.system(photo_path)
    
def update_point_size(value): # Slider logic
    global val
    sizes[:] = value
    scatter.set_sizes(sizes)
    fig.canvas.draw_idle()
    val = value

def angle(file): # Function to grab angle value from the cross-section metadata, based on the name of the section
    filename = "_".join(file.split("_")[-4:])
    
    condition = (data["full_name"] == filename)
    matching_row = data.loc[condition, ["angle"]]

    if not matching_row.empty:
        angle = matching_row.iloc[0, 0]
        return angle
    return 0

def get_value(file, column): # Function to grab angle value from the cross-section metadata, based on the name of the section
    filename = "_".join(file.split("_")[-4:])
    
    condition = (data["full_name"] == filename)
    matching_col = data.loc[condition, [column]]

    if column == "angle":
        if not matching_col.empty:
            angle = matching_col.iloc[0, 0]
            return angle
        return 0
    
    if column == "Comment":
        comment = matching_col.iloc[0, 0]
        return str(comment)


### MAIN LOOP ###

for file in scans:
    filename = "_".join(file.split("_")[-4:])
    photo_path = os.path.join(photo_folder, filename.split(".")[0]+".png")

    if get_value(file, "Comment") == "nan":
        clicks = []
        trench_visible = 0

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

        default_sizes = np.full(len(x), val)
        sizes = default_sizes.copy()

        scatter = ax.scatter(x, y, z, s = sizes, c = colors)

        scatter.set_picker(1)

        ax.view_init(azim=-get_value(file, "angle")+90, elev=0)

        plt.xlim(mean(x)-5, mean(x)+5)
        plt.ylim(mean(y)-5, mean(y)+5)

        coord_text = fig.text(0, 0.95, "Click a point", fontsize = 12, color = "blue", va = "top")
        name_text = fig.text(0.5, 0.95, get_value(file, "angle"), fontsize = 12, color = "blue" )
        warning_text = fig.text(0.3, 0.5, "", fontsize = 40, color = "red")

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

        ax_photo = fig.add_axes([0, 0.4, 0.2, 0.075])
        photo_button = Button(ax_photo, "Photo")
        photo_button.on_clicked(photo)

        ax_slider = fig.add_axes([0.2, 0.15, 0.6, 0.03])
        point_size_slider = Slider(ax_slider, "Point Size", 1, 20, valinit = val, valstep = 1)
        point_size_slider.on_changed(update_point_size)

        im = plt.imread(get_sample_data(photo_path))
        ax_photo_draw = fig.add_axes([0, 0.4, 0.2, 0.5])
        ax_photo_draw.imshow(im)
        ax_photo_draw.axis("off")

        fig.canvas.mpl_connect("key_press_event", onkeypress)
        fig.canvas.mpl_connect("button_press_event", onclick)

        manager = plt.get_current_fig_manager()
        #manager.window.showMaximized()
        manager.full_screen_toggle()

        plt.show()
    else:
        pass
        print("Section arleady completed - Skipping")

    
data.to_csv(os.path.join(folder_name, "csv.csv"))

with open(pickle_name, "wb") as f:
        pickle.dump(data, f)
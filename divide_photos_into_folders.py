import os
import shutil

photo_path = r"E:\____Wody_polskie\Przekroje\JEMIELNO\test"

photo_list = [photo for photo in os.listdir(photo_path) if photo.endswith(".png")]
flight_list = []
folder_names = []

for photo in photo_list:

    flight = photo.split("-")[-1].split(".")[0]
    
    if flight not in flight_list:
        flight_list.append(flight)

for name in flight_list:
    folder_name = os.path.join(photo_path, name)
    atlas_folder = os.path.join(folder_name, "atlas")

    folder_names.append(folder_name)
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name, exist_ok=True)
        os.makedirs(atlas_folder, exist_ok=True)
    
    name_list = []

    for photo in photo_list:
        flight = photo.split("-")[-1].split(".")[0]

        if str(flight) == str(name):
            this_photo_path = os.path.join(photo_path, photo)
            name_list.append(this_photo_path)
    
    for file in name_list:
        shutil.move(file, atlas_folder)


for folder in os.listdir(photo_path):
    atlas = os.path.join(photo_path, folder, "atlas")
    
    for old_name in os.listdir(atlas):
        new_name = old_name.split("-")[0] + ".png"

        old_path = os.path.join(atlas, old_name)
        new_path = os.path.join(atlas, new_name)

        os.rename(old_path, new_path)
        
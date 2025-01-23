import os

import glob
import re
import shutil

directory1 = r"D:\____Katowice\surowe_dane"
pendrive = r"D:\____Katowice\kato_wip\foto"

photo_path = r"\IMG\Camera1"

lista = []
img_folder = []

for i in os.listdir(directory1):
    folder = os.path.join(directory1, i)
    lista.append(folder)

c = 1

for directory in lista:
    img = glob.glob(os.path.join(directory, "IMG"))
    print(img)
    try:
        img, = img
        if os.path.exists(img):
            match = re.search(r'@@[^/\\]+', directory)
        if match: 
            folder_name = match.group(0)
            print(folder_name)
            destination_folder = os.path.join(pendrive, folder_name)
            os.makedirs(destination_folder, exist_ok=True)
            shutil.copytree(img, destination_folder, dirs_exist_ok=True)
            print(f"finished {c} out of {len(lista)}")
            c += 1
        else:
            print("error")
    except:
        pass


""" 
        img_folder.append(img)


c = 0 

for b in img_folder:
    match = re.search(r'@@[^/\\]+', directory)
    if match: 
        folder_name = match.group(0)
        print(folder_name)
        destination_folder = os.path.join(pendrive, folder_name, "FOTO")
        os.makedirs(destination_folder, exist_ok=True)
        b, = b
        #shutil.copytree(b, destination_folder, dirs_exist_ok=True)
        print(f"finished {c} out of 40")
        c += 1
    else:
        print("error")

"""
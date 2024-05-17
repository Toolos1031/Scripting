import os
from unidecode import unidecode

file_path = r"D:\Janek\folders.txt"

parent_dir = r"D:\Janek"

os.makedirs(parent_dir, exist_ok=True)

with open(file_path, "r", encoding="utf-8") as file:
    for line in file:
        folder_name = line.strip()
        if folder_name.endswith("-"):
            folder_name = folder_name[:-1]
        ascii_folder_name = unidecode(folder_name)
        new_directory_path = os.path.join(parent_dir, folder_name)
        os.makedirs(new_directory_path, exist_ok=True)

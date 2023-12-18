import csv
import os
import random

file = open(r"D:\Spychowo\CLIPPING\unikalne_id_2.csv", "r")
data = list(csv.reader(file, delimiter=","))
file.close()

print(data[1][0])

nazwy = []
numery = []

for i in range(300):
    nazwa = data[i][0]+".laz"
    nazwy.append(nazwa)

    numer = str(i) + ".laz"
    numery.append(numer)

nazwy_modified = [item.replace("/", "_") for item in nazwy]

name_mapping = dict(zip(numery, nazwy_modified))

#name_mapping = {str(i): nazwy for i, nazwy in enumerate(nazwy, start=1)}
print(name_mapping)




def rename_files(directory_path, name_mapping, output_path):
    # Iterate through files in the directory
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)

        # Check if the file is a regular file
        if os.path.isfile(file_path):
            # Get the new name from the mapping or keep the original if not found
            new_filename = name_mapping.get(filename, filename)

            # Build the new file path
            new_file_path = os.path.join(output_path, new_filename)

            # Rename the file
            try:
                os.rename(file_path, new_file_path)
            except FileExistsError:
                os.rename(file_path, new_file_path)

            print(f"Renamed: {filename} to {new_filename}")

# Example usage
directory_path = r'D:\Spychowo\CLIPPING\out'
output_path = r'D:\Spychowo\CLIPPING\out\2'

rename_files(directory_path, name_mapping, output_path)


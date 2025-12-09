import os

# Set the path to the directory containing the folders
directory = r'G:\Wody\photos'  # <-- Change this to your actual folder path

for folder_name in os.listdir(directory):
    full_path = os.path.join(directory, folder_name)

    # Ensure it's a directory and contains 'rawicz' in any case
    lower_name = folder_name.lower()
    try:
        if os.path.isdir(full_path) and 'rawicz' in lower_name:
            # Find the index of the word 'rawicz' (case-insensitive)
            index = lower_name.find('rawicz')
            
            # Get the original part of the name starting at that index
            new_name = folder_name[index:]

            # Replace starting 'R' or any case variation with lowercase 'r'
            new_name = 'r' + new_name[1:]

            new_path = os.path.join(directory, new_name)

            # Rename the folder
            os.rename(full_path, new_path)
            print(f'Renamed: {folder_name} → {new_name}')
    except:
        pass
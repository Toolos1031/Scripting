import os

# Set the directory path
directory_path = r'E:\Kotomierz_Serock\REAR_4'

# List all files in the directory
for filename in os.listdir(directory_path):
    # Construct old file name path
    old_file_path = os.path.join(directory_path, filename)
    
    # Check if it's a file
    if os.path.isfile(old_file_path):
        # Split the file name and extension
        name, ext = os.path.splitext(filename)
        
        # Construct new file name with "_1" before the extension
        new_file_name = f"{name}_3{ext}"
        new_file_path = os.path.join(directory_path, new_file_name)
        
        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f"Renamed: {old_file_path} to {new_file_path}")

print("All files have been renamed.")
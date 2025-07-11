from collections import defaultdict
import os
import shutil

# Set your base directory
base_dir = r'D:\___WodyPolskie\Gora\laczenie\1'

single = os.path.join(base_dir, "single")

# Dictionary to collect file paths by filename
files_by_name = defaultdict(list)

for root, _, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith('.las'):
            files_by_name[file].append(os.path.join(root, file))

# Filter only those filenames that occur more than once
singles = [(filename, paths) for filename, paths in files_by_name.items() if len(paths) == 1]

for filename, paths in singles:
    print(filename, paths)
    shutil.copyfile(paths[0], os.path.join(single, filename))
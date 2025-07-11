import os
from collections import defaultdict
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Set your base directory
base_dir = 'D:\___WodyPolskie\Gora\laczenie'

joined_folder = os.path.join(base_dir, "out")

# Dictionary to collect file paths by filename
files_by_name = defaultdict(list)

for root, _, files in os.walk(base_dir):
    for file in files:
        if file.lower().endswith('.las'):
            files_by_name[file].append(os.path.join(root, file))

# Filter only those filenames that occur more than once
duplicates = [(filename, paths) for filename, paths in files_by_name.items() if len(paths) > 1]
singles = [(filename, paths) for filename, paths in files_by_name.items() if len(paths) == 1]

def merge_files(godlo, file_list, output_path):
    if file_list:
        print(f"Merging {godlo}")
        cmd = ['lasmerge', '-i'] + file_list + ["-o", output_path]
        subprocess.run(cmd)

def merge_clouds():
    
    with ThreadPoolExecutor(max_workers = 10) as executor:
        for filename, paths in duplicates:
            godlo = filename.split(".")[0]
            out_path = os.path.join(joined_folder, godlo + ".las")
            executor.submit(merge_files, godlo, paths, out_path)

if __name__ == "__main__":
    merge_clouds()
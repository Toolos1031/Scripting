import os

directory_path = r"D:\CHC\Out\CHC_20240423142550\Results\Export\@@2024-04-22-141759\ADJUST1\Scanner1"

output = os.path.join(directory_path, "merged.las")

a = 0

for i in os.listdir(directory_path):
    if i.endswith(".las"):
        new_name = str(a) + ".las"

        curr_file_path = os.path.join(directory_path, i)
        new_file_path = os.path.join(directory_path, new_name)

        os.rename(curr_file_path, new_file_path)

        a += 1

las_files = [f for f in os.listdir(directory_path) if f.endswith(".las")]

full_name = [os.path.join(directory_path, file) for file in las_files]

cmd = 'las2las -i ' + ' '.join(full_name) + f' -merged -o {output}'

print(len(cmd))

os.system(cmd)
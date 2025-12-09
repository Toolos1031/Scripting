import os
import shutil

folder = r"G:\Wody\Ortho_joining\clipped_godlo_tif"


f1 = os.path.join(folder, "22")
f2 = os.path.join(folder, "23")
f3 = os.path.join(folder, "35")
f4 = os.path.join(folder, "other")


n1 = "M-33-22"
n2 = "M-33-23"
n3 = "M-33-35"

l1 = []
l2 = []
l3 = []
l4 = []

for i in os.listdir(folder):
    if n1 in i:
        src_folder = os.path.join(folder, i)
        dst_folder = os.path.join(f1, i)

        shutil.copyfile(src_folder, dst_folder)

        l1.append(i)
    elif n2 in i:
        src_folder = os.path.join(folder, i)
        dst_folder = os.path.join(f2, i)

        shutil.copyfile(src_folder, dst_folder)

        l2.append(i)
    elif n3 in i:
        src_folder = os.path.join(folder, i)
        dst_folder = os.path.join(f3, i)

        shutil.copyfile(src_folder, dst_folder)


        l3.append(i)
    else:
        if i.endswith(".tif"):
            src_folder = os.path.join(folder, i)
            dst_folder = os.path.join(f4, i)

            shutil.copyfile(src_folder, dst_folder)
            l4.append(i)


print(len(l1), len(l2), len(l3), len(l4))

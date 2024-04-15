import os

r = r"D:\Atlasus\3_ground_class\temp\roads.las"
g = r"D:\Atlasus\3_ground_class\temp\ground.las"
ng = r"D:\Atlasus\3_ground_class\temp\non_ground.las"
output = r"D:\Atlasus\3_ground_class\out.las"

cmd = f"las2las -i {r} {g} {ng} -merged -o {output}"

os.popen(cmd)
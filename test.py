import pandas as pd
import os

clip_folder = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\clipped"
csv_path = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\merged.csv"
out_path = r"D:\___WodyPolskie\7_Krotoszyn\wypelnianie\for_agi.csv"

clipped_files = [os.path.join(clip_folder, f) for f in os.listdir(clip_folder) if f.endswith(".las")]

df = pd.read_csv(csv_path, sep = ";", encoding = "cp1250")
df["files_paths"] = ""

#print(df.head())

a = df["braki_name"][1].split(",")
#print(a)



files_df = pd.DataFrame({"braki_paths" : clipped_files, "short_name" : ""})

for rows, cols in files_df.iterrows():
    short_name = cols["braki_paths"].split("^")[1].split(".")[0]
    cols["short_name"] = short_name

files_2 = (
    files_df.groupby("short_name")["braki_paths"]
    .apply(lambda x: ",".join(map(str, sorted(x))))
    .reset_index()
)

#print(files_2.head())


for rows, cols in df.iterrows():
    print(rows)
    braki = cols["braki_name"].split(",")
    files = []
    if len(braki) == 1:
        brak = braki[0]
        for rows2, cols2, in files_2.iterrows():
            if int(cols2["short_name"]) == int(brak):
                files.append(cols2["braki_paths"])
    else:
        for brak in braki:
            for rows2, cols2, in files_2.iterrows():
                if int(cols2["short_name"]) == int(brak):
                    files.append(cols2["braki_paths"])
    joined = ",".join(map(str, files))
    #df["files_paths"][rows] = str(joined)
    df.loc[rows, "files_pahts"] = str(joined)

print(df.head())

df.to_csv(out_path, sep = ";", encoding = "cp1250")
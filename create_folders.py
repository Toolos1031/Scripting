import os
import pandas as pd
import errno

directory = r"C:\___RDLP_ZIELONA\foldery"
files_path = r"C:\___RDLP_ZIELONA\file_list.txt"
inside_path = r"C:\___RDLP_ZIELONA\inside_file_list.txt"

files = pd.read_csv(files_path, sep = "\t", header = None)
inside_files = pd.read_csv(inside_path, sep = "\t", header = None)
columns1 = ["LP", "Obszar", "Cel"]
columns2 = ["Path"]
files.columns = columns1
inside_files.columns = columns2

def loop():
    for i in range(files.shape[0]):
        try:
            new_folder = f"{files['LP'][i]}_{files['Obszar'][i]}_{files['Cel'][i]}"
            for l in range(inside_files.shape[0]):
                try:
                    #print(os.path.join(new_folder, str(inside_files["Path"][l])))
                    os.makedirs(os.path.join(directory, new_folder, str(inside_files["Path"][l])))
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        print("Directory not created")
                    else:
                        raise
            os.makedirs(os.path.join(directory, new_folder))
        except OSError as e:
            if e.errno == errno.EEXIST:
                print("Directory not created")
            else:
                raise

    for l in os.listdir(directory):
        inside_folder = os.path.join(directory, l)
        print(inside_folder)


loop()
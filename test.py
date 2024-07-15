import os
import glob
from pathlib import Path

directory = r"D:\Atlasus\Naloty\Dane\Dzien_5_6\Surowe_dane"
directory1 = Path("D:/Atlasus/Naloty/Dane/Dzien_5_6/Surowe_dane")

def walk__():
    for path, folders, files in os.walk(directory):
        print(len(files))
        print(path)

def glob__():
    for filename in glob.glob(f"{directory}/*"):
        print(filename)

def pathlib__():
    files = Path(directory).glob("*")

    for filename in files:
        print(filename)

def pathlib_1():
    file_list = [f for f in directory1.glob("**/*") if f.is_file()]
    print(file_list)

pathlib_1()
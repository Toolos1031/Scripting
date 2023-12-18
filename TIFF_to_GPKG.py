import os
from osgeo import gdal

# Empty lists
files = []
converted = []
built_overview = []

# Some inputs
gdal.TermProgress = gdal.TermProgress_nocb

# Basic info
print("------------------------------TIFF to GPKG Converter------------------------------ \n")
print("Version - v.1.0 \n")
print("This program takes any orthophoto in a .tif format and converts it into GeoPackage \n")
print("For the program to work properly, please enter a directory with files to convert \n")
print("The program won't start untill you set the directory properly \n")
print("---------------------------------------------------------------------------------- \n \n")


def user_input():
    while True:
        path = input("Enter a directory with files to convert            Example : C:\ProgramFiles\Data\Files \n \n")
        if os.path.isdir(path):
            if not os.listdir(path):
                print("Directory is empty")
            else:
                print(f"Selected: {path}")
                break
        else:
            print("Select a proper directory")
    return path

def files_list(path):
     for file in os.listdir(path):
        if file.endswith(".tif"):
             files.append(file)

     if not files:
         print("No .tif files to convert")
         empty = True
     else:
         empty = False

     return empty

def gpkg_conversion(file_list, path):
    for file in file_list:
        print(f"Started converting {file}")

        extension = ".gpkg"
        source = os.path.join(path, file)
        split_file = os.path.splitext(file)
        new_file = split_file[0] + extension
        target = os.path.join(path, new_file)

        translate_options = gdal.TranslateOptions(format = "GPKG", outputSRS = "EPSG:2180", callback = gdal.TermProgress)
        gpkg = gdal.Translate(target, source, options = translate_options)
        gpkg = None

        converted.append(target)
        print(f"Finished converting {target}")

def overview_generation(converted):
    for file in converted:
        print(f"Started building overviews for {file}")

        overview = gdal.Open(file, 1)
        gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
        overview.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64], gdal.TermProgress)
        del overview

        built_overview.append(file)
        print(f"Finished building overviews for {file}")

def main():
    folder_path = user_input()
    empty = files_list(folder_path)
    if empty:
        main()
    input(f"\n \n Found {len(files)} files. Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    gpkg_conversion(files, folder_path)
    overview_generation(converted)
    print(f"We started with {files}")
    print(f"We converted following files {converted}")
    print(f"We calculated overviews for following files {built_overview}")

main()

input("\n \n \n PROCESSING DONE, PRESS ANY KEY TO EXIT \n \n \n")

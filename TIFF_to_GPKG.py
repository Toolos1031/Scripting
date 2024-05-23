import os
from osgeo import gdal

# Empty lists
tif_files = []
converted_files = []
built_overviews = []

# Some inputs
gdal.TermProgress = gdal.TermProgress_nocb

# Basic info
print("------------------------------TIFF to GPKG Converter------------------------------ \n")
print("Version - v.1.0 \n")
print("This program takes any orthophoto in a .tif format and converts it into GeoPackage \n")
print("For the program to work properly, please enter a directory with files to convert \n")
print("The program won't start untill you set the directory properly \n")
print("---------------------------------------------------------------------------------- \n \n")


def get_user_input():
    """Prompt user to enter a directory path and validate it"""
    while True:
        path = input("Enter a directory with files to convert (e.g., C:\\ProgramFiles\\Data\\Files): \n")
        if os.path.isdir(path):
            if not os.listdir(path):
                print("Directory is empty")
            else:
                print(f"Selected: {path}")
                break
        else:
            print("Select a proper directory")
    return path

def list_tif_files(path):
     """List all .tif files in the given directory"""
     for file in os.listdir(path):
        if file.endswith(".tif"):
             tif_files.append(file)

     if not tif_files:
         print("No .tif files to convert")
         return True
     return False

def convert_to_gpkg(file_list, path, epsg_code):
    """Convert .tif files to .gpkg format"""
    for file in file_list:
        print(f"Started converting {file}")
        source = os.path.join(path, file)
        target = os.path.join(path, os.path.splitext(file)[0] + ".gpkg")

        try:
            translate_options = gdal.TranslateOptions(format = "GPKG", outputSRS = f"EPSG:{epsg_code}", callback = gdal.TermProgress)
            gdal.Translate(target, source, options = translate_options)
            converted_files.append(target)
            print(f"Finished converting {target}")
        except Exception as e:
            print(f"Error converting {file}: {e}")

def generate_overviews(converted_files):
    """Generate overviews for converted .gpkg files"""
    for file in converted_files:
        print(f"Started building overviews for {file}")

        try:
            overview = gdal.Open(file, 1)
            gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
            overview.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64], gdal.TermProgress)
            del overview
            built_overviews.append(file)
            print(f"Finished building overviews for {file}")
        except Exception as e:
            print(f"Error building overviews for {file}: {e}")

def main():
    """Main function to orchestrate the conversion process"""
    folder_path = get_user_input()
    if list_tif_files(folder_path):
        main()
        return
    epsg_code = input("Enter an EPSG code (e.g. 2180) \n")
    input(f"\n \n Found {len(tif_files)} files. Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    convert_to_gpkg(tif_files, folder_path, epsg_code)
    generate_overviews(converted_files)
    print(f"Started with {tif_files}")
    print(f"Converted following files {converted_files}")
    print(f"Built overviews for following files {built_overviews}")

if __name__ == "__main__":
    main()
    input("\n \n \n PROCESSING DONE, PRESS ANY KEY TO EXIT \n \n \n")

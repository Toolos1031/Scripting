import os
from osgeo import gdal

# Empty lists
tif_files = []
converted_files = []
built_overviews = []

# Some inputs
gdal.TermProgress = gdal.TermProgress_nocb


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

def get_output():
    """Prompt user to enter an empty output directory and validate it"""
    while True:
        out_path = input("Enter an empty directory for output (e.g., C:\\ProgramFiles\\Data\\Files): \n")
        if os.path.isdir(out_path):
            if not os.listdir(out_path):
                print(f"Selected: {out_path}")
                break
            else:
                print("Directory is not empty")
        else:
            print("Select a proper directory")
    return out_path


def compress(file_list, path, output_path, epsg_code):
    """Convert .tif files to .gpkg format"""
    for file in file_list:
        print(f"Started compressing {file}")
        source = os.path.join(path, file)
        target = os.path.join(output_path, file)

        try:
            translate_options = gdal.TranslateOptions(format = "GTiff", outputSRS = f"EPSG:{epsg_code}", creationOptions = ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"], callback = gdal.TermProgress)
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
    output_path = get_output()
    if list_tif_files(folder_path):
        main()
        return
    epsg_code = input("Enter an EPSG code (e.g. 2180) \n")
    input(f"\n \n Found {len(tif_files)} files. Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    compress(tif_files, folder_path, output_path, epsg_code)
    generate_overviews(converted_files)
    print(f"Started with {tif_files}")
    print(f"Compressed following files {converted_files}")
    print(f"Built overviews for following files {built_overviews}")

if __name__ == "__main__":
    main()
    input("\n \n \n PROCESSING DONE, PRESS ANY KEY TO EXIT \n \n \n")

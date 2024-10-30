import os
from osgeo import gdal

# Empty lists
tif_files = []
converted_files = []

# Some inputs
gdal.TermProgress = gdal.TermProgress_nocb


def get_user_input():
    """Prompt user to enter a directory path and validate it"""
    while True:
        path = input("Enter a directory with files to separate (e.g., C:\\ProgramFiles\\Data\\Files): \n")
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
         print("No .tif files to separate")
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


def separate(file_list, path, output_path, epsg_code):
    """Separate bands in .tif files separate files"""
    for file in file_list:
        print(f"Started separating {file}")
        source = os.path.join(path, file)
        target_reflectance = os.path.join(output_path, os.path.splitext(file)[0] + "_reflectance.tif")
        target_NDVI = os.path.join(output_path, os.path.splitext(file)[0] + "_NDVI.tif")

        try:
            translate_options_reflectance = gdal.TranslateOptions(format = "GTiff", bandList= ["1", "2", "3", "4", "5"], outputSRS = f"EPSG:{epsg_code}", creationOptions = ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"], callback = gdal.TermProgress)
            translate_options_NDVI = gdal.TranslateOptions(format = "GTiff", bandList= ["6"], outputSRS = f"EPSG:{epsg_code}", creationOptions = ["COMPRESS=LZW", "PREDICTOR=2", "BIGTIFF=YES"], callback = gdal.TermProgress)
            gdal.Translate(target_reflectance, source, options = translate_options_reflectance)
            gdal.Translate(target_NDVI, source, options = translate_options_NDVI)
            converted_files.append(file)
            print(f"Finished separating {file}")
        except Exception as e:
            print(f"Error separating for {file}: {e}")
        
def main():
    """Main function to orchestrate the separation process"""
    folder_path = get_user_input()
    output_path = get_output()
    if list_tif_files(folder_path):
        main()
        return
    epsg_code = input("Enter an EPSG code (e.g. 2180) \n")
    input(f"\n \n Found {len(tif_files)} files. Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    separate(tif_files, folder_path, output_path, epsg_code)
    print(f"Started with {tif_files}")
    print(f"Separated following files {converted_files}")

if __name__ == "__main__":
    main()
    input("\n \n \n PROCESSING DONE, PRESS ANY KEY TO EXIT \n \n \n")

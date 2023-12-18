import os
from osgeo import gdal
import time

# Empty lists
tiles = []
clipped = []

# Some inputs
gdal.TermProgress = gdal.TermProgress_nocb

# Basic info
print("---------------------------------TIF TILE CLIPPER-------------------------------- \n")
print("Version - v.1.0 \n")
print("This program takes tiles in a .tif format and clips them using a polygon \n")
print("For the program to work properly, please enter a directory with files to convert, clip features and an empty one for output \n")
print("The program won't start untill you set the directory properly \n")
print("---------------------------------------------------------------------------------- \n \n")


def user_input_tiles():
    while True:
        tiles_path = input("Please enter the directory with tiles to clip \n \n")
        if os.path.isdir(tiles_path):
            if not os.listdir(tiles_path):
                print("Directory is empty \n")
            else:
                print(f"Selected {tiles_path} \n")
                for file in os.listdir(tiles_path):
                    if file.endswith(".tif"):
                        tiles.append(file)

                if not tiles:
                    print("No .tif files found \n")
                else:
                    print("Found: ", len(tiles), "files \n")
                    break
        else:
            print("Select a proper directory \n")
    return tiles_path

def user_input_clip():
    while True:
        clip_path = input("Please enter the path to the clip file in .gpkg format \n")
        if os.path.isfile(clip_path):
            if clip_path.endswith(".gpkg"):
                print(f"Selected {clip_path} \n")
                break
            else:
                print("Select a file with a .gpkg extension \n")
        else:
            print("Select a file \n")
    return clip_path

def user_input_clip_target():
    while True:
        target_path = input("Please enter an empty directory for clipping output \n")
        if os.path.isdir(target_path):
            if not os.listdir(target_path):
                print(f"Selected {target_path} as clipping output \n")
                break
            else:
                print("Directory is not empty \n")
    return target_path

def warp(tiles, tile_path, clip_path, target_path):
    a = 0
    for file in tiles:
        print(f"Started clipping {file} \n")

        a = a + 1
        print(f"Done {a-1} / {len(tiles)} \n")

        source = os.path.join(tile_path, file)
        target = os.path.join(target_path, file)

        warp_options = gdal.WarpOptions(format = "GTiff", cutlineDSName = clip_path, creationOptions = ["COMPRESS=LZW"], callback = gdal.TermProgress)
        warp = gdal.Warp(target, source, options=warp_options)
        warp = None

        clipped.append(target)
        print(f"Finished clipping {target} \n")

        os.system("cls")

def merge(clipped, target_path):
    name_vrt = "clipped.vrt"
    target_vrt = os.path.join(target_path, name_vrt)

    print("Started creating a .vrt file \n")

    build_options = gdal.BuildVRTOptions(srcNodata = "0", callback = gdal.TermProgress)
    vrt = gdal.BuildVRT(target_vrt, clipped, options = build_options)
    vrt = None

    print("\n Finished creating a .vrt file \n")

    print("Started converting to .gpkg \n")

    name_gpkg = "clipped.gpkg"
    target_gpkg = os.path.join(target_path, name_gpkg)

    translate_options = gdal.TranslateOptions(format = "GPKG", callback = gdal.TermProgress)
    translate = gdal.Translate(target_gpkg, target_vrt, options = translate_options)
    translate = None

    print("\n Finished converting to .gpkg \n")

    return target_gpkg

def overview(gpkg):
    print("Started building overviews \n")

    overview = gdal.Open(gpkg, 1)
    gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
    overview.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64], gdal.TermProgress)
    del overview

    print("\n Finished building overviews \n")

def main():
    tile_path = user_input_tiles()
    clip_path = user_input_clip()
    target_path = user_input_clip_target()

    input(f"\n \n Found {len(tiles)} files. Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    start_time = time.time()
    warp(tiles, tile_path, clip_path, target_path)
    #input("\n \n Tiles clipped, continue to merge them? Press any key to continue. \n \n Press Ctrl + C to abort \n \n")
    gpkg = merge(clipped, target_path)
    overview(gpkg)
    print(f"Processing took {round((time.time() - start_time)/60)} minutes")

main()

input("\n \n \n PROCESSING DONE, PRESS ANY KEY TO EXIT \n \n \n")
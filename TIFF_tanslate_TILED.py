import os
from osgeo import gdal
from tqdm import tqdm


root_folder = r"D:\___Lasy\orto"
out_folder = os.path.join(root_folder, "tiled")


files = [f for f in os.listdir(root_folder) if f.endswith(".tif")]


for file in files:
    source_file = os.path.join(root_folder, file)
    out_file = os.path.join(out_folder, file.split(".")[0], ".gpkg")

    translate_options = gdal.TranslateOptions(
        format = "GTiff", 
        outputSRS = f"EPSG:2180",
        creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES", "PREDICTOR=2", "BLOCKXSIZE=1024", "BLOCKYSIZE=1024", "NUM_THREADS=ALL_CPUS"],
        callback = gdal.TermProgress)
    gdal.Translate(out_file, source_file, options = translate_options)

from osgeo import gdal
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

gdal.TermProgress = gdal.TermProgress_nocb

root_folder = r"D:\___WodyPolskie\Gora\Przetworzone"
out_folder = r"D:\___WodyPolskie\Gora\Przetworzone\clipped_orto"
clip_folder = r"D:\___WodyPolskie\Gora\Przetworzone\clip"

tiff_files = []
clip_files = [f for f in os.listdir(clip_folder) if f.endswith(".shp")]

for dirpath, dirnames, filenames in os.walk(root_folder):
    for file in filenames:
        if file.lower().endswith(".tif"):
            full_path = os.path.join(dirpath, file)
            tiff_files.append(full_path)

#for tiff in tqdm(tiff_files, total = len(tiff_files)):
def process_raster(tiff):
    clip_name = os.path.split(tiff)[1].split(".")[0] + ".shp"
    clip_path = os.path.join(clip_folder, clip_name)

    out_path = os.path.join(out_folder, os.path.split(tiff)[1])

    overview = gdal.Open(tiff, 1)
    if overview.GetRasterBand(1).GetOverviewCount() == 0:
        gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
        overview.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64], gdal.TermProgress)
    del overview

    warp_options = gdal.WarpOptions(
        format = "GTiff",
        cutlineDSName = clip_path,
        multithread = True,
        creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES"],
        warpOptions = ["NUM_THREADS=2"],
        dstSRS = "EPSG:2180",
        cropToCutline = True,
        callback = gdal.TermProgress
    )

    warp = gdal.Warp(out_path, tiff, options = warp_options)
    warp = None
    return f"✅ {os.path.split(tiff)[1]}"

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers = 20) as executor:
        for result in tqdm(executor.map(process_raster, tiff_files), total = len(tiff_files)):
            print(result)
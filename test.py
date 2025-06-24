from osgeo import gdal
import os
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import geopandas as gpd
from shapely.geometry import box
import tempfile
from collections import defaultdict
import shutil

gdal.TermProgress = gdal.TermProgress_nocb

root_folder = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\__Przycinanie_godlo"

tif_folder = os.path.join(root_folder, "tif")
out_folder = os.path.join(root_folder, "out_tif")
joined_folder = os.path.join(root_folder, "joined_tif")
shapefile = os.path.join(root_folder, "PL1992_5000_1.shp")

tif_files = [f for f in os.listdir(tif_folder) if f.endswith(".tif")]
folder_list = [tif_folder, out_folder, joined_folder]

def check_root():
    if os.path.isdir(root_folder):
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder):
                os.mkdir(folder)
                print(f"Created folder for {name}")
    else:
        input("Root folder does not exist, PRESS ENTER TO EXIT")
        raise SystemExit(0)
    
    if not os.path.isfile(shapefile):
        input("Shapefile not found, PRESS ENTER TO EXIT")
        raise SystemExit(0)

    if not tif_files:
        input("No .tif files in directory, PRESS ENTER TO EXIT")
        raise SystemExit(0)

#for tiff in tqdm(tiff_files, total = len(tiff_files)):
def process_raster(tif):
    shape = gpd.read_file(shapefile)
    tif_path = os.path.join(tif_folder, tif)
    
    ds = gdal.Open(tif_path)
    gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    bbox = box(gt[0], gt[3] + rows * gt[5], gt[0] + cols * gt[1], gt[3])

    intersecting_polygons = shape[shape.intersects(bbox)]

    for rows, cols in intersecting_polygons.iterrows():
        single_shape = gpd.GeoDataFrame([cols], crs = "EPSG:2180")

        with tempfile.TemporaryDirectory() as tmpdir:
            temp_vector = os.path.join(tmpdir, "cutline.geojson")
            single_shape.to_file(temp_vector, driver = "GeoJSON")

            clip_name = cols["godlo"]
            out_path = os.path.join(out_folder, tif.split(".")[0] + "^" + clip_name + ".tif")

            overview = gdal.Open(tif_path, 1)
            if overview.GetRasterBand(1).GetOverviewCount() == 0:
                gdal.SetConfigOption("COMPRESS_OVERVIEW", "LZW")
                overview.BuildOverviews("NEAREST", [2, 4, 8, 16, 32, 64], gdal.TermProgress)
            del overview

            warp_options = gdal.WarpOptions(
                format = "GTiff",
                cutlineDSName = temp_vector,
                multithread = True,
                creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES"],
                warpOptions = ["NUM_THREADS=2"],
                dstSRS = "EPSG:2180",
                cropToCutline = True,
                callback = gdal.TermProgress
            )

            warp = gdal.Warp(out_path, tif_path, options = warp_options)
            warp = None

def merge_group(godlo, file_list, output_path):
    print(f"merging {godlo}")
    if len(file_list) == 1:
        shutil.copyfile(file_list[0], output_path)

    elif len(file_list) > 1:
        warp_options = gdal.WarpOptions(
            format = "GTiff",
            multithread = True,
            creationOptions = ["COMPRESS=DEFLATE", "BIGTIFF=YES"],
            warpOptions = ["NUM_THREADS=5"],
            dstSRS = "EPSG:2180",
            callback = gdal.TermProgress
        )
    
        warp = gdal.Warp(output_path, file_list, options = warp_options)
        warp = None

def merge_tiffs():
    shape = gpd.read_file(shapefile)
    all_files = [f for f in os.listdir(out_folder) if f.endswith(".tif")]
    godlo_to_files = defaultdict(list)

    for file in all_files:
        for godlo in shape["godlo"]:
            if godlo in file:
                godlo_to_files[godlo].append(os.path.join(out_folder, file))

    with ProcessPoolExecutor(max_workers = 15) as executor:
        futures = []
        
        for _, row in shape.iterrows():
            godlo = row["godlo"]
            out_path = os.path.join(joined_folder, f"{godlo}.tif")
            futures.append(executor.submit(merge_group, godlo, godlo_to_files.get(godlo, []), out_path))

        for f in tqdm(futures, desc = "Merging"):
            f.result()

def main():
    check_root()

    #with ProcessPoolExecutor(max_workers = 15) as executor:
        #list(tqdm(executor.map(process_raster, tif_files), total = len(tif_files), desc = "Clipping"))
    
    merge_tiffs()

if __name__ == "__main__":
    main()
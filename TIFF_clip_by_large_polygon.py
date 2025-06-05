import os
from osgeo import gdal
from tqdm import tqdm

gdal.TermProgress = gdal.TermProgress_nocb

root_folder = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\ortho\monster\out2"
clip_path = r"D:\___WodyPolskie\Ostrzeszow\przetwarzanie\Gotowe\clip.shp"

tiff_files = []

for dirpath, dirnames, filenames in os.walk(root_folder):
    for file in filenames:
        if file.lower().endswith(".tif"):
            print(file)
            full_path = os.path.join(dirpath, file)
            tiff_files.append(full_path)

def raster_extent(tile):
    ds = gdal.Open(tile)
    gt = ds.GetGeoTransform()
    cols = ds.RasterXSize
    rows = ds.RasterYSize
    minx = gt[0]
    maxx = gt[0] + cols * gt[1]
    miny = gt[3] + rows * gt[5]
    maxy = gt[3]

    return (minx, miny, maxx, maxy)

def clip_polygon(tile, clip_path):
    temp_clip = os.path.join(root_folder, "temp_clip.shp")

    extent = raster_extent(tile)

    minx, miny, maxx, maxy = extent

    os.system(f"ogr2ogr -clipsrc {minx} {miny} {maxx} {maxy} {temp_clip} {clip_path}")

    return temp_clip


def warp_tiles(tiles, clip_path):
    for tile in tqdm(tiles, total = len(tiles)):
        clip = clip_polygon(tile, clip_path)
        file = os.path.split(tile)[1]
        folder = os.path.split(tile)[0]

        out_folder = os.path.join(folder, "out")
        if not os.path.isdir(out_folder):
            os.makedirs(out_folder, exist_ok = True)

        out = os.path.join(out_folder, file)

        warp_options = gdal.WarpOptions(format = "GTiff", cutlineDSName = clip, creationOptions = ["COMPRESS=LZW"], dstSRS = "EPSG:2180", callback = gdal.TermProgress)
        warp = gdal.Warp(out, tile, options = warp_options)
        warp = None

        os.remove(clip)


warp_tiles(tiff_files, clip_path)

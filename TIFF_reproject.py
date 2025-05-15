from osgeo import gdal
import os
from tqdm import tqdm

gdal.TermProgress = gdal.TermProgress_nocb

folder_path = r"Y:\______Wody_Polskie\Dane_Od_Klienta\Rastry\woj. wielkopolskie\powiat krotoszyński\m_gm_kozmin_skalibrowane"
out = r"Y:\______Wody_Polskie\Dane_Od_Klienta\Rastry\woj. wielkopolskie\powiat krotoszyński\m_gm_kozmin_skalibrowane\fixed"

tiff_files = [tif for tif in os.listdir(folder_path) if tif.endswith(".tif")]

for raster in tqdm(tiff_files, total = len(tiff_files)):
    source = os.path.join(folder_path, raster)
    target = os.path.join(out, raster)

    warp_options = gdal.WarpOptions(format = "GTiff", creationOptions = ["COMPRESS=LZW"], srcSRS = "EPSG:2174", dstSRS = "EPSG:2180", callback = gdal.TermProgress)
    warp = gdal.Warp(target, source, options = warp_options)
    warp = None
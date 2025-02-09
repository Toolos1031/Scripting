from osgeo import gdal
import os

gdal.TermProgress = gdal.TermProgress_nocb


tiff_path = r"D:\____Katowice\kato_wip\orto\tif"
shp_path = r"D:\____Katowice\kato_wip\clip"
out_path = r"D:\____Katowice\kato_wip\orto\clipped_tiff"

tiffs = []
shp = []

for i in os.listdir(tiff_path):
    if i.endswith(".tif"):
        tiffs.append(i)

for j in os.listdir(shp_path):
    if j.endswith(".gpkg"):
        shp.append(j)

def clip(raster, shape):
    source = os.path.join(tiff_path, raster)
    target = os.path.join(out_path, raster)
    clipper = os.path.join(shp_path, shape)

    warp_options = gdal.WarpOptions(format = "GTiff", cutlineDSName = clipper, creationOptions = ["COMPRESS=LZW"], callback = gdal.TermProgress)
    warp = gdal.Warp(target, source, options = warp_options)
    warp = None


for shape in shp:
    shape_name = os.path.splitext(shape)[0]
    for raster in tiffs:
        raster_name = os.path.splitext(raster)[0]
        if shape_name == raster_name:
            clip(raster, shape)        


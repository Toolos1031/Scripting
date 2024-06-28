"""
import os
from osgeo import gdal

input_directory = r"D:\katowice"
output_directory = r"D:\katowice\files"

gdal.TermProgress = gdal.TermProgress_nocb

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        input_file = os.path.join(input_directory, filename)
        output_file = os.path.join(output_directory, filename)
        
        # Get current georeference information
        ds = gdal.Open(input_file)
        gt = ds.GetGeoTransform()
        minx = gt[0]
        maxy = gt[3]
        maxx = minx + (ds.RasterXSize * gt[1])
        miny = maxy + (ds.RasterYSize * gt[5])
        ds = None
        print(minx, maxy, maxx, miny)

        # Shift X coordinates by 0.04 meters
        new_miny = miny + 10
        new_maxy = maxy + 10

        translate_options = gdal.TranslateOptions(format = "GTiff", callback = gdal.TermProgress, creationOptions = ["COMPRESS=LZW"])

        # Apply the shift using gdal_translate
        #gdal.Translate(output_file, input_file, outputSRS='EPSG:2177', outputBounds=[minx, new_maxy, maxx, new_miny], options = translate_options)

print("Shift completed for all files.")
"""

import os
from osgeo import gdal

def shift_tiff(input_file, output_file, shift_y):
    # Open the input file
    ds = gdal.Open(input_file, gdal.GA_ReadOnly)
    
    # Get the current geotransform
    gt = ds.GetGeoTransform()
    
    # Modify the geotransform to shift by shift_y
    new_gt = (gt[0], gt[1], gt[2], gt[3] + shift_y, gt[4], gt[5])
    
    # Create a new file with the modified geotransform
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.CreateCopy(output_file, ds)
    out_ds.SetGeoTransform(new_gt)
    
    # Close datasets
    ds = None
    out_ds = None

input_directory = r"D:\katowice"
output_directory = r"D:\katowice\files"
shift_y = -0.04  # Shift by 10 meters

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for filename in os.listdir(input_directory):
    if filename.endswith(".tif"):
        input_file = os.path.join(input_directory, filename)
        output_file = os.path.join(output_directory, filename)
        
        shift_tiff(input_file, output_file, shift_y)

print("Shift completed for all files.")
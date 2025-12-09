import rasterio
import numpy as np
from rasterio.mask import mask
import geopandas as gpd


raster = rasterio.open(r"D:\___WodyPolskie\poprawa_chmur\krotoszyn\raster.tif")
shape_path = r"D:\___WodyPolskie\7_Krotoszyn\uzupelnianie\krotoszyn_rowy_buffer.shp"


data = raster.read(1)

vector = gpd.read_file(shape_path)
geometries = [shapes for shapes in vector.geometry]

shape_mask = rasterio.features.rasterize(
    shapes = geometries,
    out_shape = raster.shape,
    transform = raster.transform,
    all_touched = True,
    fill = 0,
    dtype = rasterio.uint8
)
shape_mask_bool = shape_mask.astype(bool)

modified_data = np.where(shape_mask_bool, data, 999).astype(data.dtype)

count_0 = np.sum(modified_data == 0)
count_gt_50 = np.sum((modified_data >= 50) & (modified_data < 999))
count_lt_50 = np.sum((modified_data > 0) & (modified_data < 50))
print(f"Count of pixels with value 0: {count_0}, percentage: {(count_0 * 100)/ (count_0 + count_gt_50 + count_lt_50)}%")
print(f"Count of pixels with value >= 50: {count_gt_50}, percentage: {(count_gt_50 * 100)/ (count_0 + count_gt_50 + count_lt_50)}%")
print(f"Count of pixels with value > 0 and < 50: {count_lt_50}, percentage: {(count_lt_50 * 100)/ (count_0 + count_gt_50 + count_lt_50)}%")
print(f"Total valid pixels: {count_0 + count_gt_50 + count_lt_50}")


# make raster with pixels with value from 0 to 50 set to 1, others to 0
binary_raster = np.where((modified_data >= 0) & (modified_data < 50), 1, 0).astype("uint8")
out_meta = raster.meta.copy()
out_meta.update({
    "height": binary_raster.shape[0],
    "width": binary_raster.shape[1],
    "count": 1,
    "dtype": "uint8" 
})
out_path = r"D:\___WodyPolskie\poprawa_chmur\krotoszyn\binary_raster2.tif"
with rasterio.open(out_path, "w", **out_meta) as dest:
    dest.write(binary_raster, 1)

raster.close()


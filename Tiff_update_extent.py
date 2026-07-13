import rasterio
from rasterio.windows import get_data_window
import glob
import os

# Get a list of all your rasters
raster_dir = r"D:\E65-geoster\orto_clipped"

raster_files = [os.path.join(raster_dir, f) for f in os.listdir(raster_dir) if f.endswith('.tif')]
output_dir = r"D:\E65-geoster\orto_clipped\cropped"

for file_path in raster_files:
    filename = os.path.basename(file_path)
    
    with rasterio.open(file_path) as src:
        # 1. Read the first band to find where the actual data is
        band1 = src.read(1)
        
        # 2. Automatically find the window that contains valid data (ignores NoData)
        # If your NoData value isn't defined in the metadata, replace src.nodata with the value (e.g., 0)
        window = get_data_window(band1, nodata=src.nodata)
        
        # 3. Read the data just for that window and get the new transform
        clipped_array = src.read(window=window)
        new_transform = src.window_transform(window)
        
        # 4. Update metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "height": window.height,
            "width": window.width,
            "transform": new_transform
        })
        
    # 5. Save the cropped file
    out_path = os.path.join(output_dir, f"cropped_{filename}")
    with rasterio.open(out_path, "w", **out_meta) as dest:
        dest.write(clipped_array)
        
    print(f"Successfully auto-cropped {filename}")
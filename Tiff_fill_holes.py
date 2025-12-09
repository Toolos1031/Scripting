import rasterio
from rasterio import features, fill
from shapely.geometry import box
import geopandas as gpd
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation
import time
from scipy import ndimage
import gc
import os
from matplotlib import pyplot
from tqdm import tqdm

# -------------- PATHS --------------
shape_path = r"D:\___WodyPolskie\3_Milicz\uzupelnianie\milicz_rowy_buffer.shp"
tile_path = r"D:\1111Przetwarzanie\PL1992_5000_1.shp"
out_folder = r"D:\___WodyPolskie\clipping_rastry\Milicz\out"
folder_path = r"D:\___WodyPolskie\clipping_rastry\Milicz\in"
# -----------------------------------

# -------------- PARAMETERS --------------
FACTOR = 10  # downsampling factor for hole filling
MAX_SEARCH_DISTANCE = 200  # max search distance in original resolution
MARGIN = 3  # margin around hole components in low resolution
SIGMA = 1.0  # Gaussian smoothing sigma
RASTER_DTYPE = np.uint8  # output data type
COMPRESS = "LZW"  # compression type
TILED = True  # whether to use tiling
BLOCK_SIZE = 512  # block size for tiling
BIGTIFF = "IF_SAFER"  # BigTIFF option
SPARSE_OK = True  # whether to allow sparse files
# ---------------------------------------

# Get list of rasters to process
rasters = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".tif")]

# Function to fill holes locally
def fill_holes_locally(
        clipped_image: np.ndarray,
        combined_mask_lr: np.ndarray,
        max_search_distance: int,
        margin: int
):
    
    image = clipped_image
    del clipped_image
    gc.collect()

    bands, height, width = image.shape
    
    structure = np.array(
        [[0,1,0],
         [1,1,1],
         [0,1,0]],
        dtype=bool
    )

    # Label connected components of holes in the low-resolution combined mask
    labels, num = ndimage.label(combined_mask_lr == 0, structure=structure)

    for label_id in range(1, num + 1):
        component_mask = labels == label_id
        if not component_mask.any(): # Skip empty components
            continue

        # Find bounding box of the component
        rows, cols = np.where(component_mask)
        rmin, rmax = rows.min(), rows.max()
        cmin, cmax = cols.min(), cols.max()

        # Expand bounding box by margin
        r0 = max(rmin - margin, 0)
        r1 = min(rmax + margin + 1, height)
        c0 = max(cmin - margin, 0)
        c1 = min(cmax + margin + 1, width)

        # Extract local window
        local_data = image[:, r0:r1, c0:c1]
        local_mask = combined_mask_lr[r0:r1, c0:c1]

        # Expand hole regions in local mask
        mask_expanded = binary_dilation(local_mask == 0, iterations = 2)
        local_mask = np.where(mask_expanded, 0, 1).astype(np.uint8)

        # Skip if no holes in local mask
        if not (local_mask == 0).any():
            continue

        # Run fillnodata per band in local window
        for b in range(bands):
            band = local_data[b]
            band_filled = fill.fillnodata(
                band,
                mask=local_mask,
                max_search_distance=max_search_distance,
                smoothing_iterations=0
            )

            local_data[b] = band_filled
    
        # Smooth filled areas to blend with surroundings
        smoothed = gaussian_filter(local_data, sigma = (0, SIGMA, SIGMA))

        # Combine smoothed filled areas with original data
        final = np.where(local_mask == 0, smoothed, local_data)

        # Put filled data back into main array
        image[:, r0:r1, c0:c1] = final

    return image

# Process each raster file
for file_path in tqdm(rasters, total = len(rasters), desc = "Processing rasters"):

    with rasterio.open(file_path) as src:

        raster_name = file_path.split("\\")[-1].split(".")[0]

        # Load vector data
        vector = gpd.read_file(shape_path)
        tile = gpd.read_file(tile_path)
        selected_tile = tile[tile["godlo"] == raster_name]

        # Create clipping geometry from raster bounds
        clip_geom = box(src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)
        clipped = vector.clip(clip_geom)
        clipped_buffered = clipped.buffer(15)

        clipped_vector = clipped_buffered.clip(selected_tile)
        clipped_vector_not_buffered = clipped.clip(selected_tile)

        # Prepare geometries for rasterio rasterization
        geom = [shapes for shapes in clipped_vector.geometry]
        not_buffered_geom = [shapes for shapes in clipped_vector_not_buffered.geometry]
        
        # Read original masks
        raster_mask = src.read_masks()

        # Invert mask: 1 = hole, 255 = valid data. Working with first band only
        switched_mask = np.where(raster_mask[0] == 0, 1, raster_mask[0])

        # Create shape mask from vector geometries
        shape_mask = features.rasterize(shapes = geom, out_shape = (src.height, src.width), transform = src.transform, all_touched = True, fill = 0, dtype = rasterio.uint8)
        non_buff_shape_mask = features.rasterize(shapes = not_buffered_geom, out_shape = (src.height, src.width), transform = src.transform, all_touched = True, fill = 0, dtype = rasterio.uint8)

        # Combine both masks: 255 = valid data, 0 = hole, 1 = outside polygon, then turn to boolean
        combined_mask = (switched_mask * shape_mask)

        combined_switched = np.where((combined_mask == 0) | (combined_mask == 1), combined_mask^1, combined_mask)
    
        combined_bool = np.where(combined_switched == 0, 0, 1)

        # Cleanup intermediate variables
        del geom, clip_geom, clipped, clipped_buffered, clipped_vector, raster_mask, switched_mask, shape_mask, combined_mask, combined_switched
        gc.collect()

        # Downsample image and masks for hole filling
        image_full = src.read()
        bands, H, W = image_full.shape
        holes_full = (combined_bool == 0)

        # Trim dimensions to be divisible by FACTOR
        H_trim = (H // FACTOR) * FACTOR
        W_trim = (W // FACTOR) * FACTOR

        # Trim images and masks to trimmed dimensions
        image_trim = image_full[:, :H_trim, :W_trim]
        holes_trim = combined_bool[:H_trim, :W_trim]

        # Downsample image and holes mask
        image_lr = image_trim[:, ::FACTOR, ::FACTOR]
        H_lr, W_lr = image_lr.shape[1], image_lr.shape[2]

        holes_lr = holes_trim.reshape(
            H_lr, FACTOR,
            W_lr, FACTOR
        ).any(axis = (1, 3))

        # Create low-resolution combined boolean mask
        combined_bool_lr = np.where(holes_lr, 1, 0).astype(np.uint8)

        # Fill holes locally
        filled = fill_holes_locally(
            clipped_image=image_lr,
            combined_mask_lr=combined_bool_lr,
            max_search_distance=MAX_SEARCH_DISTANCE // FACTOR,
            margin=MARGIN
        )

        # Upsample filled image back to original resolution
        filled_lr_up = filled.repeat(FACTOR, axis = 1).repeat(FACTOR, axis = 2)

        # Integrate filled areas back into full-resolution image
        holes_full_trim = holes_full[:H_trim, :W_trim]

        # Replace hole areas in full-resolution image with filled data
        image_full[:, :H_trim, :W_trim] = np.where(
            holes_full_trim[np.newaxis, :, :],
            filled_lr_up,
            image_full[:, :H_trim, :W_trim]
        )

        del combined_bool
        gc.collect()
        
        # Create final clipped image using non-buffered shape mask
        mask_bool = non_buff_shape_mask.astype(bool)
        nodata = src.nodata if src.nodata is not None else 0
        clipped_image = np.where(mask_bool, image_full, nodata).astype(filled.dtype)

        # Prepare output metadata
        out_meta = src.meta.copy()
        out_meta.update({
            "height": clipped_image.shape[1],
            "width": clipped_image.shape[2],
            "count": clipped_image.shape[0],
            "dtype": RASTER_DTYPE,
            #"nodata": nodata
            "compress": COMPRESS,
            "tiled": TILED,
            "blockxsize": BLOCK_SIZE,
            "blockysize": BLOCK_SIZE,
            "BIGTIFF": BIGTIFF,
            "SPARSE_OK": SPARSE_OK
        })

        file_name = file_path.split("\\")[-1]
        out_path = os.path.join(out_folder, file_name)
        
        # Write output raster
        with rasterio.open(
            out_path,
            "w",
            **out_meta
        ) as dst:
            for idx, array in enumerate(clipped_image, start=1):
                dst.write(array, idx)


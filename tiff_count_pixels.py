import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import os
from tqdm import tqdm


### CONFIG
ROOT_DIR = r"D:\___WodyPolskie\1_Gora\uzupelnianie"
RASTER_DIR = os.path.join(ROOT_DIR, "tif")
SHAPE_PATH = os.path.join(ROOT_DIR, "gora_rowy_buffer.shp")
TILE_PATH = r"D:\1111Przetwarzanie\PL1992_5000_1.shp"
OUTPUT_CSV = os.path.join(ROOT_DIR, "gora_stats.csv")

def stats_for_raster(raster, union_geom, gdf_tiles):

    raster_name = raster.split("\\")[-1].split(".")[0]
    tile_geom = gdf_tiles[gdf_tiles["godlo"] == raster_name].geometry.values[0]

    with rasterio.open(raster) as src:
        data_orig = src.read(1)

        # first clip
        out_poly, _ = mask(
            src,
            union_geom,
            crop = False,
            filled = True,
            nodata = 255
        )

        # second clip to tile
        out_tile, _ = mask(
            src,
            [tile_geom],
            crop = False,
            filled = True,
            nodata = 255
        )

    mask_poly = out_poly[0] != 255
    mask_tile = out_tile[0] != 255

    combined_mask = mask_poly & mask_tile

    inside_vals = data_orig[combined_mask]

    
    total_valid = inside_vals.size
    if total_valid > 0:
        count_1 = int(np.count_nonzero(inside_vals == 1))
        count_0 = int(np.count_nonzero(inside_vals == 0))
        percentage = (count_0 * 100) / total_valid

        if percentage >= 95:
            valid_flag = "ok"
        else:
            valid_flag = "TOO EMPTY"

        return {
            "raster_name": raster.split("\\")[-1],
            "total_pixels_inside_aoi": total_valid,
            "count_1": count_1,
            "count_0": count_0,
            "percent": percentage,
            "valid": valid_flag
            }
    else:
        print(f"WARNING: No valid pixels inside AOI for raster {raster}")
        return {
            "raster_name": raster.split("\\")[-1],
            "total_pixels_inside_aoi": 0,
            "count_1": 0,
            "count_0": 0,
            "percent": 0,
            "valid": "NO DATA"
            }

def main():

    raster_files = [os.path.join(RASTER_DIR, f) for f in os.listdir(RASTER_DIR) if f.endswith(".tif")]

    results = []

    gdf = gpd.read_file(SHAPE_PATH)
    union_geom = gdf.unary_union

    gdf_tiles = gpd.read_file(TILE_PATH)

    for raster in tqdm(raster_files, total = len(raster_files), desc = "Calculating statistics"):

        stats = stats_for_raster(raster, [union_geom], gdf_tiles)
        results.append(stats)

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index = False)

if __name__ == "__main__":
    main()


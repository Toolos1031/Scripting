import os
from pathlib import Path
from osgeo import gdal
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# -------- CONFIG --------
RASTER_DIR   = r"G:\2_Ostrzeszow\Ortofotomapa"
OUT_DIR      = r"D:\___WodyPolskie\poprawa_chmur\test_przed_wyslaniem\2_Ostrzeszow"
PATTERN      = "*.tif"

MAX_SIZE     = 2000     # longest side
FORMAT       = "JPEG"   # or "PNG"
JPG_QUALITY  = 85
# ------------------------

def process_raster(rp):
    try:
        ds = gdal.Open(str(rp), gdal.GA_ReadOnly)
        if ds is None:
            return f"FAILED open: {rp.name}"

        gt = ds.GetGeoTransform()
        w = ds.RasterXSize
        h = ds.RasterYSize

        scale = min(MAX_SIZE / w, MAX_SIZE / h, 1.0)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        out_name = rp.stem + (".jpg" if FORMAT == "JPEG" else ".png")
        out_path = str(Path(OUT_DIR) / out_name)

        translate_opts = gdal.TranslateOptions(
            format=FORMAT,
            width=new_w,
            height=new_h,
            bandList=[1,2,3],
            creationOptions=[f"QUALITY={JPG_QUALITY}"] if FORMAT == "JPEG" else []
        )

        gdal.Translate(out_path, ds, options=translate_opts)

        px_size_x = gt[1] * (1 / scale)
        px_size_y = gt[5] * (1 / scale)

        preview_gt = [
            px_size_x,
            gt[2],
            gt[4],
            px_size_y,
            gt[0],
            gt[3]
        ]

        world_ext = ".jgw" if FORMAT == "JPEG" else ".pgw"
        world_file = os.path.splitext(out_path)[0] + world_ext

        with open(world_file, "w") as f:
            f.write(f"{preview_gt[0]}\n")
            f.write(f"{preview_gt[1]}\n")
            f.write(f"{preview_gt[2]}\n")
            f.write(f"{preview_gt[3]}\n")
            f.write(f"{preview_gt[4]}\n")
            f.write(f"{preview_gt[5]}\n")

        ds = None
        return f"OK: {rp.name}"
    except Exception as e:
        return f"FAILED {rp.name}: {e}"


def main():
    Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
    rasters = sorted(Path(RASTER_DIR).glob(PATTERN))
    if not rasters:
        raise FileNotFoundError("No TIFFs found.")

    with ProcessPoolExecutor(max_workers = 10) as executor:
        futures = {executor.submit(process_raster, rp): rp for rp in rasters}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing in parallel"):
            result = future.result()
            print(result)

    print("Done. Previews + world files saved to:", OUT_DIR)


if __name__ == "__main__":
    main()

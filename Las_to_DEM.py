from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

# deps: laspy (with lazrs), rasterio, numpy, tqdm (optional), scipy
import laspy
from tqdm import tqdm
import rasterio
from rasterio.transform import Affine
from concurrent.futures import ProcessPoolExecutor, as_completed
from scipy import ndimage as ndi

# =========================
# USER SETTINGS (EDIT HERE)
# =========================
INPUT_DIR = r"D:\___WodyPolskie\Poznan\wagrowiec_classified"        # folder with .laz/.las
OUTPUT_DIR = r"D:\___WodyPolskie\Poznan\wagrowiec_NMT"              # folder for GeoTIFFs
RESOLUTION = 0.25                    # cell size in meters (0.10 = 10 cm)
NODATA = -9999.0
AGGREGATION = "mean"                  # "min" (recommended), "mean", or "max"
CHUNK_POINTS = 5_000_000             # points per chunk; adjust for memory
WORKERS = 15                          # parallel file-level workers; 8–16 is fine on 64C/256GB
FORCE_EPSG: Optional[str] = "EPSG:2180"     # e.g. "EPSG:2180"; if None, try read CRS from LAS
COMPRESS = "LZW"                     # "LZW", "DEFLATE", or None
BIGTIFF = "YES"                 # "YES", "NO", "IF_NEEDED", "IF_SAFER"
FILE_GLOB = "*.laz"                  # or ["*.laz","*.las"]

# ---- Hole filling (NEW) ----
FILL_HOLES_METERS = 2.5              # fill gaps up to this radius (meters) using nearest neighbor
ENABLE_HOLE_FILL = True              # set False to disable


def _derive_grid_bounds(hdr, res: float) -> Tuple[float, float, float, float, int, int]:
    minx, maxx = hdr.mins[0], hdr.maxs[0]
    miny, maxy = hdr.mins[1], hdr.maxs[1]
    minx_s = np.floor(minx / res) * res
    maxx_s = np.ceil (maxx / res) * res
    miny_s = np.floor(miny / res) * res
    maxy_s = np.ceil (maxy / res) * res
    width  = int(np.round((maxx_s - minx_s) / res))
    height = int(np.round((maxy_s - miny_s) / res))
    return minx_s, maxy_s, res, res, width, height  # origin_x, origin_y_top


def _try_read_crs(hdr) -> Optional[str]:
    try:
        crs = hdr.parse_crs()
        if crs and crs.to_epsg():
            return f"EPSG:{crs.to_epsg()}"
        if crs:
            return crs.to_wkt()
    except Exception:
        pass
    return None


def _aggregate_into_grid(grid_flat: np.ndarray,
                         count_flat: Optional[np.ndarray],
                         x: np.ndarray, y: np.ndarray, z: np.ndarray,
                         ox: float, oy_top: float, res: float,
                         width: int, height: int,
                         agg: str = "min") -> None:
    ix = np.floor((x - ox) / res).astype(np.int64)
    iy = np.floor((oy_top - y) / res).astype(np.int64)
    m = (ix >= 0) & (iy >= 0) & (ix < width) & (iy < height)
    if not np.any(m):
        return
    ix = ix[m]; iy = iy[m]; z = z[m]
    idx = iy * width + ix

    if agg == "min":
        np.minimum.at(grid_flat, idx, z)
    elif agg == "max":
        np.maximum.at(grid_flat, idx, z)
    elif agg == "mean":
        if count_flat is None:
            raise ValueError("count_flat required for mean aggregation")
        np.add.at(grid_flat, idx, z)
        np.add.at(count_flat, idx, 1)
    else:
        raise ValueError(f"Unknown aggregation: {agg}")


def _fill_holes_nearest(grid: np.ndarray, nodata: float, max_radius_m: float, res: float) -> np.ndarray:
    """
    Nearest-neighbor hole fill up to max_radius_m.
    Uses Euclidean Distance Transform to map each hole to the nearest valid cell.
    Only fills cells within the radius; others remain nodata.
    """
    mask_valid = grid != nodata
    if not np.any(mask_valid):
        return grid  # nothing to fill, or no valid data at all

    # EDT expects zeros as "features"; make valid cells == 0, holes == 1
    edt_input = (~mask_valid).astype(np.uint8)
    distances, (ri, ci) = ndi.distance_transform_edt(edt_input, return_indices=True)

    # convert pixel distances to meters (square cells)
    distances_m = distances * res
    fill_mask = (~mask_valid) & (distances_m <= max_radius_m)

    filled = grid.copy()
    filled[fill_mask] = grid[ri[fill_mask], ci[fill_mask]]
    return filled


def process_one_file(in_path: Path, out_dir: Path) -> Tuple[Path, bool, Optional[str]]:
    out_path = out_dir / (in_path.stem + ".tif")
    if out_path.exists():
        return out_path, True, None

    try:
        with laspy.open(in_path) as lfile:
            hdr = lfile.header
            ox, oy_top, rx, ry, width, height = _derive_grid_bounds(hdr, RESOLUTION)

            if AGGREGATION in ("min", "max"):
                fill_val = np.inf if AGGREGATION == "min" else -np.inf
                grid_flat = np.full(width * height, fill_val, dtype=np.float64)
                count_flat = None
            elif AGGREGATION == "mean":
                grid_flat = np.zeros(width * height, dtype=np.float64)
                count_flat = np.zeros(width * height, dtype=np.uint32)
            else:
                raise ValueError("AGGREGATION must be 'min', 'mean', or 'max'.")

            out_crs = FORCE_EPSG if FORCE_EPSG else _try_read_crs(hdr)

            for pts in lfile.chunk_iterator(CHUNK_POINTS):
                cls = pts.classification
                m = (cls == 2)  # ground only
                if not np.any(m):
                    continue
                x = pts.x[m]; y = pts.y[m]; z = pts.z[m]
                _aggregate_into_grid(grid_flat, count_flat, x, y, z,
                                     ox, oy_top, RESOLUTION, width, height,
                                     agg=AGGREGATION)

            if AGGREGATION == "min":
                grid_flat[np.isinf(grid_flat)] = NODATA
            elif AGGREGATION == "max":
                grid_flat[np.isneginf(grid_flat)] = NODATA
            elif AGGREGATION == "mean":
                nz = count_flat > 0
                grid_flat[~nz] = NODATA
                grid_flat[nz] = grid_flat[nz] / count_flat[nz]

            grid = grid_flat.reshape((height, width)).astype(np.float32, copy=False)

            # ---- Hole filling (NEW) ----
            if ENABLE_HOLE_FILL and FILL_HOLES_METERS and FILL_HOLES_METERS > 0:
                grid = _fill_holes_nearest(grid, NODATA, FILL_HOLES_METERS, RESOLUTION)

            transform = Affine.translation(ox, oy_top) * Affine.scale(RESOLUTION, -RESOLUTION)
            profile = {
                "driver": "GTiff",
                "height": height,
                "width": width,
                "count": 1,
                "dtype": "float32",
                "crs": out_crs,
                "transform": transform,
                "nodata": NODATA,
                "tiled": True,
                "compress": COMPRESS if COMPRESS else "NONE",
                "BIGTIFF": BIGTIFF,
                "blockxsize": 512,
                "blockysize": 512,
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            with rasterio.open(out_path, "w", **profile) as dst:
                dst.write(grid, 1)

        return out_path, True, None

    except Exception as exc:
        return out_path, False, str(exc)


def main():
    in_dir = Path(INPUT_DIR)
    out_dir = Path(OUTPUT_DIR)
    patterns = FILE_GLOB if isinstance(FILE_GLOB, (list, tuple)) else [FILE_GLOB]
    files = []
    for pat in patterns:
        files.extend(in_dir.glob(pat))
    if FILE_GLOB == "*.laz":
        files.extend(in_dir.glob("*.las"))
    files = sorted(set(files))

    if not files:
        print(f"No matching files in {in_dir}")
        return

    print(f"Found {len(files)} files.")
    if WORKERS and WORKERS > 1:
        with ProcessPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(process_one_file, f, out_dir): f for f in files}
            for fut in tqdm(as_completed(futs), total=len(futs), desc="Processing"):
                out_path, ok, err = fut.result()
                if not ok:
                    print(f"[FAIL] {out_path.name}: {err}")
    else:
        for f in tqdm(files, desc="Processing", unit="file"):
            out_path, ok, err = process_one_file(f, out_dir)
            if not ok:
                print(f"[FAIL] {out_path.name}: {err}")

    print("Done.")


if __name__ == "__main__":
    main()
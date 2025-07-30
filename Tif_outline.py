import os
from glob import glob
from shapely.geometry import box
import geopandas as gpd
import rasterio
from concurrent.futures import ProcessPoolExecutor, as_completed

def get_raster_bbox(tif_path):
    try:
        with rasterio.open(tif_path) as src:
            bbox = box(*src.bounds)
            return {
                "geometry": bbox,
                "filename": os.path.basename(tif_path),
                "crs": src.crs.to_string() if src.crs else "EPSG:4326"
            }
    except Exception as e:
        return {"error": str(e), "filename": os.path.basename(tif_path)}

def process_rasters_to_gpkg(tif_folder, output_gpkg, max_workers=8):
    tif_files = glob(os.path.join(tif_folder, "*.tif"))
    results = []
    crs = None

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(get_raster_bbox, tif): tif for tif in tif_files}
        for future in as_completed(future_to_file):
            try:
                result = future.result()
                if "error" in result:
                    print(f"❌ Failed: {result['filename']} — {result['error']}")
                    continue
                if crs is None:
                    crs = result["crs"]
                results.append({
                    "geometry": result["geometry"],
                    "filename": result["filename"]
                })
                print(f"✅ Processed: {result['filename']}")
            except Exception as exc:
                print(f"🔥 Unexpected error: {exc}")

    if results:
        gdf = gpd.GeoDataFrame(results, crs=crs)
        gdf.to_file(output_gpkg, driver="GPKG")
        print(f"\n🎉 Done! Saved {len(gdf)} bounding boxes to {output_gpkg}")
    else:
        print("⚠️ No valid raster bounding boxes were saved.")

# Example usage
if __name__ == "__main__":
    process_rasters_to_gpkg(
        tif_folder=r"D:\1111Przetwarzanie\JOINING_TIF\raw\together",     # ⬅️ Change this
        output_gpkg=r"D:\1111Przetwarzanie\JOINING_TIF\raw\raster_bboxes.gpkg",
        max_workers=8
    )
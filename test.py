import os
import glob
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from osgeo import gdal, ogr, osr

gdal.UseExceptions()
ogr.UseExceptions()

def footprint_from_alpha_one(
    raster_path: str,
    out_gpkg: str,
    alpha_band_index: int = 4,
    eight_connected: bool = True,
    tmp_layer: str = "raw",
    out_layer: str = "outline",
):
    ds = gdal.Open(raster_path, gdal.GA_ReadOnly)
    if ds is None:
        raise RuntimeError(f"Cannot open raster: {raster_path}")

    if ds.RasterCount < alpha_band_index:
        raise RuntimeError(f"{raster_path}: has {ds.RasterCount} bands, no alpha band {alpha_band_index}")

    band = ds.GetRasterBand(alpha_band_index)

    # Prepare output
    os.makedirs(os.path.dirname(out_gpkg), exist_ok=True)
    if os.path.exists(out_gpkg):
        os.remove(out_gpkg)

    drv = ogr.GetDriverByName("GPKG")
    out_ds = drv.CreateDataSource(out_gpkg)

    # Spatial reference
    wkt = ds.GetProjection()
    srs = osr.SpatialReference()
    if wkt:
        srs.ImportFromWkt(wkt)
    else:
        srs = None

    raw = out_ds.CreateLayer(tmp_layer, srs=srs, geom_type=ogr.wkbPolygon)
    raw.CreateField(ogr.FieldDefn("DN", ogr.OFTInteger))

    opts = []
    if eight_connected:
        opts.append("8CONNECTED=8")

    # Polygonize alpha values into DN
    gdal.Polygonize(band, None, raw, 0, opts)

    raw.SyncToDisk()

    # Dissolve DN>0 using SQLite dialect + GEOS
    sql = f"SELECT ST_Union(geom) AS geom FROM {tmp_layer} WHERE DN > 0"
    dissolved_lyr = out_ds.ExecuteSQL(sql, dialect="SQLITE")
    if dissolved_lyr is None:
        raise RuntimeError(f"{raster_path}: dissolve SQL returned no layer")

    feat = dissolved_lyr.GetNextFeature()
    if feat is None:
        out_ds.ReleaseResultSet(dissolved_lyr)
        raise RuntimeError(f"{raster_path}: dissolve produced no geometry (no DN>0?)")

    geom = feat.GetGeometryRef()
    if geom is None or geom.IsEmpty():
        out_ds.ReleaseResultSet(dissolved_lyr)
        raise RuntimeError(f"{raster_path}: dissolve geometry empty")

    # Fix minor topology issues
    geom = geom.Buffer(0)

    out_ds.ReleaseResultSet(dissolved_lyr)

    # Write final outline layer
    outL = out_ds.CreateLayer(out_layer, srs=srs, geom_type=geom.GetGeometryType())
    outL.CreateField(ogr.FieldDefn("id", ogr.OFTInteger))

    outF = ogr.Feature(outL.GetLayerDefn())
    outF.SetField("id", 1)
    outF.SetGeometry(geom)
    outL.CreateFeature(outF)
    outL.SyncToDisk()

    # Cleanup: optionally drop raw layer to keep outputs small
    out_ds.DeleteLayer(tmp_layer)

    out_ds = None
    ds = None


def _worker(args):
    raster_path, out_gpkg, alpha_band_index, eight_connected = args
    try:
        footprint_from_alpha_one(
            raster_path=raster_path,
            out_gpkg=out_gpkg,
            alpha_band_index=alpha_band_index,
            eight_connected=eight_connected,
        )
        return (raster_path, True, "")
    except Exception:
        return (raster_path, False, traceback.format_exc())


def batch_process(
    in_glob: str,
    out_dir: str,
    workers: int = 16,            # tune this (see notes below)
    alpha_band_index: int = 4,
    eight_connected: bool = True,
    skip_existing: bool = True,
):
    rasters = sorted(glob.glob(in_glob))
    if not rasters:
        raise RuntimeError(f"No inputs matched: {in_glob}")

    tasks = []
    for rp in rasters:
        base = os.path.splitext(os.path.basename(rp))[0]
        out_gpkg = os.path.join(out_dir, f"{base}_outline.gpkg")
        if skip_existing and os.path.exists(out_gpkg):
            continue
        tasks.append((rp, out_gpkg, alpha_band_index, eight_connected))

    print(f"Inputs matched: {len(rasters)}")
    print(f"To process:     {len(tasks)}")
    os.makedirs(out_dir, exist_ok=True)


    os.environ.setdefault("GDAL_CACHEMAX", "2048") 
    os.environ.setdefault("OGR_SQLITE_SYNCHRONOUS", "OFF") 

    ok = 0
    bad = 0

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_worker, t) for t in tasks]
        for f in as_completed(futs):
            rp, success, msg = f.result()
            if success:
                ok += 1
                print(f"[OK]  {os.path.basename(rp)}")
            else:
                bad += 1
                print(f"[ERR] {os.path.basename(rp)}\n{msg}")

    print(f"\nDone. OK={ok}, ERR={bad}")


if __name__ == "__main__":
    batch_process(
        in_glob=r"D:\___WodyPolskie\clipping_rastry\piramidy\krotoszyn_wypelnione\*.tif",
        out_dir=r"D:\___WodyPolskie\clipping_rastry\piramidy\krotoszyn_outline",
        workers=16,         
        alpha_band_index=4,
        eight_connected=True,
        skip_existing=True,
    )

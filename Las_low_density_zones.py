import numpy as np
import laspy
from rasterio.transform import from_origin
import rasterio
from osgeo import gdal, ogr, osr
from shapely.geometry import Polygon
import geopandas as gpd
from shapely import wkt
import os
from tqdm import tqdm
import tempfile

### Setup ###
root_folder = r"D:\WODY_testy\zakrety"
las_folder = os.path.join(root_folder, "las")
poly_folder = os.path.join(root_folder, "poly")
tif_folder = os.path.join(root_folder, "tif")

folder_list = [las_folder, poly_folder, tif_folder]


def check_root():
    if os.path.isdir(root_folder): # Check if the root path, and other dirs exits
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder): # If not we can create them
                os.mkdir(folder)
                print(f"Created folder for {name}")
            else:
                print(f"Folder for {name} found")
    else:
        input("Root folder does not exist, PRESS ENTER TO EXIT") # When missing the root folder, exit
        raise SystemExit(0)
            
def process_scans(scan):
    las_path = os.path.join(las_folder, scan)
    las = laspy.read(las_path)

    points = np.column_stack((las.x, las.y, las.z)) # Convert to numpy vertical array

    cell_size = 1 # Size of the resulting raster

    x = points[:, 0]
    y = points[:, 1]

    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()

    x_edges = np.arange(xmin, xmax + cell_size, cell_size) # Create a bbox for the raster
    y_edges = np.arange(ymin, ymax + cell_size, cell_size)

    density, x_edges, y_edges = np.histogram2d(x, y, bins = [x_edges, y_edges])

    density_raster = np.flipud(density.T) # Flip it vertically, cause for whatever reason its upside down

    binary_raster = np.where((density_raster > 0) & (density_raster < 50), 1, 0) # Get only values that are within the scan (>0) and lower than our goal (<50) and make it binary

    transform = from_origin(xmin, ymax, cell_size, cell_size) # Transform it back to original location

    raster_path = os.path.join(tif_folder, scan.split(".")[0] + ".tif")

    with rasterio.open( # Save the binary raster
        raster_path,
        "w",
        driver = "GTiff",
        height = binary_raster.shape[0],
        width = binary_raster.shape[1],
        count = 1,
        dtype = binary_raster.dtype,
        crs = "EPSG:2180",
        transform = transform
    ) as dst:
        dst.write(binary_raster, 1)

def process_raster(tif):
    with tempfile.TemporaryDirectory() as tmpdir:
        raster_path = os.path.join(tif_folder, tif)
        #poly_path = os.path.join(temp_folder, tif.split(".")[0] + ".shp")
        poly_path = f"{tmpdir}/out.shp"

        raster = gdal.Open(raster_path)
        raster_band = raster.GetRasterBand(1)

        driver = ogr.GetDriverByName("ESRI Shapefile") # Set up the output shapefile
        out_ds = driver.CreateDataSource(poly_path)

        srs = osr.SpatialReference() # Set the CRS
        srs.ImportFromEPSG(2180)

        out_layer = out_ds.CreateLayer("polygonized", srs, geom_type = ogr.wkbPolygon) # Create layer

        field_defn = ogr.FieldDefn("DN", ogr.OFTInteger) # Create attributes
        out_layer.CreateField(field_defn)

        gdal.Polygonize(raster_band, None, out_layer, 0, [], callback = None) # Polygonize the raster and save in shp

        raster = None # Clear gdal
        out_ds = None

        shape = gpd.read_file(poly_path) # Read the poly and convert to gpd

        max_idx = shape.geometry.area.idxmax() # Get the biggest poly and remove it
        shape = shape.drop(index = max_idx)

        indices_to_drop = []

        for cols, rows in shape.iterrows(): # Also detele each poly smaller than
            if rows["geometry"].area < 20:
                indices_to_drop.append(cols)

        shape = shape.drop(index = indices_to_drop)

        list_interiors = []
        polygons = []

        for cols, rows in shape.iterrows():
            poly = wkt.loads(str(rows["geometry"])) # Convert to WKT

            poly = poly.buffer(2)

            for interior in poly.interiors: # Find all holes smaller than 20, big holes are allowed
                p = Polygon(interior)
                if p.area > 20:
                    list_interiors.append(interior)

            new_polygon = Polygon(poly.exterior.coords, holes = list_interiors) 
            polygons.append(new_polygon)


        polys = gpd.GeoDataFrame({"geometry" : polygons}) # Go back to gpd

        polys.set_crs("EPSG:2180", inplace = True)

        polys["geometry"] = polys["geometry"].simplify(tolerance = 5, preserve_topology = True) # At the end simplify it

        poly_path = os.path.join(poly_folder, tif.split(".")[0] + ".shp")
        polys.to_file(poly_path)

if __name__ == "__main__":
    check_root()
    scan_files = [scan_file for scan_file in os.listdir(las_folder) if scan_file.endswith(".las")]

    for scan in tqdm(scan_files, total = len(scan_files)):
        tif = scan.split(".")[0] + ".tif"
        process_scans(scan)
        process_raster(tif)

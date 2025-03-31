from shapely.geometry import Point, box
import geopandas as gpd
import laspy
import numpy as np
import os
from tqdm import tqdm
from multiprocessing import Pool

### SETUP

poly_path = r"D:\WODY_testy\clipping\profiles.shp"
scan_folder = r"D:\WODY_testy\clipping"
out_folder = r"D:\WODY_testy\clipping\out"


# Function for calculating the extent of a laserscan
def bbox(scan):
    scan_extent = {
        "xmin" : scan.header.mins[0],
        "xmax" : scan.header.maxs[0],
        'ymin' : scan.header.mins[1],
        "ymax" : scan.header.maxs[1]
    }

    scan_bbox = box(
        scan_extent["xmin"],
        scan_extent["ymin"],
        scan_extent["xmax"],
        scan_extent["ymax"]
    )

    return scan_bbox
# Function to check if points are inside of polygons
def check_points(args):
    chunk, polygon = args
    return [polygon.contains(Point(x, y)) for x, y in chunk]

# Main processing function
def process_scan(scan_file, shapefile, out_folder):
    scan = laspy.read(scan_file)
    points = np.vstack((scan.x, scan.y)).T # Prepare data for shapely

    intersecting_polygons = shapefile[shapefile.geometry.intersects(bbox(scan))] # Use only polygons that are intersecting the laser scan

    for rows, cols in tqdm(intersecting_polygons.iterrows(), total = len(intersecting_polygons)): # Iterate over selected polygons
    
        polygon = cols["geometry"]
        xmin, ymin, xmax, ymax = cols["geometry"].bounds # Get polygons bounding box

        polygon_mask = (
            (points[:, 0] >= xmin) & 
            (points[:, 0] <= xmax) & 
            (points[:, 1] >= ymin) & 
            (points[:, 1] <= ymax)
        ) # Mask points in the polygons bounding box

        filtered_points = points[polygon_mask] # Select points in polygons bounding box

        num_cores = 2
        chunks = np.array_split(filtered_points, num_cores)

        with Pool(num_cores) as pool: # Run pools
            results = pool.map(check_points, [(chunk, polygon) for chunk in chunks])

        inside_polygon = np.concatenate(results) # Merge results from pools

        if inside_polygon.any(): # If the result is not empty

            final_indices = np.where(polygon_mask)[0][inside_polygon] # Go back to initial array size

            clipped_scan = laspy.LasData(scan.header)
            clipped_scan.points = scan.points[final_indices].copy()

            new_filename = os.path.join(out_folder, f"{cols['id']}_{cols['distance']}.las")

            clipped_scan.write(new_filename)

if __name__ == "__main__":
    shapefile = gpd.read_file(poly_path)

    scans = [os.path.join(scan_folder, i) for i in os.listdir(scan_folder) if i.endswith(".las")]
    for scan_file in scans:
        process_scan(scan_file, shapefile, out_folder)



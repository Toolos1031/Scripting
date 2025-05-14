from shapely.geometry import Point, box
import geopandas as gpd
import laspy
import numpy as np
import os
from tqdm import tqdm
from multiprocessing import Pool
import pandas as pd
import pickle


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
def process_scan(scan_file, shapefile, out_folder, scan_name, temp_folder):
    clipped_scans = []

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

        num_cores = 32
        chunks = np.array_split(filtered_points, num_cores)

        with Pool(num_cores) as pool: # Run pools
            results = pool.map(check_points, [(chunk, polygon) for chunk in chunks])

        inside_polygon = np.concatenate(results) # Merge results from pools

        if inside_polygon.any(): # If the result is not empty

            final_indices = np.where(polygon_mask)[0][inside_polygon] # Go back to initial array size

            clipped_scan = laspy.LasData(scan.header)
            clipped_scan.points = scan.points[final_indices].copy()

            fid = round(cols["FID"])

            new_filename = os.path.join(temp_folder, f"{scan_name.split('.')[0]}-{fid}.las")
            clipped_scans.append(new_filename)

            clipped_scan.write(new_filename)
    
    cmd = 'las2las -i ' + ' '.join(clipped_scans) + f' -merged -o {out_folder + "/" + scan_name}' # Merge them together
    os.system(cmd)

def main():
    shapefile = gpd.read_file(r"D:\___WodyPolskie\Gora\Przetwarzanie\Przetworzone\Chmury_punktow\buffer.shp")
    scan_folder = r"D:\___WodyPolskie\Gora\Przetwarzanie\Przetworzone\Chmury_punktow\Jemielno" ######## TUTAJ JANKU #######
    out_folder = r"D:\___WodyPolskie\Gora\Przetwarzanie\Przetworzone\Chmury_punktow\CLIPPED"
    temp_folder = r"D:\___WodyPolskie\Gora\Przetwarzanie\Przetworzone\Chmury_punktow\TEMP_CLIPPED"

    scans = [i for i in os.listdir(scan_folder) if i.endswith(".las")]
    for scan_file in scans:
        scan_path = os.path.join(scan_folder, scan_file)
        process_scan(scan_path, shapefile, out_folder, scan_file, temp_folder)

if __name__ == "__main__":
    main()
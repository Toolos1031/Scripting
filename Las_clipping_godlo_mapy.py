import geopandas as gpd
from shapely.geometry import box, Point
import os
from tqdm import tqdm
import laspy
import numpy as np
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor
import subprocess
from collections import defaultdict

root_folder = r"D:\___WodyPolskie\Gora\laczenie"

scan_folder = os.path.join(root_folder, "las")
out_folder = os.path.join(root_folder, "clipped_godlo")
joined_folder = os.path.join(root_folder, "joined")
shapefile = os.path.join(root_folder, "PL1992_5000_1.shp")

folder_list = [out_folder, joined_folder]
las_files = [os.path.join(scan_folder, f) for f in os.listdir(scan_folder) if f.endswith(".las")]

def check_root():
    if os.path.isdir(root_folder):
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder):
                os.mkdir(folder)
                print(f"Created folder for {name}")
    else:
        input("Root folder does not exist, PRESS ENTER TO EXIT")
        raise SystemExit(0)
    
    if not os.path.isfile(shapefile):
        input("Shapefile not found, PRESS ENTER TO EXIT")
        raise SystemExit(0)

    if not las_files:
        input("No .las files in directory, PRESS ENTER TO EXIT")
        raise SystemExit(0)
    
def bbox(scan): #bounding box of the scan
    scan_extent = {
        "xmin" : scan.header.mins[0],
        "xmax" : scan.header.maxs[0],
        "ymin" : scan.header.mins[1],
        "ymax" : scan.header.maxs[1]
    }

    scan_bbox = box(
        scan_extent["xmin"],
        scan_extent["ymin"],
        scan_extent["xmax"],
        scan_extent["ymax"]
    )
    
    return scan_bbox

def check_points(args): #check if points are inside of a polygon (used for multiprocessing)
    chunk, polygon = args
    return [polygon.contains(Point(x, y)) for x, y in chunk]

def process_scans(scan_file): #main function
    las = laspy.read(scan_file)
    shape = gpd.read_file(shapefile)

    #Take las and make it usable for later
    points = np.vstack((las.x, las.y)).T 

    #Get only polygons that intersect the point cloud
    intersecting_polygons = shape[shape.geometry.intersects(bbox(las))]

    for rows, cols in intersecting_polygons.iterrows():
        print(cols['godlo'])
        print(scan_file)
        polygon = cols["geometry"]
        xmin, ymin, xmax, ymax = polygon.bounds
        
        #First layer bounding box filter - bbox of the entire polygon
        polygon_mask = (
            (points[:, 0] >= xmin) & 
            (points[:, 0] <= xmax) & 
            (points[:, 1] >= ymin) & 
            (points[:, 1] <= ymax)
        )

        filtered_points = points[polygon_mask]

        #Buffer whose bbox will fit inside the poly
        inner_polygon = polygon.buffer(-100)
        ixmin, iymin, ixmax, iymax = inner_polygon.bounds

        #bbox filter for the inside poly
        inner_bbox_mask = (
            (filtered_points[:, 0] >= ixmin) & 
            (filtered_points[:, 0] <= ixmax) & 
            (filtered_points[:, 1] >= iymin) & 
            (filtered_points[:, 1] <= iymax)
        )

        #points in the inner bounding box are assumed that are completely inside
        inner_indices = np.where(polygon_mask)[0][inner_bbox_mask]

        #remaining points (in the outer but not in inner bbox)
        border_points = filtered_points[~inner_bbox_mask]
        border_indices = np.where(polygon_mask)[0][~inner_bbox_mask]

        #split into chunks for multiprocessing
        num_cores = 16
        chunks = np.array_split(border_points, num_cores)
        index_chunks = np.array_split(border_indices, num_cores)

        with Pool(num_cores) as pool:
            results = pool.map(check_points, [(chunk, polygon) for chunk in chunks])

        #merge results from multiprocessing (these points are inside the border)
        inside_polygon = np.concatenate(results)

        """
        #if the scan is completely inside the inner bbox and not in the border
        if any(inside_polygon):
            border_final_indices = np.concatenate(index_chunks)[inside_polygon]
            #merge final indices
            final_indices = np.concatenate((inner_indices, border_final_indices))
        else:
            new_filename = os.path.join(out_folder, str(scan_file.split("\\")[-1].split(".")[0] + "^" + cols["godlo"] + ".las"))
            las.write(new_filename)
        """

        #if the clipping is not empty
        if inside_polygon.any():
            border_final_indices = np.concatenate(index_chunks)[inside_polygon]
            #merge final indices
            final_indices = np.concatenate((inner_indices, border_final_indices))

            clipped_scan = laspy.LasData(las.header)
            clipped_scan.points = las.points[final_indices].copy()

            new_filename = os.path.join(out_folder, str(scan_file.split("\\")[-1].split(".")[0] + "^" + cols["godlo"] + ".las"))
            clipped_scan.write(new_filename)

        else: #it means that the scan is completely in the inner polygon not the border
            new_filename = os.path.join(out_folder, str(scan_file.split("\\")[-1].split(".")[0] + "^" + cols["godlo"] + ".las"))
            las.write(new_filename)

def merge_files(godlo, file_list, output_path):
    if file_list:
        print(f"Merging {godlo}")
        cmd = ['lasmerge', '-i'] + file_list + ["-o", output_path]
        subprocess.run(cmd)

def merge_clouds():
    shape = gpd.read_file(shapefile)
    all_files = [f for f in os.listdir(out_folder) if f.endswith(".las")]

    godlo_to_files = defaultdict(list)
    for file in all_files:
        for godlo in shape["godlo"]:
            if godlo in file:
                godlo_to_files[godlo].append(os.path.join(out_folder, file))
    
    with ThreadPoolExecutor(max_workers = 10) as executor:
        for _, row in shape.iterrows():
            godlo = row["godlo"]
            out_path = os.path.join(joined_folder, godlo + ".las")
            executor.submit(merge_files, godlo, godlo_to_files.get(godlo, []), out_path)

def main():
    check_root()

    with ThreadPoolExecutor(max_workers = 5) as executor:
        for scan in las_files:
            executor.submit(process_scans, scan)

    merge_clouds()

if __name__ == "__main__":
    main()
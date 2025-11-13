import laspy
import numpy as np
from collections import defaultdict
from tqdm import tqdm
import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from rasterio.transform import from_origin
import rasterio
from osgeo import gdal, ogr, osr
from shapely.geometry import Polygon, Point, box
import geopandas as gpd
from shapely import wkt
from shapely.geometry.polygon import orient
import tempfile
import pandas as pd
from io import BytesIO
import random
import pyvista as pv
from multiprocessing import Pool
import subprocess
import logging

# Setup logging
logging.basicConfig(
    filename = r"D:\1111Przetwarzanie\processing_log.log",
    filemode = 'a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level = logging.ERROR
)


#Root folders dirs
root_folder = r"D:\1111Przetwarzanie"
source_folder = r"D:\1111Przetwarzanie\las"

#Output folders dirs
sampled_folder = os.path.join(root_folder, "sampled_pre_processed")
poly_folder = os.path.join(root_folder, "poly")
tif_folder = os.path.join(root_folder, "tif")
filled_folder = os.path.join(root_folder, "filled")
clipped_folder = os.path.join(root_folder, "clipped_godlo")
joined_folder = os.path.join(root_folder, "joined")
shapefile = os.path.join(root_folder, "PL1992_5000_1.shp")

#List with all folders to check for
folder_list = [sampled_folder, poly_folder, tif_folder, filled_folder, clipped_folder, joined_folder]

def check_root():
    if os.path.isdir(source_folder):
        if not os.listdir(source_folder):
            input("Source folder is empty, PRESS ENTER TO EXIT")
            raise SystemExit(0)
        else:
            print(f"Found: {len(os.listdir(source_folder))}")
    else:
        input("Source folder not found, PRESS ENTER TO EXIT")
        raise SystemExit(0)
    
    if os.path.isdir(root_folder):
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder):
                os.mkdir(folder)
                print(f"Created folder for {name}")
            else:
                print(f"Folder for {name} found")

def delete_non_rgb(scan, out_file):

    # Define colors in the scan
    red = scan.red
    blue = scan.blue
    green = scan.green

    # Mask points that have all three color information
    color_only = (red != 0) & (blue != 0) & (green != 0)

    # Take only points that are colored and create a new entity
    colored_points = scan.points[color_only].copy()
    color = laspy.LasData(scan.header)
    color.points = colored_points

    # Save it
    color.write(out_file)

def sample_indices(x, y):
    # Floor coordinates to create 1x1 m tile indices
    tile_x = np.floor(x).astype(int)
    tile_y = np.floor(y).astype(int)

    # Build a mapping from (tile_x, tile_y) to point indices 
    tile_index_dict = defaultdict(list)
    for i, (tx, ty) in enumerate(zip(tile_x, tile_y)):
        tile_index_dict[(tx, ty)].append(i)

    # Set the limit for points in one tile
    max_pts_per_tile = 100
    sampled_indices = []

    # Loop over tiles with more points than a limit and subsample
    for indices in tqdm(tile_index_dict.values(), desc = "Downsampling"):
        if len(indices) > max_pts_per_tile:
            sampled_indices.extend(np.random.choice(indices, max_pts_per_tile, replace = False))
        else:
            sampled_indices.extend(indices)

    # Go back to desired shape
    sampled_indices = np.array(sampled_indices)

    return sampled_indices

def subsample_scans(scan):
    print(f"Sampling: {scan}")
    scan_file = os.path.join(source_folder, scan)
    las = laspy.read(scan_file)

    # Take only the ground and create a new entity
    ground_only = las.classification == 2
    ground = laspy.LasData(las.header)
    ground.points = las.points[np.array(ground_only)]

    # Subsample ground points
    x, y = ground.x, ground.y
    try:
        sampled_indices = sample_indices(x, y)
    except Exception as e:
        logging.error(f"Failed to sample indices for ground {scan}: {e}")

    # Go back to laspy data style
    downsampled_ground_points = ground.points[sampled_indices].array

    # Take non ground points and create a new entity
    non_ground_only = las.classification != 2 
    non_ground = laspy.LasData(las.header)
    non_ground.points = las.points[np.array(non_ground_only)]

    # Subsample non-ground points
    x, y = non_ground.x, non_ground.y
    try:
        sampled_indices = sample_indices(x, y)
    except Exception as e:
        logging.error(f"Failed to sample indices for non_ground {scan}: {e}")

    # Go back to laspy data style
    non_ground_points = non_ground.points[sampled_indices].array

    # Concat ground and non-ground together and create a new entity
    combined_array = np.concatenate((downsampled_ground_points, non_ground_points))
    combined_points = laspy.ScaleAwarePointRecord(
        combined_array,
        las.header.point_format,
        las.header.scales,
        las.header.offsets
    )

    new_las = laspy.LasData(las.header)
    new_las.points = combined_points

    out_file = os.path.join(sampled_folder, scan)
    
    # After subsampling delete non-RGB points
    try:
        delete_non_rgb(new_las, out_file)
    except Exception as e:
        logging.error(f"Failed to delete RGB {new_las}: {e}")

def detect_low_density(scan):
    las_path = os.path.join(sampled_folder, scan)
    las = laspy.read(las_path)

    # Convert to numpy vertical array
    points = np.column_stack((las.x, las.y, las.z)) 

    # Size of the resulting raster
    cell_size = 1 

    x = points[:, 0]
    y = points[:, 1]

    xmin, xmax = x.min(), x.max()
    ymin, ymax = y.min(), y.max()

    # Create a bbox for the raster
    x_edges = np.arange(xmin, xmax + cell_size, cell_size) 
    y_edges = np.arange(ymin, ymax + cell_size, cell_size)

    density, x_edges, y_edges = np.histogram2d(x, y, bins = [x_edges, y_edges])

    # Flip it vertically, cause for whatever reason its upside down
    density_raster = np.flipud(density.T) 

    # Get only values that are within the scan (>0) and lower than our goal (<50) and make it binary
    binary_raster = np.where((density_raster > 0) & (density_raster < 50), 1, 0)
    binary_raster = binary_raster.astype("uint8")

    # Transform it back to original location
    transform = from_origin(xmin, ymax, cell_size, cell_size) 

    raster_path = os.path.join(tif_folder, scan.split(".")[0] + ".tif")

    # Save the binary raster
    with rasterio.open( 
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

    # Create an temporary directory to store all misc files
    with tempfile.TemporaryDirectory() as tmpdir:
        raster_path = os.path.join(tif_folder, tif)
        poly_path = f"{tmpdir}/out.shp"

        raster = gdal.Open(raster_path)
        raster_band = raster.GetRasterBand(1)

        # Set up the output shapefile
        driver = ogr.GetDriverByName("ESRI Shapefile") 
        out_ds = driver.CreateDataSource(poly_path)

        # Set the CRS
        srs = osr.SpatialReference() 
        srs.ImportFromEPSG(2180)

        # Create layer
        out_layer = out_ds.CreateLayer("polygonized", srs, geom_type = ogr.wkbPolygon) 
        
        # Create attributes
        field_defn = ogr.FieldDefn("DN", ogr.OFTInteger) 
        out_layer.CreateField(field_defn)

        # Polygonize the raster and save in shp
        gdal.Polygonize(raster_band, None, out_layer, 0, [], callback = None) 

        # Clear gdal
        raster = None 
        out_ds = None

        # Read the poly and convert to gpd
        shape = gpd.read_file(poly_path) 

        # Get the biggest poly and remove it
        max_idx = shape.geometry.area.idxmax() 
        shape = shape.drop(index = max_idx)

        indices_to_drop = []

        # Also delete each poly smaller than
        for cols, rows in shape.iterrows(): 
            if rows["geometry"].area < 100:
                indices_to_drop.append(cols)

        # Drop all selected polys
        shape = shape.drop(index = indices_to_drop)

        polygons = []
        list_interiors = []

        # Delete holes inside polygons
        for cols, rows in shape.iterrows():
            poly = wkt.loads(str(rows["geometry"])) # Convert to WKT

            poly = poly.buffer(4)

            if not poly.interiors:
                new_polygon = Polygon(poly.exterior.coords)
                polygons.append(new_polygon)
            else:
                for interior in poly.interiors: # Find all holes smaller than 100, big holes are allowed
                    p = Polygon(interior)
                    if p.area > 100:
                        list_interiors.append(interior)
                        new_polygon = Polygon(poly.exterior.coords, holes = list_interiors)
                        polygons.append(new_polygon)
                    else:
                        new_polygon = Polygon(poly.exterior.coords)
                        polygons.append(new_polygon)
                
        # Go back to gpd
        polys = gpd.GeoDataFrame({"geometry" : polygons}) 

        polys.set_crs("EPSG:2180", inplace = True)
        
        # Simple geometry clean up
        polys["geometry"] = polys["geometry"].buffer(0) 
        #dissolved = polys.dissolve()
        #singleparts = dissolved.explode(index_parts = False).reset_index(drop = True)

        #polys = singleparts

        # At the end simplify it
        polys["geometry"] = polys["geometry"].simplify(tolerance = 5, preserve_topology = True) 
        polys["geometry"] = polys["geometry"].apply(lambda geom: orient(geom, sign = 1.0))

        # Simple geometry clean up
        polys["geometry"] = polys["geometry"].buffer(0) 

        # Read the poly and convert to gpd. Saving and loading saves some problems from happening
        poly_path = os.path.join(poly_folder, tif.split(".")[0] + ".shp")
        polys.to_file(poly_path)
        polys = gpd.read_file(poly_path) 

        # Find single and multipolygons
        polys_singlepoly = polys[polys.geometry.type == "Polygon"]
        polys_mutlipoly = polys[polys.geometry.type == "MultiPolygon"]

        # Iterate over multipolygons and turn them into single polygons
        for cols, rows in polys_mutlipoly.iterrows():
            Series_geometries = pd.Series(rows.geometry)
            df = pd.concat([gpd.GeoDataFrame(rows, geometry = Series_geometries, crs = polys_mutlipoly.crs).T]*len(Series_geometries), ignore_index = True)
            #df["geometry"] = Series_geometries
            polys_singlepoly = pd.concat([polys_singlepoly, df])

        polys_singlepoly.reset_index(inplace = True, drop = True)
        
        # Delete polys that appear multiple times - based on their area
        for cols, rows in polys.iterrows():
            mode_idx = polys.geometry.area.mode().iloc[0]
            if rows["geometry"].area == mode_idx:
                polys = polys.drop(index = cols)

        poly_path = os.path.join(poly_folder, tif.split(".")[0] + ".shp")
        polys.to_file(poly_path)

# Run rasterization and poly processing in this pipeline, to enable multithreading

def low_density_workflow(sampled):
    tif = sampled.split(".")[0] + ".tif"
    try:
        detect_low_density(sampled)
    except Exception as e:
        logging.error(f"Failed to execute low density detection for {sampled}: {e}")

    try:
        process_raster(tif)
    except Exception as e:
        print(e)
        logging.error(f"Failed to execute tif processing for {tif}: {e}")

# Check if points are inside of the polygon. Function needed for multiprocessing
def check_points(args):
    chunk, polygon = args
    return [polygon.contains(Point(x, y)) for x, y in chunk]

def process_scans(scan_path, name, clipped_scans):
    scan = laspy.read(scan_path)

    # Get rid of all unnecessary scalar fields
    try:
        scan.intensity[:] = 0
        scan.return_number[:] = 0
        scan.number_of_returns[:] = 0
        scan.scan_direction_flag[:] = 0
        scan.scan_angle_rank[:] = 0
        scan.user_data[:] = 0
        scan.point_source_id[:] = 0
        scan.gps_time[:] = 0
    except:
        pass
    
    # Overwrite original file to preserve it
    scan.write(scan_path)

    # Prepare data for shapely
    points = np.vstack((scan.x, scan.y)).T 

    # Import polygons based on scan name
    poly = gpd.read_file(poly_folder + "/" + name.split(".")[0] + ".shp") 
    poly["area"] = poly["geometry"].area

    # For each polygon in the file
    for rows, cols in tqdm(poly.iterrows(), total = len(poly)): 
        polygon = cols["geometry"]

        # Get the polygons bounding box
        xmin, ymin, xmax, ymax = cols["geometry"].bounds 

        polygon_mask = (
            (points[:, 0] >= xmin) & 
            (points[:, 0] <= xmax) & 
            (points[:, 1] >= ymin) & 
            (points[:, 1] <= ymax)
        ) # Mask points that are inside of polygons bbox

        # Select points that area inside polygon
        filtered_points = points[polygon_mask] 

        num_cores = 5
        chunks = np.array_split(filtered_points, num_cores)

        # Select points using multiprocessing
        with Pool(num_cores) as pool: 
            results = pool.map(check_points, [(chunk, polygon) for chunk in chunks])

        # Combine all results
        inside_polygon = np.concatenate(results) 

        # If the masking result is not empty
        if inside_polygon.any(): 
            final_indices = np.where(polygon_mask)[0][inside_polygon] # Clip and go back to initial array size

            clipped_scan = laspy.LasData(scan.header) # Create a las entity for clipped points
            clipped_scan.points = scan.points[final_indices].copy() # Insert the points into las

            ground_only = clipped_scan.classification == 2 # Take only the ground and create a new entity
            ground = laspy.LasData(scan.header)
            ground.points = clipped_scan.points[np.array(ground_only)]


            number = int(cols["area"])
            area = f"{number}_{random.randint(1, 10000)}"

            buf = BytesIO() # Save the file in memory
            ground.write(buf)
            buf.seek(0)
            clipped_scans[f"{area}"] = buf
        else:
            print("fail")

# Read LAS and create PyVista object
def load_data(scan_path):
    las = laspy.read(scan_path) # Import laser scan
    points = np.column_stack((las.x, las.y, las.z))  # (N,3) array to match PyVista requirements

    point_cloud = pv.PolyData(points) # Create a PyVista PolyData object

    # If color info exists, add it as point data.
    if hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue"):
        colors = np.column_stack((las.red, las.green, las.blue))
        point_cloud.point_data["RGB"] = colors
       
    return point_cloud

def sample_points_on_mesh(point_cloud, n_points): # Triangulate and sample points on the mesh

    if int(point_cloud.n_points) > 120000:
        n_total = point_cloud.n_points
        n_sample = int(50000)
        sampled_indices = np.random.choice(n_total, size = n_sample, replace = False)

        new_pc = pv.PolyData(point_cloud.points[sampled_indices])

        for name in point_cloud.point_data:
            new_pc[name] = point_cloud.point_data[name][sampled_indices]
                
        mesh = new_pc.delaunay_2d() #Triangulate scan. Its mostly ground so 2D is acceptable
    else:
        mesh = point_cloud.delaunay_2d() #Triangulate scan. Its mostly ground so 2D is acceptable

    # Extract triangle connectivity.
    # In PyVista, faces are stored in a flat array: [3, i0, i1, i2, 3, j0, j1, j2, ...]
    faces = mesh.faces.reshape((-1, 4))
    if not np.all(faces[:, 0] == 3):
        raise ValueError("Mesh faces are not all triangles.")
    tri_indices = faces[:, 1:]  # (n_tri, 3)
    vertices = mesh.points

    # Compute areas of triangles using the cross product.
    v0 = vertices[tri_indices[:, 0]]
    v1 = vertices[tri_indices[:, 1]]
    v2 = vertices[tri_indices[:, 2]]
    tri_areas = np.linalg.norm(np.cross(v1 - v0, v2 - v0), axis=1) / 2.0
    prob = tri_areas / tri_areas.sum()
    cumulative_prob = np.cumsum(prob)

    # Choose triangles based on area.
    random_vals = np.random.rand(n_points)
    tri_choice = np.searchsorted(cumulative_prob, random_vals)

    # Generate barycentric coordinates for each sample.
    r1 = np.sqrt(np.random.rand(n_points))
    r2 = np.random.rand(n_points)
    a = 1 - r1
    b = r1 * (1 - r2)
    c = r1 * r2

    # Get the vertices of the chosen triangles.
    chosen_tris = tri_indices[tri_choice]
    p0 = vertices[chosen_tris[:, 0]]
    p1 = vertices[chosen_tris[:, 1]]
    p2 = vertices[chosen_tris[:, 2]]

    # Compute the sampled points using barycentric interpolation.
    sampled_points = (a[:, None] * p0 + b[:, None] * p1 + c[:, None] * p2)

    # If the mesh has color data ("RGB"), interpolate colors similarly.
    if "RGB" in mesh.point_data:
        colors = mesh.point_data["RGB"]
        c0 = colors[chosen_tris[:, 0]]
        c1 = colors[chosen_tris[:, 1]]
        c2 = colors[chosen_tris[:, 2]]
        sampled_colors = (a[:, None] * c0 + b[:, None] * c1 + c[:, None] * c2)
    else:
        sampled_colors = None

    return sampled_points, sampled_colors

def convert(sampled_pts, sampled_cols, temp_name, temp_dir):
    # Create a PyVista point cloud for the sampled points.
    sampled_point_cloud = pv.PolyData(sampled_pts)
    if sampled_cols is not None:
        # Clamp colors to [0, 65535] and store as integers.
        sampled_cols = np.clip(sampled_cols, 0, 65535).astype(np.uint16)
        sampled_point_cloud.point_data["RGB"] = sampled_cols

    # Save the sampled point cloud as a LAS file using laspy.
    header = laspy.LasHeader(point_format=3, version="1.2")
    las_sampled = laspy.LasData(header)
    las_sampled.x = sampled_pts[:, 0]
    las_sampled.y = sampled_pts[:, 1]
    las_sampled.z = sampled_pts[:, 2]
    if sampled_cols is not None:
        las_sampled.red = sampled_cols[:, 0]
        las_sampled.green = sampled_cols[:, 1]
        las_sampled.blue = sampled_cols[:, 2]
        las_sampled.classification[:] = 2

    try:
        file_path = os.path.join(temp_dir, f"{temp_name}.las")
        las_sampled.write(file_path)
    except:
        pass

    return file_path

def fill_gaps_for_sampled(sampled, sampled_folder, filled_folder):
    try:
        # Create a dict for clipped scans in memory
        clipped_scans = {}
        las_path = os.path.join(sampled_folder, sampled)

        process_scans(las_path, sampled, clipped_scans)

        # Process within a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            las_files = []
            las_files.append(las_path)
            
            # For each clipped scan in dict
            for key, value in clipped_scans.items():
                try:
                    # Load and return scan as a PyVista object
                    las = load_data(value)

                    key_area = key.split("_")[0]
                    poly_area = int(key_area)
                    n_sample = poly_area * 100 # Sampled points based on area
                    sampled_pts, sampled_cols = sample_points_on_mesh(las, n_sample) # Sample points

                    # Convert back to laspy format
                    file_path = convert(sampled_pts, sampled_cols, key, temp_dir)
                    las_files.append(file_path)
                except Exception as e:
                    logging.error(f"Failed to sample or convert {value}: {e}")

            # Flag to make sure that the command doenst exceed its character limit
            MAX_FILES = 120

            # Merge all parts together, If there are too many, split into parts
            try: 
                if len(las_files) > MAX_FILES:
                    temp_scan = sampled.split(".")[0] + "temp." + sampled.split(".")[1]
                    temp_path = os.path.join(filled_folder, temp_scan)
                    las_files.append(temp_path)

                    # Split command into chunks
                    chunks = [las_files[i:i + MAX_FILES] for i in range(0, len(las_files), MAX_FILES)]
                    intermediate_outputs = []

                    # All except last chunk
                    for i, chunk in enumerate(chunks[:-1]): 
                        out_temp = os.path.join(filled_folder, f"chunk_{i}.las")
                        intermediate_outputs.append(out_temp)

                        #cmd = 'las2las -i ' + ' '.join(chunk) + f' -merged -target_epsg 2180 -o "{out_temp}"'
                        #os.system(cmd)
                        cmd = ['lasmerge', '-i'] + chunk + ["-o", out_temp]
                        subprocess.run(cmd)

                    # Add the last chunk
                    final_chunk = chunks[-1] + intermediate_outputs
                    #cmd = 'las2las -i ' + ' '.join(f'"{f}"' for f in final_chunk) + f' -merged -target_epsg 2180 -o "{os.path.join(filled_folder, scan)}"'
                    #os.system(cmd)
                    cmd = ['lasmerge', '-i'] + final_chunk + ["-o", os.path.join(filled_folder, sampled)]
                    subprocess.run(cmd)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    for f in intermediate_outputs:
                        if os.path.exists(f):
                            os.remove(f)

                else:
                    #cmd = 'las2las -i ' + ' '.join(f'"{f}"' for f in las_files) + f' -merged -target_epsg 2180 -o "{os.path.join(filled_folder, scan)}"'
                    #os.system(cmd)
                    cmd = ['lasmerge', '-i'] + las_files + ["-o", os.path.join(filled_folder, sampled)]
                    subprocess.run(cmd)
                
            except Exception as e:
                logging.error(f"Failed to merge {sampled}: {e}")

    except Exception as e:
        logging.error(f"Failed to fill gaps for {sampled}: {e}")

    return sampled

# Bounding box of the scan
def bbox(scan):
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

def clip_scans(scan_file):
    try:
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

            #if the clipping is not empty
            if inside_polygon.any():
                border_final_indices = np.concatenate(index_chunks)[inside_polygon]
                #merge final indices
                final_indices = np.concatenate((inner_indices, border_final_indices))

                clipped_scan = laspy.LasData(las.header)
                clipped_scan.points = las.points[final_indices].copy()

                new_filename = os.path.join(clipped_folder, str(scan_file.split("\\")[-1].split(".")[0] + "^" + cols["godlo"] + ".las"))
                clipped_scan.write(new_filename)

            else: #it means that the scan is completely in the inner polygon not the border
                new_filename = os.path.join(clipped_folder, str(scan_file.split("\\")[-1].split(".")[0] + "^" + cols["godlo"] + ".las"))
                las.write(new_filename)
    except Exception as e:
        logging.error(f"Failed to clip scan {scan_file}: {e}")

def merge_files(godlo, file_list, output_path):
    if file_list:
        print(f"Merging {godlo}")
        cmd = ['lasmerge', '-i'] + file_list + ["-o", output_path]
        subprocess.run(cmd)

def merge_clouds():
    shape = gpd.read_file(shapefile)
    all_files = [f for f in os.listdir(clipped_folder) if f.endswith(".las")]

    godlo_to_files = defaultdict(list)
    for file in all_files:
        for godlo in shape["godlo"]:
            if godlo in file:
                godlo_to_files[godlo].append(os.path.join(clipped_folder, file))
    
    with ThreadPoolExecutor(max_workers = 10) as executor:
        for _, row in shape.iterrows():
            godlo = row["godlo"]
            out_path = os.path.join(joined_folder, godlo + ".las")
            executor.submit(merge_files, godlo, godlo_to_files.get(godlo, []), out_path)



#if __name__ == "__main__":
def main():
    # Check files before continuing
    check_root()
    
    # Loop over all .las files in the source directory
    las_files = [f for f in os.listdir(source_folder) if f.endswith(".las")]

    # Subsample Point Clouds and delete non-RGB points
    with ProcessPoolExecutor(max_workers = 5) as executor:
        futures = []

        for scan in las_files:
            futures.append(executor.submit(subsample_scans, scan))

        for f in tqdm(futures, desc = "Subsampling Point Clouds"):
            try:
                f.result()
            except Exception as e:
                logging.error(f"Failed to execute scan subsampling {f}: {e}")
    
    # On subsampled files, detect areas with low point density
    sampled_files = [f for f in os.listdir(sampled_folder) if f.endswith(".las")]

    with ProcessPoolExecutor(max_workers = 10) as executor:
        futures = {executor.submit(low_density_workflow, sampled): sampled for sampled in sampled_files}

        for future in tqdm(as_completed(futures), total = len(futures), desc = "Detecting low density zones"):
            src = futures[future]
            try:
                _ = future.result()
            except Exception as e:
                logging.error(f"Worker crashed on executing low density {src.name}: {e}")
    
    # Fill gaps in the sampled scans using created polygons
    sampled_files = [f for f in os.listdir(sampled_folder) if f.endswith(".las")]
    with ThreadPoolExecutor(max_workers = 10) as executor:
        futures = {
            executor.submit(fill_gaps_for_sampled, sampled, sampled_folder, filled_folder) : sampled for sampled in sampled_files
        }

        for future in tqdm(as_completed(futures), total = len(futures), desc = "Filling gaps in scans"):
            fname = futures[future]
            try:
                future.result()
            except Exception as e:
                logging.error(f"Worker crashed on executing gaps filling {fname}: {e}")

    """
    # Clip filled scans with godlo
    filled_scans = [os.path.join(filled_folder, f) for f in os.listdir(filled_folder) if f.endswith(".las")]

    with ThreadPoolExecutor(max_workers = 5) as executor:
        for filled in filled_scans:
            executor.submit(clip_scans, filled)

    # Merge clipped scans
    try:
        merge_clouds()
    except Exception as e:
        logging.error(f"Failed to make final merge: {e}")
    """
if __name__ == "__main__":
    main()
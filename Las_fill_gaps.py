import laspy
import numpy as np
import pyvista as pv
import os
import geopandas as gpd
from tqdm import tqdm
from shapely.geometry import Point
from multiprocessing import Pool
from io import BytesIO
import tempfile

### SETUP
root_folder = r"D:\WODY_testy\zakrety"
las_folder = os.path.join(root_folder, "las")
poly_folder = os.path.join(root_folder, "poly")
out_folder = os.path.join(root_folder, "out")

folder_list = [las_folder, poly_folder, out_folder]

def check_root(): # Check if the root folder and other dirs exist
    if os.path.isdir(root_folder):
        for folder in folder_list:
            name = folder.split("\\")[-1]
            if not os.path.isdir(folder): # Create them if needed
                os.mkdir(folder)
                print(f"Created folder for {name}")
            else:
                print(f"Folder for {name} found")
    else:
        input("Root folder does not exist, PRESS ENTER TO EXIT")
        raise SystemExit(0)

def check_points(args): # Check if points are inside of the polygon. Function needed for multiprocessing
    chunk, polygon = args
    return [polygon.contains(Point(x, y)) for x, y in chunk]

def process_scans(scan_path, name):
    scan = laspy.read(scan_path)
    points = np.vstack((scan.x, scan.y)).T # Prepare data for shapely
    poly = gpd.read_file(poly_folder + "/" + name.split(".")[0] + ".shp") # Import polygons based on scan name
    poly["area"] = poly["geometry"].area

    for rows, cols in tqdm(poly.iterrows(), total = len(poly)): # For each polygon in the file
        polygon = cols["geometry"]
        xmin, ymin, xmax, ymax = cols["geometry"].bounds # Get the polygons bounding box

        polygon_mask = (
            (points[:, 0] >= xmin) & 
            (points[:, 0] <= xmax) & 
            (points[:, 1] >= ymin) & 
            (points[:, 1] <= ymax)
        ) # Mask points that are inside of polygons bbox

        filtered_points = points[polygon_mask] # Select points that area inside polygon

        num_cores = 16
        chunks = np.array_split(filtered_points, num_cores)

        with Pool(num_cores) as pool: # Select points using multiprocessing
            results = pool.map(check_points, [(chunk, polygon) for chunk in chunks])

        inside_polygon = np.concatenate(results) # Combine all results

        if inside_polygon.any(): # If the masking result is not empty
            final_indices = np.where(polygon_mask)[0][inside_polygon] # Clip and go back to initial array size

            clipped_scan = laspy.LasData(scan.header) # Create a las entity for clipped points
            clipped_scan.points = scan.points[final_indices].copy() # Insert the points into las

            ground_only = clipped_scan.classification == 2 # Take only the ground and create a new entity
            ground = laspy.LasData(scan.header)
            ground.points = clipped_scan.points[np.array(ground_only)]

            area = int(cols["area"])

            buf = BytesIO() # Save the file in memory
            ground.write(buf)
            buf.seek(0)
            clipped_scans[f"{area}"] = buf
            #ground.write(temp_folder + "/" + str(name) + str(fid) + "_" + str(area) + "_" + ".las")
        else:
            print("fail")

def load_data(scan_path): # Read LAS and create PyVista object
    las = laspy.read(scan_path) # Import laser scan
    points = np.column_stack((las.x, las.y, las.z))  # (N,3) array to match PyVista requirements

    point_cloud = pv.PolyData(points) # Create a PyVista PolyData object

    # If color info exists, add it as point data.
    if hasattr(las, "red") and hasattr(las, "green") and hasattr(las, "blue"):
        colors = np.column_stack((las.red, las.green, las.blue))
        point_cloud.point_data["RGB"] = colors
    
    return point_cloud

def sample_points_on_mesh(point_cloud, n_points): # Triangulate and sample points on the mesh
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
    
    file_path = os.path.join(temp_dir, f"{temp_name}.las")
    las_sampled.write(file_path)

    return file_path

if __name__ == "__main__":
    check_root()

    las_files = [scan for scan in os.listdir(las_folder) if scan.endswith(".las")] #List with laser scans

    for scan in tqdm(las_files, total = len(las_files)): # For each scan in dir
        clipped_scans = {} # Create a dict for clipped scans in memory

        las_path = os.path.join(las_folder, scan)
        process_scans(las_path, scan) # Clip scans

        with tempfile.TemporaryDirectory() as temp_dir:
            las_files = []
            las_files.append(las_path)

            for key, value in clipped_scans.items(): # For each clipped scan in dict
                las = load_data(value)

                poly_area = int(key)
                n_sample = poly_area * 60 # Sampled points based on area
                sampled_pts, sampled_cols = sample_points_on_mesh(las, n_sample) # Sample points

                file_path = convert(sampled_pts, sampled_cols, key, temp_dir) # Convert back to laspy format
                las_files.append(file_path)
                
            cmd = 'las2las -i ' + ' '.join(las_files) + f' -merged -o {out_folder + "/" + scan}' # Merge them together
            os.system(cmd)
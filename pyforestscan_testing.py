from pyforestscan.handlers import read_lidar
from pyforestscan.visualize import plot_pad, plot_metric
from pyforestscan.filters import filter_hag
from pyforestscan.calculate import assign_voxels, calculate_pad, calculate_pai, calculate_fhd, calculate_chm, calculate_canopy_cover


print("start")

file_path = r"D:\Lasy_Skaning\chmury\moto_350_star.las"
arrays = read_lidar(file_path, "EPSG:2180", hag = True)

print("file read")

arrays = filter_hag(arrays)
points = arrays[0]

print("points filtered")

voxel_resolution = (1, 1, 1)
voxels, extent = assign_voxels(points, voxel_resolution)

print("voxels assigned")

chm, extent = calculate_chm(points, voxel_resolution)
plot_metric("Canopy Height Model", chm, extent, metric_name = "Height (m)", cmap = "viridis", fig_size = None)

print("chm calculated")

pad = calculate_pad(voxels, voxel_resolution[-1])
plot_pad(pad, None, axis = "y", cmap = "viridis")

print("pad calculated")

pai = calculate_pai(pad, voxel_height = 1)
plot_metric("Plant Area Index", pai, extent, metric_name = "PAI", cmap = "viridis", fig_size = None, flip_y = True)

print("pai calculated")

cover = calculate_canopy_cover(pad, voxel_height = voxel_resolution[-1], min_height = 2, k = 0.5)
plot_metric("Canopy Cover", cover, extent, metric_name = "Cover (%)", cmap = "viridis", fig_size = None, flip_y = True)

print("cover calculated")

fhd = calculate_fhd(voxels)
plot_metric("Foliage Height Diversity", fhd, extent, metric_name = "FHD", cmap = "viridis", fig_size = None, flip_y = True)

print("fhd calculated")
import Metashape
import os, sys
import re


def find_files(folder, types):
    return [entry.path for entry in os.scandir(folder) if (entry.is_file() and os.path.splitext(entry.name)[1].lower() in types)]

folders = list(filter(lambda arg : arg[0] != "-", sys.argv[1:])) #lists folders taken from arguments

if len(folders) != 2: #program requires exactly two inputs into arguments
    print("Usage: <laser_scans_folder> <output_folder>")
    raise Exception("Invalid script arguments")

laser_scans_folder = folders[0] #first arg is input
output_folder = folders[1] #second arg is output

laser_scans = find_files(laser_scans_folder, [".las"]) #list all .las files

doc = Metashape.app.document #initialize doc class
doc.save(output_folder + "/calibration_project.psx")
doc.open(output_folder + "/calibration_project.psx")

chunk = doc.chunk #initialize chunk class
doc.save()

for laser_scan_path in laser_scans: #import laser scans
    chunk.importPointCloud(laser_scan_path, is_laser_scan = False, crs = Metashape.CoordinateSystem("EPSG::2177"))
    doc.save()

task = Metashape.Tasks.ClassifyPoints() #initialize classifing task class

source = Metashape.PointClass.Created #classification number 0 as source
target = [Metashape.PointClass.Building, Metashape.PointClass.Ground, Metashape.PointClass.HighVegetation, Metashape.PointClass.RoadSurface, Metashape.PointClass.Car, Metashape.PointClass.Manmade]

def clean_name(file_name): #get rid of agisoft shitty naming scheme
    pattern = r',.*?>' #regex to get rid of everything from , to >
    name_without_number_points = re.sub(pattern, "", file_name) #replace regex with empty string

    chars_to_remove = "<PointCloud '" #get rid of beginning
    cleaned_name = name_without_number_points.replace(chars_to_remove, "")

    return cleaned_name

a = 0

for cloud in chunk.point_clouds:
    task.source_class = source
    task.target_classes = target
    task.point_cloud = cloud
    task.confidence = 0.4
    task.apply(chunk)
    doc.save()
    new_name = clean_name(str(cloud))
    chunk.exportPointCloud(path = output_folder + "\export" + f"\{new_name}.las", point_cloud = a, crs = Metashape.CoordinateSystem("EPSG::2177"))
    a += 1
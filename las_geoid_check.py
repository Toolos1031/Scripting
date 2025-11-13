import os
import json
import subprocess
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# CONFIG
las_folder = r"V:\1_NW_Gora\Dane pośrednie - LIDAR"
output_csv = r"E:\geoid_test\las_height_types2.csv"
max_workers = 25  # Adjust based on your CPU

# Thread-safe file write lock
csv_lock = Lock()

# Header fields
csv_fields = ["filename", "srs_info", "mean_z", "is_evrf2007"]

# Ensure CSV is initialized once
with open(output_csv, mode='w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()

# Define the processing function
def process_las_file(file):
    print(f"Processing: {file}")
    filepath = os.path.join(las_folder, file)
    result = {"filename": file, "srs_info": "ERROR", "mean_z": "NA", "is_evrf2007": "Unknown"}
    try:
        # Get metadata
        output = subprocess.check_output(["pdal", "info", "--metadata", filepath], text=True)
        metadata = json.loads(output)
        srs_info = metadata.get("metadata", {}).get("comp_spatialreference", "")

        # Heuristic check for EVRF2007
        vertical_hint = "EVRF2007" in srs_info or "EPSG:5621" in srs_info

        # Get stats
        stats_output = subprocess.check_output(["pdal", "info", "--stats", filepath], text=True)
        stats = json.loads(stats_output)
        mean_z = stats.get("stats", {}).get("Z", {}).get("mean", "NA")

        result.update({
            "srs_info": srs_info,
            "mean_z": mean_z,
            "is_evrf2007": "Yes" if vertical_hint else "No"
        })

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] {file}: {e}")

    # Write result to CSV (thread-safe)
    with csv_lock:
        with open(output_csv, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writerow(result)

    return result

# Gather all LAS files
las_files = [f for f in os.listdir(las_folder) if f.lower().endswith(".las")]

# Run concurrent processing
with ThreadPoolExecutor(max_workers=max_workers) as executor:
    future_to_file = {executor.submit(process_las_file, file): file for file in las_files}
    for future in as_completed(future_to_file):
        file = future_to_file[future]
        try:
            result = future.result()
            print(f"[DONE] {file}: {result['is_evrf2007']} | Mean Z: {result['mean_z']}")
        except Exception as exc:
            print(f"[FAIL] {file}: {exc}")
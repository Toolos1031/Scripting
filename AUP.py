import re
from shapely.geometry import Polygon, mapping
import os
import fiona
from fiona.crs import from_epsg
from collections import defaultdict
import sys
import requests

def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    return content

def parse_blocks(content):
    blocks = content.strip().split("\n\n")
    parsed_blocks = []

    for block in blocks:
        lines = block.split("\n")
        zone_data = {
            "Airspace" : None,
            "Zone" : None,
            "Lowest_altitude" : None,
            "Highest_altitude" : None,
            "Vertices" : []
        }

        for line in lines:
            if line.startswith("AC"):
                zone_data["Airspace"] = line[3:]
            elif line.startswith("AN"):
                zone_data["Zone"] = line[3:]
            elif line.startswith("AL"):
                zone_data["Lowest_altitude"] = line[3:]
            elif line.startswith("AH"):
                zone_data["Highest_altitude"] = line[3:]
            elif line.startswith("DP"):
                coords = re.findall(r'\d+:\d+:\d+ [NE]', line)
                if coords:
                    lat, lon = coords
                    lat = convert_to_decimal(lat)
                    lon = convert_to_decimal(lon)
                    zone_data["Vertices"].append((lon, lat))
        
        if zone_data["Vertices"]:
            parsed_blocks.append(zone_data)

    return parsed_blocks

def convert_to_decimal(coord):
    d, m, s, direction = re.split(r'[ :]', coord)
    dd = float(d) + float(m)/60 + float(s)/(60*60)
    if direction in ['S', 'W']:
        dd *= -1
    return dd

def create_geopackage(zones, out):
    grouped_zones = defaultdict(list)
    for zone in zones:
        pattern = re.compile(r'^L')
        key = zone["Zone"].split(" ")[0]
        if not pattern.match(key) and key != "TSA":
            grouped_zones[key].append(zone)

    for key, zones in grouped_zones.items():
        output = os.path.join(out, key + ".gpkg")
        schema = {
            'geometry': 'Polygon',
            'properties': {
                'Airspace': 'str',
                'Zone': 'str',
                'Lowest_altitude': 'str',
                'Highest_altitude': 'str'
            }
        }

        with fiona.open(
            output,
            mode = "w",
            driver = "GPKG",
            schema = schema,
            crs = from_epsg(4326)
        ) as layer:
            for zone in zones:
                polygon = Polygon(zone["Vertices"])
                layer.write({
                    'geometry': mapping(polygon),
                    'properties': {
                        'Airspace': zone['Airspace'],
                        'Zone': zone['Zone'],
                        'Lowest_altitude': zone['Lowest_altitude'],
                        'Highest_altitude': zone['Highest_altitude']
                    }
                })

def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size = 8192):
                f.write(chunk)

def main():
    directory = os.path.dirname(os.path.realpath(sys.argv[0]))
    filepath = os.path.join(directory, "Poland_Airspaces_TODAY.txt")
    output = os.path.join(directory, "out")
    url = "http://www.lotnik.org/strefy/Poland_Airspaces_TODAY.txt"
    download_file(url, filepath)
    content = read_file(filepath)
    zones = parse_blocks(content)
    create_geopackage(zones, output)

if __name__ == "__main__":
    main()
import pandas as pd
import gpxpy
import gpxpy.gpx
from datetime import datetime
from pyproj import Transformer
import os

folder = r"Y:\______Wody_Polskie\Dane\Geodeci\Góra\Jemielno\Surowe\17_05_2024_wyniki_pomiarow\Celina"

file_path = os.path.join(folder, "2025-05-17 07-18-39_Celina.csv")
gpx_path = os.path.join(folder, "celina_track.gpx")

df = pd.read_csv(file_path, encoding = "cp1250")

gpx = gpxpy.gpx.GPX()

transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy = True)

gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

for cols, rows in df.iterrows():
    if rows["wysokość"] != -2.047:

        try:
            easting = float(rows["Wschód"])
            northing = float(rows["Północ"])
            elevation = float(rows["wysokość"])
            time_str = str(rows["czas"]).replace("-", ":")#.replace("-", ":", 1).replace("-", ":", 0)

            #convert tim
            time = datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S")

            lon, lat = transformer.transform(easting, northing)

            point = gpxpy.gpx.GPXTrackPoint(latitude = lat, longitude = lon, elevation = elevation, time = time)

            #add point to the segment
            gpx.tracks[0].segments[0].points.append(point)

        except Exception as e:
            print(e)

with open(gpx_path, "w") as f:
    f.write(gpx.to_xml())
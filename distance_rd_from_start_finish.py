import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, Point, MultiLineString
from tqdm import tqdm
from shapely.ops import linemerge, unary_union


rowy = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\trzebnica_rowy.gpkg"
pikiety = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\trzebnica_pikiety.gpkg"

rowy_gdf = gpd.read_file(rowy)
pikiety_gdf = gpd.read_file(pikiety)

results = []
results2 = []

# --- CRS check
if rowy_gdf.crs and pikiety_gdf.crs and rowy_gdf.crs != pikiety_gdf.crs:
    pikiety_gdf = pikiety_gdf.to_crs(rowy_gdf.crs)

# --- Prepare stable 'uwagi' grouping (treat NaN as its own group)
HAS_UWAGI = "uwagi" in rowy_gdf.columns
UG = "_uwagi_group"
if HAS_UWAGI:
    rowy_gdf[UG] = rowy_gdf["uwagi"].fillna("__NO_UWAGI__")
else:
    rowy_gdf[UG] = "__NO_UWAGI__"

# --- Dissolve within (oznaczenie, id_obrebu, uwagi-group) so we don't mix different uwagi
rowy_dissolved = (
    rowy_gdf
    .dissolve(by=["oznaczenie", "id_zlewni", UG])
    .reset_index()
)

def merge_connected_lines(geoms):
    lines = [g for g in geoms if g is not None and not g.is_empty]
    if not lines:
        return None
    u = unary_union(lines)  # LineString | MultiLineString | GeometryCollection
    gt = u.geom_type
    if gt == "LineString":
        return u
    if gt == "MultiLineString":
        return linemerge(u)
    if gt == "GeometryCollection":
        parts = []
        for g in u.geoms:
            if g.geom_type == "LineString":
                parts.append(g)
            elif g.geom_type == "MultiLineString":
                parts.extend(g.geoms)
        if not parts:
            return None
        return linemerge(MultiLineString(parts))
    return None

# --- Merge ACROSS id_obrebu but ONLY within (oznaczenie, uwagi-group)
merged_df = (
    rowy_dissolved
    .groupby(["oznaczenie", UG], as_index=False)
    .agg({"geometry": merge_connected_lines})
)

# Back to GeoDataFrame + explode
rowy_joined = gpd.GeoDataFrame(merged_df, geometry="geometry", crs=rowy_dissolved.crs)
try:
    rowy_joined = rowy_joined.explode(index_parts=False).reset_index(drop=True)
except TypeError:
    rowy_joined = rowy_joined.explode().reset_index(drop=True)

# Recover original 'uwagi' (None where it was missing)
if HAS_UWAGI:
    rowy_joined["uwagi"] = rowy_joined[UG].replace({"__NO_UWAGI__": None})
rowy_joined.drop(columns=[UG], inplace=True)

# Optional: bring back other attributes (per oznaczenie,uwagi) if you want them
attrs_to_keep = [c for c in ["id", "id_zlewni"] if c in rowy_dissolved.columns]
if attrs_to_keep:
    attrs_agg = (
        rowy_dissolved
        .groupby(["oznaczenie", UG], as_index=False)
        .agg({col: "first" for col in attrs_to_keep})
        .rename(columns={UG: UG})
    )
    if HAS_UWAGI:
        attrs_agg["uwagi"] = attrs_agg[UG].replace({"__NO_UWAGI__": None})
        attrs_agg = attrs_agg.drop(columns=[UG])
    rowy_joined = rowy_joined.merge(attrs_agg, on=["oznaczenie", "uwagi"], how="left")

# Assign a stable id if needed
rowy_joined["id"] = rowy_joined.index + 1

# --- Save merged lines
rowy_joined.to_file(
    r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\dissolved_trzebnica_rowy_2.gpkg",
    driver="GPKG"
)

rowy_poprawa = []

def get_endpoints(geom):
    if isinstance(geom, LineString):
        start = Point(geom.coords[0])
        finish = Point(geom.coords[-1])
        return start, finish
    
    elif isinstance(geom, MultiLineString):
        first = list(geom.geoms)[0]
        last = list(geom.geoms)[-1]


        start = Point(first.coords[0])
        finish = Point(last.coords[-1])
        return start, finish
    
    else:
        raise TypeError(f"Unsupported geometry type: {geom.geom_type}")

for rows, cols in tqdm(rowy_joined.iterrows(), total = len(rowy_joined)):
    #print(cols["oznaczenie"], "   -   ", cols["id_zlewni"])
    #try:
    #row_oznaczenie = cols["oznaczenie"]

    #candidate_points = pikiety_gdf[pikiety_gdf["oznaczenie"] == row_oznaczenie]

    #pikiety_rd = candidate_points[candidate_points["kod"] == 'RD']
    pikiety_rd = pikiety_gdf[pikiety_gdf["kod"] == 'RD']

    points_on_line = pikiety_rd[pikiety_rd.intersects(cols.geometry)]

    results.append({
        "id rowu": cols["id"],
        #"oznaczenie rowu": cols["oznaczenie"],
        "ile punktow": len(points_on_line),
    })
    
    #start_pt = Point(cols.geometry.coords[0])
    #finish_pt = Point(cols.geometry.coords[-1])

    start_pt, finish_pt = get_endpoints(cols.geometry)

    if len(points_on_line) > 2:
        distances = []

        for _, pt in points_on_line.iterrows():
            d_start = start_pt.distance(pt.geometry)
            d_end = finish_pt.distance(pt.geometry)

            distances.append({
                "point_id": pt.iloc[0],
                "d_start": d_start,
                "d_end": d_end
            })

        closest_start = min(distances, key = lambda x: x["d_start"])
        closest_end = min(distances, key = lambda x: x["d_end"])

        if closest_start["d_start"] > 30 or closest_end["d_end"] > 30:

            rowy_poprawa.append({
                "id": cols["id"],
                #"oznaczenie": cols["oznaczenie"],
                "closest_start_id": closest_start["point_id"],
                "closest_start_dist": closest_start["d_start"],
                "closest_end_id": closest_end["point_id"],
                "closest_end_dist": closest_end["d_end"],
                "geometry": cols.geometry
            })

            results2.append({
                #"oznaczenie": cols["oznaczenie"],
                "closest_start_id": closest_start["point_id"],
                "closest_start_dist": closest_start["d_start"],
                "closest_end_id": closest_end["point_id"],
                "closest_end_dist": closest_end["d_end"]
            })

    #except Exception as e:
        #print(f"Failed {e}")

results_df = pd.DataFrame(results)

rowy_poprawa_gdf = gpd.GeoDataFrame(rowy_poprawa, crs = rowy_joined.crs)
rowy_poprawa_gdf.to_file(r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\za_daleko_rd.gpkg", driver = "GPKG")

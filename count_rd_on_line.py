import geopandas as gpd
import pandas as pd
from shapely.ops import linemerge, unary_union
from shapely.geometry import MultiLineString, Polygon
from tqdm import tqdm

rowy = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\trzebnica_rowy.gpkg"
pikiety = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\trzebnica_pikiety.gpkg"

rowy_gdf = gpd.read_file(rowy)
pikiety_gdf = gpd.read_file(pikiety)

TOL = 0.1

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
attrs_to_keep = [c for c in ["id1", "id_zlewni"] if c in rowy_dissolved.columns]
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
    r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\dissolved_trzebnica_rowy.gpkg",
    driver="GPKG"
)

# --- Count RD points on each merged line (respecting uwagi)
pikiety_rd = pikiety_gdf[pikiety_gdf.get("kod", pd.Series(index=pikiety_gdf.index)) == "RD"].copy()
sidx = pikiety_rd.sindex

results = []
for idx, row in tqdm(rowy_joined.iterrows(), total=len(rowy_joined)):
    line = row.geometry
    if line is None or line.is_empty:
        n = 0
    else:
        query_geom = line.buffer(TOL)
        try:
            cand_idx = sidx.query(query_geom, predicate="intersects")
        except Exception:
            cand_idx = list(sidx.intersection(query_geom.bounds))
        cand = pikiety_rd.iloc[cand_idx]
        #n = len(pikiety_rd.iloc[cand_idx].loc[lambda df: df.intersects(line)])
        n = int((cand.geometry.distance(line) <= TOL).sum())

    # example skip: pipelines
    if HAS_UWAGI and (row.get("uwagi") == "Rurociąg grawitacyjny" or row.get("brak_pomiaru") == "Rozlewisko"):
        continue

    results.append({
        "id": row.get("id1", row["id"]),
        "oznaczenie": row["oznaczenie"],
        "uwagi": row.get("uwagi"),
        "ile_punktow": int(n),
        "geometry": line
    })

# --- Save results
results_df = pd.DataFrame(results)

rowy_count_gdf = gpd.GeoDataFrame(results_df, geometry="geometry", crs=rowy_joined.crs)
rowy_count_gdf.to_file(
    r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\rd_on_row_count.gpkg",
    driver="GPKG"
)
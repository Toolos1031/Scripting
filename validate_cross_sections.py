# validate_cross_sections.py
# ------------------------------------------------------------
# Dependencies (install in your environment):
#   pip install geopandas shapely pyproj rtree pandas numpy
#
# What it does:
# - For each RD point that intersects/is near the ditch line, it builds a local
#   perpendicular cross-section and searches for RDS, RGS, and RL points.
# - Validates heights with rules:
#     1) RGS > RDS (checked per side when both exist)
#     2) RD < RDS (checked per side when RDS exists)
#     3) RL > RD  (if RL exists)
# - Writes a GeoPackage of RD points with validation results + issues.
# ------------------------------------------------------------

from __future__ import annotations
import math
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.ops import linemerge

# =========================
# CONFIG — EDIT THESE PATHS
# =========================
POINTS_PATH = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\wys.gpkg"           # points with 'kod' and height field
POINTS_LAYER = None                              # e.g. "points"; None = default/first
LINES_PATH = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\trzebnica_rowy.gpkg"        # line(s) representing ditch axis/centerline
LINES_LAYER = None                               # e.g. "ditch"; None = default/firsts
OUTPUT_GPKG = r"D:\___WodyPolskie\_ostateczne_sprawdzanie\4_trzebnica\output_rd_validation2_trzebnica.gpkg"
OUTPUT_LAYER = "RD_validation"

# Working CRS: if your data are in geographic degrees, set a local projected CRS (meters).
# If None, the script will reuse the points CRS; if that is geographic, it will try EPSG:3857.
WORK_CRS = "EPSG:2180"  # e.g. "EPSG:2180" for Poland, or "EPSG:3857"

# Geometry / search parameters (meters, if projected)
MAX_DISTANCE_TO_LINE = 0.5        # how far an RD can be from the line and still count as intersecting
CROSS_HALF_LENGTH = 5          # half-length of the cross-section line (each side of RD)
CROSS_CORRIDOR_WIDTH = 2.0        # width of corridor to capture RDS/RGS/RL points
TANGENT_DELTA_FRACTION = 0.01     # fraction of line length used to approximate tangent (clamped)

# Attribute names
KOD_FIELD = "kod"                  # categorical code: RD, RDS, RGS, RL
# Height field autodetection tries these (case-insensitive) in order:
HEIGHT_CANDIDATES = [
    "h", "height", "z", "elev", "elevation", "wysokosc", "wys", "n"
]
ID_FIELD_PREFERENCE = ["id", "fid", "ID", "FID", "objectid", "OBJECTID"]


# =========================
# UTILITIES
# =========================
def pick_height_field(df: pd.DataFrame) -> str:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in HEIGHT_CANDIDATES:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    # fallback: pick the first numeric column that isn't geometry or kod
    for c in df.columns:
        if c == KOD_FIELD or c == df._geometry_column_name:
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            return c
    raise ValueError(
        f"Could not find a height/elevation field. "
        f"Tried: {HEIGHT_CANDIDATES}. "
        f"Available columns: {list(df.columns)}"
    )


def pick_id_field(df: pd.DataFrame) -> Optional[str]:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in ID_FIELD_PREFERENCE:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None


def ensure_projected(gdf: gpd.GeoDataFrame, fallback: Optional[str]) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        if not fallback:
            raise ValueError("Input layer has no CRS. Please define WORK_CRS.")
        return gdf.set_crs(fallback, allow_override=True)
    if gdf.crs.is_geographic:
        crs = fallback or "EPSG:3857"
        return gdf.to_crs(crs)
    return gdf


def nearest_line(point: Point, lines_gdf: gpd.GeoDataFrame, query_dist: float) -> Tuple[int, LineString, float]:
    """
    Returns (index, line, distance) of the nearest line geometry to the point.
    Uses a spatial index for speed.
    """
    sidx = lines_gdf.sindex
    bbox = point.buffer(query_dist).bounds
    candidates = list(sidx.intersection(bbox))
    if not candidates:
        # expand search if nothing found
        bbox = point.buffer(query_dist * 10).bounds
        candidates = list(sidx.intersection(bbox))
        if not candidates:
            # as a last resort, check all (slow)
            candidates = list(range(len(lines_gdf)))
    min_d, min_i = float("inf"), -1
    for i in candidates:
        geom = lines_gdf.geometry.iloc[i]
        d = point.distance(geom)
        if d < min_d:
            min_d, min_i = d, i
    return min_i, lines_gdf.geometry.iloc[min_i], min_d


def safe_linemerge(geom) -> LineString:
    try:
        m = linemerge(geom)
        # linemerge can return MultiLineString if disjoint; pick the part nearest to origin
        if m.geom_type == "MultiLineString":
            # merge parts by length? pick the longest
            parts = list(m.geoms)
            parts.sort(key=lambda ls: ls.length, reverse=True)
            return parts[0]
        return m
    except Exception:
        # If linemerge fails, try to coerce to LineString if already is
        if geom.geom_type == "LineString":
            return geom
        # fallback: if MultiLineString, pick longest
        if geom.geom_type == "MultiLineString":
            parts = list(geom.geoms)
            parts.sort(key=lambda ls: ls.length, reverse=True)
            return parts[0]
        raise


def tangent_and_normal_at_point(line: LineString, pt: Point) -> Tuple[np.ndarray, np.ndarray]:
    """
    Approximate unit tangent and normal (perpendicular) at the nearest point on 'line' to 'pt'.
    """
    length = line.length
    if length == 0:
        raise ValueError("Zero-length line encountered.")
    s = line.project(pt)
    delta = max(0.01, min(length * TANGENT_DELTA_FRACTION, length / 10.0))
    s1 = max(0.0, s - delta)
    s2 = min(length, s + delta)
    p1 = line.interpolate(s1)
    p2 = line.interpolate(s2)
    v = np.array([p2.x - p1.x, p2.y - p1.y], dtype=float)
    nrm = np.linalg.norm(v)
    if nrm == 0:
        # Degenerate case: use small offset in x
        v = np.array([1.0, 0.0])
        nrm = 1.0
    t_hat = v / nrm
    n_hat = np.array([-t_hat[1], t_hat[0]])  # rotate +90°
    return t_hat, n_hat


def build_cross_section(pt: Point, n_hat: np.ndarray, half_len: float) -> LineString:
    p = np.array([pt.x, pt.y], dtype=float)
    a = p - n_hat * half_len
    b = p + n_hat * half_len
    return LineString([tuple(a), tuple(b)])


def classify_side(rd_pt: Point, n_hat: np.ndarray, other_pt: Point) -> float:
    """
    Returns signed coordinate along the perpendicular axis:
    positive -> one side, negative -> the other side. Magnitude is distance along normal.
    """
    v = np.array([other_pt.x - rd_pt.x, other_pt.y - rd_pt.y], dtype=float)
    return float(np.dot(v, n_hat))


def choose_nearest_per_side(
    rd_pt: Point,
    n_hat: np.ndarray,
    candidates: gpd.GeoDataFrame,
    code: str
) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """
    Among candidates with KOD == code, pick up to one on each side of the RD point:
      - the one with smallest |signed_normal_distance| for each side
    Returns (left, right) where 'left' means signed < 0, 'right' means signed > 0.
    """
    subset = candidates[candidates[KOD_FIELD].str.upper() == code.upper()].copy()
    if subset.empty:
        return None, None
    subset["signed_n"] = subset.geometry.apply(lambda g: classify_side(rd_pt, n_hat, g))
    left = subset[subset["signed_n"] < 0]
    right = subset[subset["signed_n"] > 0]

    def pick_min_abs(df):
        if df.empty:
            return None
        idx = (df["signed_n"].abs()).idxmin()
        return df.loc[idx]

    return pick_min_abs(left), pick_min_abs(right)


def validate_rules(
    rd_h: float,
    rds_left_h: Optional[float],
    rds_right_h: Optional[float],
    rgs_left_h: Optional[float],
    rgs_right_h: Optional[float],
    rl_h: Optional[float],
) -> Tuple[bool, Dict[str, Optional[bool]], list[str]]:
    """
    Apply rules and collect issues.
    """
    issues = []
    rules: Dict[str, Optional[bool]] = {
        "RGS_gt_RDS_left": None,
        "RGS_gt_RDS_right": None,
        "RD_lt_RDS_left": None,
        "RD_lt_RDS_right": None,
        "RL_gt_RD": None,
        "RL_gt_RGS": None,
    }

    # RGS > RDS (per side)
    if rgs_left_h is not None and rds_left_h is not None:
        rules["RGS_gt_RDS_left"] = rgs_left_h > rds_left_h
        if not rules["RGS_gt_RDS_left"]:
            issues.append(f"Left side: RGS({rgs_left_h}) <= RDS({rds_left_h})")
    if rgs_right_h is not None and rds_right_h is not None:
        rules["RGS_gt_RDS_right"] = rgs_right_h > rds_right_h
        if not rules["RGS_gt_RDS_right"]:
            issues.append(f"Right side: RGS({rgs_right_h}) <= RDS({rds_right_h})")

    # RD < RDS (per side)
    if rds_left_h is not None:
        rules["RD_lt_RDS_left"] = rd_h < rds_left_h
        if not rules["RD_lt_RDS_left"]:
            issues.append(f"RD({rd_h}) >= RDS_left({rds_left_h})")
    if rds_right_h is not None:
        rules["RD_lt_RDS_right"] = rd_h < rds_right_h
        if not rules["RD_lt_RDS_right"]:
            issues.append(f"RD({rd_h}) >= RDS_right({rds_right_h})")

    # RL > RD (if present)
    if rl_h is not None:
        rules["RL_gt_RD"] = rl_h > rd_h
        if not rules["RL_gt_RD"]:
            issues.append(f"RL({rl_h}) <= RD({rd_h})")
    if rl_h is not None and rgs_right_h is not None and rgs_left_h is not None:
        rules["RL_gt_RGS"] = rl_h < rgs_left_h or rl_h < rgs_right_h
        if not rules["RL_gt_RGS"]:
            issues.append(f"RL({rl_h}) <= RGS({rgs_right_h})")

    # Overall OK if no issues recorded (we only flag when rule comparisons were applicable)
    ok = len(issues) == 0
    return ok, rules, issues


def main():
    # Load data
    points = gpd.read_file(POINTS_PATH, layer=POINTS_LAYER) if POINTS_LAYER else gpd.read_file(POINTS_PATH)
    lines = gpd.read_file(LINES_PATH, layer=LINES_LAYER) if LINES_LAYER else gpd.read_file(LINES_PATH)

    # Basic checks
    if KOD_FIELD not in points.columns:
        raise ValueError(f"Expected column '{KOD_FIELD}' with codes RD/RDS/RGS/RL in points.")

    # Determine height field
    height_field = pick_height_field(points)

    # Harmonize CRS
    work_crs = WORK_CRS or points.crs
    points = ensure_projected(points, work_crs)
    lines = ensure_projected(lines, points.crs.to_string())

    # Normalize codes to upper
    points[KOD_FIELD] = points[KOD_FIELD].astype(str).str.upper()

    # Separate RD and others
    rd_gdf = points[points[KOD_FIELD] == "RD"].copy()
    others = points[points[KOD_FIELD] != "RD"].copy()

    if rd_gdf.empty:
        print("No RD points found. Nothing to validate.")
        return

    # Build spatial indexes
    _ = lines.sindex
    _ = others.sindex

    rd_id_field = pick_id_field(rd_gdf)
    if rd_id_field is None:
        rd_id_field = "rd_id"

    results = []
    out_rows = []

    for idx, rd in rd_gdf.iterrows():
        rd_geom: Point = rd.geometry
        rd_h = float(rd[height_field])

        # Find nearest line
        li, raw_line, dist = nearest_line(rd_geom, lines, MAX_DISTANCE_TO_LINE)
        intersects_line = dist <= MAX_DISTANCE_TO_LINE

        if not intersects_line:
            results.append((idx, False, ["RD not intersecting/near line"]))
            issues = ["RD not intersecting/near line"]
            out_rows.append({
                rd_id_field: rd.get(rd_id_field, idx),
                "intersects_line": False,
                "found_rds_left": False,
                "found_rds_right": False,
                "found_rgs_left": False,
                "found_rgs_right": False,
                "found_rl": False,
                "rule_RGS_gt_RDS_left": None,
                "rule_RGS_gt_RDS_right": None,
                "rule_RD_lt_RDS_left": None,
                "rule_RD_lt_RDS_right": None,
                "rule_RL_gt_RD": None,
                "rule_RL_gt_RGS": None,
                "ok": False,
                "issues": "; ".join(issues),
                height_field: rd_h,
                "geometry": rd_geom
            })
            continue

        # Clean/merge line to a usable LineString
        line = safe_linemerge(raw_line)

        # Tangent & normal at RD
        t_hat, n_hat = tangent_and_normal_at_point(line, rd_geom)

        # Build cross-section corridor
        cross_line = build_cross_section(rd_geom, n_hat, CROSS_HALF_LENGTH)
        corridor = cross_line.buffer(CROSS_CORRIDOR_WIDTH / 2.0, cap_style=2)

        # Candidate points within corridor (exclude this RD itself by index)
        cand_idx = list(others.sindex.intersection(corridor.bounds))
        candidates = others.iloc[cand_idx].copy()
        candidates = candidates[candidates.intersects(corridor)]

        # Pick nearest per side for RDS and RGS; RL optional (nearest overall within corridor)
        rds_left, rds_right = choose_nearest_per_side(rd_geom, n_hat, candidates, "RDS")
        rgs_left, rgs_right = choose_nearest_per_side(rd_geom, n_hat, candidates, "RGS")

        rl_row = None
        rl_subset = candidates[candidates[KOD_FIELD] == "RL"].copy()
        if not rl_subset.empty:
            # choose RL with min |signed_n|
            rl_subset["signed_n"] = rl_subset.geometry.apply(lambda g: classify_side(rd_geom, n_hat, g))
            rl_row = rl_subset.loc[(rl_subset["signed_n"].abs()).idxmin()]

        # Heights for validation
        rds_left_h = float(rds_left[height_field]) if rds_left is not None else None
        rds_right_h = float(rds_right[height_field]) if rds_right is not None else None
        rgs_left_h = float(rgs_left[height_field]) if rgs_left is not None else None
        rgs_right_h = float(rgs_right[height_field]) if rgs_right is not None else None
        rl_h = float(rl_row[height_field]) if rl_row is not None else None

        ok, rule_dict, issues = validate_rules(
            rd_h, rds_left_h, rds_right_h, rgs_left_h, rgs_right_h, rl_h
        )

        out_rows.append({
            rd_id_field: rd.get(rd_id_field, idx),
            "intersects_line": True,
            "found_rds_left": rds_left is not None,
            "found_rds_right": rds_right is not None,
            "found_rgs_left": rgs_left is not None,
            "found_rgs_right": rgs_right is not None,
            "found_rl": rl_row is not None,
            "rule_RGS_gt_RDS_left": rule_dict["RGS_gt_RDS_left"],
            "rule_RGS_gt_RDS_right": rule_dict["RGS_gt_RDS_right"],
            "rule_RD_lt_RDS_left": rule_dict["RD_lt_RDS_left"],
            "rule_RD_lt_RDS_right": rule_dict["RD_lt_RDS_right"],
            "rule_RL_gt_RD": rule_dict["RL_gt_RD"],
            "rule_RL_gt_RGS": rule_dict["RL_gt_RGS"],
            "ok": ok,
            "issues": "; ".join(issues) if issues else "",
            height_field: rd_h,
            "geometry": rd_geom
        })
        results.append((idx, True, issues))

    # Build output GeoDataFrame for RD only
    out_gdf = gpd.GeoDataFrame(out_rows, geometry="geometry", crs=points.crs)

    # Save GeoPackage
    out_path = Path(OUTPUT_GPKG)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Remove existing layer if overwriting (GeoPandas will overwrite the whole file by default for GPKG)
    out_gdf.to_file(OUTPUT_GPKG, layer=OUTPUT_LAYER, driver="GPKG")

    # Also print a concise log to the terminal
    total = len(out_gdf)
    bad = int((~out_gdf["ok"]).sum())
    print(f"\nValidation complete. RD points: {total}, with issues: {bad}")
    if bad:
        print("\nExamples of issues:")
        sample = out_gdf[~out_gdf["ok"]].head(10)
        for _, r in sample.iterrows():
            print(f" - RD {r[rd_id_field]}: {r['issues']}")

    # Optional: write CSV summary next to GPKG
    csv_path = out_path.with_suffix(".csv")
    out_gdf.drop(columns="geometry").to_csv(csv_path, index=False)
    print(f"\nSaved:\n - {OUTPUT_GPKG} (layer: {OUTPUT_LAYER})\n - {csv_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)
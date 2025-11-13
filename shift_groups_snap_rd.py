# shift_groups_snap_rd.py
# Stand-alone script: shift clusters of points so that RD snaps to nearest line.
# All points in the same cluster (around RD) are translated by the same vector.

import argparse
import sys
from typing import Dict, Iterable, Optional, Tuple

import geopandas as gpd
from shapely.geometry import Point, LineString, MultiLineString
from shapely.ops import nearest_points
from shapely.affinity import translate


def read_layer(path: str, layer: Optional[str]) -> gpd.GeoDataFrame:
    if layer:
        return gpd.read_file(path, layer=layer)
    return gpd.read_file(path)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Shift point groups so RD intersects the nearest line."
    )
    p.add_argument("--points", required=True, help="Path to point layer file")
    p.add_argument("--points-layer", help="Layer name (for GeoPackage, etc.)")
    p.add_argument("--lines", required=True, help="Path to line layer file")
    p.add_argument("--lines-layer", help="Layer name (for GeoPackage, etc.)")
    p.add_argument("--kod-field", default="kod", help="Field with codes (default: kod)")
    p.add_argument("--rd-value", default="RD", help="Value that marks RD (default: RD)")
    p.add_argument(
        "--allowed-codes",
        default="RD,RDS,RGS,RL",
        help="CSV of codes considered part of a group (default: RD,RDS,RGS,RL)",
    )
    p.add_argument(
        "--radius",
        type=float,
        default=10.0,
        help="Grouping radius around RD in layer units (default: 10)",
    )
    p.add_argument(
        "--max-move",
        type=float,
        default=50.0,
        help="Maximum allowed RD→line move distance (0 disables, default: 50)",
    )
    p.add_argument("--out", required=True, help="Output file (e.g., .gpkg, .shp)")
    p.add_argument("--out-layer", help="Output layer name (GeoPackage etc.)")
    return p


def is_geographic(crs) -> bool:
    try:
        return crs and crs.is_geographic
    except Exception:
        return False


def nearest_line_idx(
    pt: Point, lines: gpd.GeoSeries, lines_sindex
) -> Tuple[int, LineString, float, Point]:
    """
    Returns (line_idx, line_geom, distance, snap_point_on_line) for a point.
    Uses spatial index to get a close candidate, then exact nearest point.
    """
    # Quick candidate(s) via sindex.nearest if available; else fallback to bbox query
    candidate_idxs: Iterable[int] = []
    try:
        res = list(lines_sindex.nearest(pt.bounds, return_all=True))
        candidate_idxs = res[0] if res else []
    except Exception:
        # Fallback: query a small bbox; if empty, expand progressively
        expand = 1.0
        for _ in range(4):
            minx, miny, maxx, maxy = pt.bounds
            bbox = (minx - expand, miny - expand, maxx + expand, maxy + expand)
            candidate_idxs = list(lines_sindex.intersection(bbox))
            if candidate_idxs:
                break
            expand *= 5.0
        if not candidate_idxs:
            candidate_idxs = range(len(lines))

    best_idx = None
    best_dist = float("inf")
    best_snap = None
    for idx in candidate_idxs:
        geom = lines.iloc[idx]
        if geom is None or geom.is_empty:
            continue
        # Ensure a (Multi)LineString
        if not isinstance(geom, (LineString, MultiLineString)):
            continue
        # exact closest point
        p_on_pt, p_on_line = nearest_points(pt, geom)
        d = p_on_pt.distance(p_on_line)
        if d < best_dist:
            best_dist = d
            best_idx = idx
            best_snap = p_on_line

    if best_idx is None or best_snap is None:
        raise RuntimeError("Could not find nearest line.")

    return best_idx, lines.iloc[best_idx], best_dist, best_snap


def main():
    args = build_arg_parser().parse_args()

    pts = read_layer(args.points, args.points_layer)
    lns = read_layer(args.lines, args.lines_layer)

    if pts.empty:
        sys.exit("Point layer is empty.")
    if lns.empty:
        sys.exit("Line layer is empty.")

    # CRS sanity
    if is_geographic(lns.crs):
        print(
            "WARNING: Line layer CRS is geographic (degrees). "
            "Distances will be in degrees; consider reprojecting to a metric CRS."
        )

    # Work in the line layer CRS; keep original point CRS for saving back
    pts_orig_crs = pts.crs
    if pts.crs is None or lns.crs is None:
        sys.exit("Both layers must have a valid CRS.")
    pts_work = pts.to_crs(lns.crs)
    allowed = {s.strip() for s in args.allowed_codes.split(",") if s.strip()}

    if args.kod_field not in pts_work.columns:
        sys.exit(f"Field '{args.kod_field}' not found in point layer.")

    # Spatial indexes
    lines_series = lns.geometry
    lines_sindex = lines_series.sindex
    pts_sindex = pts_work.sindex

    # Cache: nearest line id per point index
    nearest_line_cache: Dict[int, Tuple[int, float, Point]] = {}

    def nearest_line_for_point_idx(ix: int) -> Tuple[int, float, Point]:
        if ix in nearest_line_cache:
            return nearest_line_cache[ix]
        pt = pts_work.geometry.iloc[ix]
        lid, _, dist, snap_pt = nearest_line_idx(pt, lines_series, lines_sindex)
        nearest_line_cache[ix] = (lid, dist, snap_pt)
        return nearest_line_cache[ix]

    # Identify RD points
    rd_mask = pts_work[args.kod_field].astype(str) == args.rd_value
    rd_indices = list(pts_work.index[rd_mask])

    processed = set()
    moved_geoms: Dict[int, Point] = {}

    print(f"Found {len(rd_indices)} RD points to anchor.")

    for rd_ix in rd_indices:
        if rd_ix in processed:
            continue

        rd_pt: Point = pts_work.geometry.loc[rd_ix]
        rd_line_id, rd_dist, rd_snap = nearest_line_for_point_idx(rd_ix)

        if args.max_move > 0 and rd_dist > args.max_move:
            print(
                f"Skip RD idx {rd_ix}: nearest line {rd_dist:.3f} > max_move {args.max_move}"
            )
            continue

        # translation vector (in line CRS)
        dx = rd_snap.x - rd_pt.x
        dy = rd_snap.y - rd_pt.y

        # Candidates within a bbox radius
        minx, miny, maxx, maxy = rd_pt.bounds
        bbox = (minx - args.radius, miny - args.radius, maxx + args.radius, maxy + args.radius)
        cand = list(pts_sindex.intersection(bbox))

        # Build group: allowed codes, same nearest line as RD, actually within radius
        group = []
        for ix in cand:
            if ix in processed:
                continue
            code = str(pts_work.at[ix, args.kod_field])
            if code not in allowed:
                continue
            pt = pts_work.geometry.iloc[ix]
            if pt.distance(rd_pt) > args.radius:
                continue
            lid, _, _ = nearest_line_for_point_idx(ix)
            if lid == rd_line_id:
                group.append(ix)

        if not group:
            group = [rd_ix]  # ensure we at least move RD

        # Apply translation to every member
        for ix in group:
            pt = pts_work.geometry.loc[ix]
            moved_geoms[ix] = translate(pt, xoff=dx, yoff=dy)
            processed.add(ix)

        print(f"Moved group anchored at RD idx {rd_ix}: {len(group)} point(s).")

    # Construct output GeoDataFrame in the original point CRS
    out = pts_work.copy()
    # Fill geometries: moved ones replaced, others unchanged
    for ix, new_geom in moved_geoms.items():
        out.at[ix, "geometry"] = new_geom

    # Convert back to the original CRS (if needed)
    if pts_orig_crs != lns.crs:
        out = out.to_crs(pts_orig_crs)

    # Save
    if args.out_layer:
        out.to_file(args.out, layer=args.out_layer, driver="GPKG")
    else:
        out.to_file(args.out)

    moved_count = len(moved_geoms)
    print(f"Done. Moved {moved_count} features. Wrote: {args.out}" + (f"::{args.out_layer}" if args.out_layer else ""))


if __name__ == "__main__":
    main()

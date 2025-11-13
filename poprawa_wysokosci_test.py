import numpy as np
import geopandas as gpd
import pandas as pd

# --- wejście ---
gdf = gpd.read_file(r'D:\test\pikiety_lokalnie.shp')

# upewnij się, że 'z' jest liczbą
gdf['z'] = pd.to_numeric(gdf['z'], errors='coerce')

rd_points  = gdf[gdf['kod'] == 'RD'].copy()
rds_points = gdf[gdf['kod'] == 'RDS'].copy()
rgs_points = gdf[gdf['kod'] == 'RGS'].copy()


def _nearest_indices(base_geom, candidates_gdf, max_distance, k=2):
    """Zwraca indeksy do k najbliższych kandydatów w odległości <= max_distance."""
    if candidates_gdf.empty:
        return []
    idx_bbox = list(candidates_gdf.sindex.intersection(base_geom.buffer(max_distance).bounds))
    if not idx_bbox:
        return []
    cand = candidates_gdf.iloc[idx_bbox]   # używamy iloc!
    d = cand.geometry.distance(base_geom)
    d = d[d <= max_distance]
    if d.empty:
        return []
    return list(d.nsmallest(k).index)


def popraw_wysokosci_rd_rds_rgs(
    rd_points, rds_points, rgs_points, max_distance=7, eps=0.0, delta=0.11, k=2
):
    """
    Wymusza RD < RDS < RGS przez obniżanie RD i/lub RDS.
    RGS nie jest modyfikowany. Ignoruje przekroje zanikające (brak RDS, 2xRGS).
    """
    # zgodność CRS
    rds_points = rds_points.to_crs(rd_points.crs)
    rgs_points = rgs_points.to_crs(rd_points.crs)

    out_rd  = rd_points.copy()
    out_rds = rds_points.copy()
    out_rgs = rgs_points.copy()

    # flagi diagnostyczne
    out_rd['auto_fixed']  = False
    out_rd['fix_reason']  = ''
    out_rds['auto_fixed'] = False
    out_rds['fix_reason'] = ''

    # iterujemy po RD
    for idx, rd in out_rd.iterrows():
        geom = rd.geometry
        z_RD = float(rd['z'])

        try:
            rds_idxs = _nearest_indices(geom, out_rds, max_distance, k=k)
            rgs_idxs = _nearest_indices(geom, out_rgs, max_distance, k=k)

            # row zanikający: brak RDS i dokładnie 2 RGS -> pomijamy
            if len(rds_idxs) == 0 and len(rgs_idxs) == 2:
                continue

            # aktualne wartości
            rds_z = out_rds.loc[rds_idxs, 'z'].astype(float) if rds_idxs else pd.Series(dtype=float)
            rgs_z = out_rgs.loc[rgs_idxs, 'z'].astype(float) if rgs_idxs else pd.Series(dtype=float)

            # 1) RDS < RGS
            if (len(rds_z) > 0) and (len(rgs_z) > 0):
                rds_max = float(rds_z.max())
                rgs_min = float(rgs_z.min())
                if rds_max >= rgs_min - eps:
                    new_rds_val = rgs_min - delta
                    high_rds_mask = out_rds.loc[rds_idxs, 'z'] >= (rgs_min - eps)
                    high_rds_indices = list(out_rds.loc[rds_idxs].index[high_rds_mask])
                    if high_rds_indices:
                        out_rds.loc[high_rds_indices, 'z'] = new_rds_val
                        out_rds.loc[high_rds_indices, 'auto_fixed'] = True
                        out_rds.loc[high_rds_indices, 'fix_reason'] = 'RDS<RGS enforced'
                        print(f"Poprawiono RDS {high_rds_indices}: ustawiono {new_rds_val:.2f}")

                    # odśwież rds_z po korekcie
                    rds_z = out_rds.loc[rds_idxs, 'z'].astype(float)

            # 2) RD < RDS
            if len(rds_z) > 0:
                rds_min = float(rds_z.min())
                if z_RD >= rds_min - eps:
                    new_rd = rds_min - delta
                    out_rd.at[idx, 'old_z'] = z_RD
                    out_rd.at[idx, 'z'] = new_rd
                    out_rd.at[idx, 'auto_fixed'] = True
                    out_rd.at[idx, 'fix_reason'] = 'RD<RDS enforced'
                    print(f"Poprawiono RD {idx}: ustawiono {new_rd:.2f}")
        except:
            pass
    return out_rd, out_rds, out_rgs


# --- uruchomienie korekty ---
rd_corr, rds_corr, rgs_corr = popraw_wysokosci_rd_rds_rgs(
    rd_points, rds_points, rgs_points,
    max_distance=7, eps=0.0, delta=0.11, k=2
)

# sklej z resztą warstw i zapisz
pozostale = gdf[~gdf['kod'].isin(['RD', 'RDS', 'RGS'])].copy()
wynik = pd.concat([rd_corr, rds_corr, rgs_corr, pozostale], ignore_index=True)

wynik.to_file(r"D:\test\poprawione_RD_RDS_RGS.gpkg", layer="wysokosc_auto", driver="GPKG")

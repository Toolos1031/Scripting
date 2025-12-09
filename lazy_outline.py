"""
Obliczanie footprintu (outline) chmur punktów .laz + zapis do GeoJSON + TXT.

Wymagane biblioteki:
    pip install laspy numpy rasterio shapely geopandas tqdm
"""

from pathlib import Path
import numpy as np
import laspy
import rasterio
from rasterio.transform import from_origin
from rasterio.features import shapes
from shapely.geometry import shape
from shapely.ops import unary_union
import geopandas as gpd
from tqdm import tqdm

# ===================== KONFIGURACJA =====================

# Katalog z plikami .laz
INPUT_DIR = r"V:\6_NW_Leszno\Chmura punktow"

# Wzorzec plików
LAZ_PATTERN = "*.laz"

# Rozmiar piksela w metrach
CELL_SIZE = 1.0

# Układ współrzędnych
CRS_EPSG = "EPSG:2180"

# Ścieżka zapisu GeoJSON
OUTPUT_GEOJSON = r"D:\___WodyPolskie\POWIERZCHNIA_CHMUR\LESZNO\LESZNO_coverage.gpkg"

# Ścieżka zapisu raportu TXT
OUTPUT_TXT = r"D:\___WodyPolskie\POWIERZCHNIA_CHMUR\LESZNO\LESZNO.txt"

# Lista plików, których nie udało się przetworzyć
FAILED_FILES = set()


# ===================== LOGIKA =====================


def find_laz_files(input_dir: str, pattern: str = "*.laz"):
    p = Path(input_dir)
    files = list(p.rglob(pattern))
    return [str(f) for f in files]


def compute_global_bbox(laz_files, cell_size: float):
    global FAILED_FILES

    xmin, ymin = float("inf"), float("inf")
    xmax, ymax = float("-inf"), float("-inf")

    print("\n[1/3] Wyznaczanie globalnego bounding boxa...")
    for f in tqdm(laz_files):
        try:
            las = laspy.read(f)
        except Exception as e:
            print(f"[BŁĄD] Nie udało się odczytać pliku (bbox): {f}")
            print(f"       Szczegóły: {e}")
            FAILED_FILES.add(f)
            continue

        xs = np.asarray(las.x)
        ys = np.asarray(las.y)

        if xs.size == 0:
            print(f"[UWAGA] Plik bez punktów (bbox): {f}")
            FAILED_FILES.add(f)
            continue

        xmin = min(xmin, xs.min())
        ymin = min(ymin, ys.min())
        xmax = max(xmax, xs.max())
        ymax = max(ymax, ys.max())

    if not np.isfinite([xmin, ymin, xmax, ymax]).all():
        raise ValueError("Brak poprawnego bounding boxa — być może wszystkie pliki miały błędy lub brak punktów.")

    width = int(np.ceil((xmax - xmin) / cell_size))
    height = int(np.ceil((ymax - ymin) / cell_size))

    if width <= 0 or height <= 0:
        raise ValueError("Niepoprawne wymiary rastra (width/height <= 0).")

    return xmin, ymin, xmax, ymax, width, height


def build_coverage_mask(laz_files, xmin, ymin, xmax, ymax, width, height, cell_size: float):
    global FAILED_FILES

    print("\n[2/3] Budowanie maski pokrycia...")
    mask = np.zeros((height, width), dtype=np.uint8)

    for f in tqdm(laz_files):
        # Jeśli plik już wcześniej się wywalił przy bbox, pomijamy
        if f in FAILED_FILES:
            continue

        try:
            las = laspy.read(f)
        except Exception as e:
            print(f"[BŁĄD] Nie udało się odczytać pliku (mask): {f}")
            print(f"       Szczegóły: {e}")
            FAILED_FILES.add(f)
            continue

        xs = np.asarray(las.x)
        ys = np.asarray(las.y)

        if xs.size == 0:
            print(f"[UWAGA] Plik bez punktów (mask): {f}")
            FAILED_FILES.add(f)
            continue

        cols = ((xs - xmin) / cell_size).astype(int)
        rows = ((ymax - ys) / cell_size).astype(int)

        valid = (
            (cols >= 0) & (cols < width) &
            (rows >= 0) & (rows < height)
        )
        cols = cols[valid]
        rows = rows[valid]

        mask[rows, cols] = 1

    return mask


def mask_to_footprint_geometry(mask, xmin, ymax, cell_size: float):
    print("\n[3/3] Konwersja maski na poligony...")
    transform = from_origin(xmin, ymax, cell_size, cell_size)

    geometries = []
    for geom, value in shapes(mask, transform=transform):
        if value == 1:
            geometries.append(shape(geom))

    if not geometries:
        return None

    return unary_union(geometries)


def main():
    global FAILED_FILES

    laz_files = find_laz_files(INPUT_DIR, LAZ_PATTERN)

    if not laz_files:
        print(f"Nie znaleziono żadnych plików .laz w: {INPUT_DIR}")
        return

    print(f"Znaleziono {len(laz_files)} plików .laz.")

    xmin, ymin, xmax, ymax, width, height = compute_global_bbox(laz_files, CELL_SIZE)

    print(f"\nBounding box (CRS {CRS_EPSG}):")
    print(f"  xmin: {xmin}")
    print(f"  ymin: {ymin}")
    print(f"  xmax: {xmax}")
    print(f"  ymax: {ymax}")
    print(f"Rozmiar rastra: width={width}, height={height}, cell={CELL_SIZE} m")

    mask = build_coverage_mask(laz_files, xmin, ymin, xmax, ymax, width, height, CELL_SIZE)

    footprint_geom = mask_to_footprint_geometry(mask, xmin, ymax, CELL_SIZE)

    if footprint_geom is None:
        print("Brak geometrii — maska nie zawiera punktów.")
        return

    area_m2 = footprint_geom.area
    area_ha = area_m2 / 10_000.0

    print("\n=== WYNIKI ===")
    print(f"Powierzchnia pokrycia: {area_m2:,.2f} m²   ({area_ha:,.2f} ha)")
    print(f"Liczba plików z błędami: {len(FAILED_FILES)}")

    # === Zapis GeoJSON ===
    print(f"\nZapisuję footprint do GeoJSON:")
    print(OUTPUT_GEOJSON)

    gdf = gpd.GeoDataFrame(
        {"id": [1], "area_m2": [area_m2], "area_ha": [area_ha]},
        geometry=[footprint_geom],
        crs=CRS_EPSG
    )
    gdf.to_file(OUTPUT_GEOJSON, driver="GPKG")

    # === Zapis TXT ===
    print(f"Zapisuję dane do pliku TXT:\n{OUTPUT_TXT}")

    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("=== FOOTPRINT CHMUR PUNKTÓW ===\n")
        f.write(f"Źródłowy katalog: {INPUT_DIR}\n")
        f.write(f"Liczba plików .laz (wszystkich): {len(laz_files)}\n")
        f.write(f"Liczba plików przetworzonych poprawnie: {len(laz_files) - len(FAILED_FILES)}\n")
        f.write(f"Liczba plików z błędem: {len(FAILED_FILES)}\n")
        f.write(f"Rozdzielczość maski: {CELL_SIZE} m\n\n")
        f.write(f"Powierzchnia pokrycia: {area_m2:.2f} m²\n")
        f.write(f"Powierzchnia pokrycia: {area_ha:.4f} ha\n\n")

        if FAILED_FILES:
            f.write("Pliki, których nie udało się przetworzyć:\n")
            for bad in sorted(FAILED_FILES):
                f.write(f" - {bad}\n")

    print("\nGotowe! Otwórz GeoJSON w QGIS, aby sprawdzić footprint.")
    if FAILED_FILES:
        print("Uwaga: niektóre pliki nie zostały przetworzone. Lista w raporcie TXT.")


if __name__ == "__main__":
    main()

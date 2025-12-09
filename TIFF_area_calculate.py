import os
import rasterio
import numpy as np
from multiprocessing import Pool, freeze_support
from tqdm import tqdm

# ---- FUNKCJE NA POZIOMIE MODUŁU (muszą być picklowalne) ----
def process_tif(file_path):
    try:
        with rasterio.open(file_path) as src:
            if src.count < 4:
                raise ValueError("Plik nie posiada band 4")

            band1 = src.read(1)
            band4 = src.read(4)

            transform = src.transform
            pixel_area = transform[0] * -transform[4]

            valid_mask = (band1 != src.nodata) & (band4 != 0)
            valid_pixels = np.count_nonzero(valid_mask)
            area = valid_pixels * pixel_area

        return (file_path, area, None)

    except Exception as e:
        return (file_path, 0, str(e))


def gather_tif_files(folder_path):
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith((".tif", ".tiff"))
    ]


def main():
    # --- PODAJ ŚCIEŻKĘ DO FOLDERU ---
    folder_path = r"V:\7_NW_Krotoszyn\Ortofotomapa"  # <- zmień na swoją ścieżkę

    tif_files = gather_tif_files(folder_path)
    if not tif_files:
        print("Brak plików .tif w podanej ścieżce.")
        return

    failed_files = []
    total_area = 0.0

    # maksymalnie 3 procesy
    with Pool(processes=12) as pool:
        for file_path, area, error in tqdm(
            pool.imap_unordered(process_tif, tif_files),
            total=len(tif_files),
            desc="Przetwarzanie"
        ):
            if error:
                failed_files.append((file_path, error))
            else:
                total_area += area

    # PODSUMOWANIE
    print("\nŁączna powierzchnia Rawicz:", total_area, "m²")
    print("Łączna powierzchnia w hektarach:", total_area / 10_000, "ha")

    if failed_files:
        print("\n❗ NIE UDAŁO SIĘ PRZETWORZYĆ PLIKÓW:")
        for f, err in failed_files:
            print(f"- {f}  (błąd: {err})")
    else:
        print("\n✔ Wszystkie pliki przetworzone bez błędów.")


if __name__ == "__main__":
    # dla aplikacji mrożonych (exe) - bez szkody uruchomić też w normalnym środowisku
    freeze_support()
    main()
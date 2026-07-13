import subprocess
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

in_dir = Path(r"D:\E65-geoster\orto_gotowe")
levels = ["2", "4", "8", "16", "32", "64"]


def build_overviews(tif_file: str): 
    cmd = [
        "gdaladdo",
        "-r", "average",
        "--config", "COMPRESS_OVERVIEW", "LZW",
        "--config", "GDAL_NUM_THREADS", "ALL_CPUS",
        "--config", "PREDICTOR_OVERVIEW", "2",
        "--config", "ZLEVEL", "6",
        str(tif_file), *levels
    ]

    try:
        p = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return (str(tif_file), True, "OK (built overviews)")
    except subprocess.CalledProcessError as e:
        msg = (e.stderr or e.stdout or "").strip()
        if not msg:
            msg = f"gdaladdo failed with exit code {e.returncode}"
        return (str(tif_file), False, msg)
    except FileNotFoundError:
        return (str(tif_file), False, "gdaladdo not found; is GDAL installed and on PATH?")
    

def main():
    tifs = sorted(in_dir.rglob("*.tif"))
    if not tifs:
        print(f"No .tif files found in {in_dir}")
        return
    
    print(f"Found {len(tifs)} .tif files in {in_dir}")

    ok = 0
    fail = 0

    with ProcessPoolExecutor(max_workers = 20) as executor:
        futures = {executor.submit(build_overviews, str(tif)): tif for tif in tifs}

        try:
            for fut in tqdm(
                as_completed(futures),
                total = len(futures),
                desc = "Building Overviews",
                unit = "file"
                ):
                    path, success, msg = fut.result()
                    if success:
                        ok += 1
                    else:
                        fail += 1
                        tqdm.write(f"Error processing {path}: {msg}")

        except KeyboardInterrupt:
            print("Aborting...")
            for f in futures:
                f.cancel()
            return
        
    print(f"\nDone. OK={ok}, ERR={fail}")

if __name__ == "__main__":
    main()


import os
import re
from pathlib import Path
from tqdm import tqdm
import threading

serwer_path = Path("D:/Atlasus/Naloty/Dane/Dzien_5_6/skaning/CHC_20240627182814/Results/@@2024-06-26-071229/AUTOSOLVE/GPS") #serwer
dysk_path = Path("D:/Atlasus/GPS") #dysk

#tworzenie slownikow
hash_serwer = {}
hash_dysk = {}

file_list_serwer = [f for f in serwer_path.glob("**/*") if f.is_file()]
file_list_dysk = [f for f in dysk_path.glob("**/*") if f.is_file()]

def new_MD5(file_path):
    cmd = f"certutil -hashfile {file_path} MD5"
    return_value = os.popen(cmd).read()
    return return_value.splitlines()[1]

def hasher(list, dictionary, path):
    for file in tqdm(list, total = len(list)):
        hash_file = str(new_MD5(file))
        pattern=re.escape(str(path))
        short_path=re.sub(pattern, '', str(file))
        dictionary[short_path]=hash_file

def tester(serwer_hash, dysk_hash):
    # Keys present in dict1 but not in dict2
    only_in_dict = {k: serwer_hash[k] for k in serwer_hash if k not in dysk_hash}
    if only_in_dict:
        print("Pliki na dysku, ktorych nie ma na serwerze", only_in_dict.keys())

    # Keys present in both but with different values
    diff_values = {k: (dysk_hash[k], serwer_hash[k]) for k in dysk_hash if k in serwer_hash and dysk_hash[k] != serwer_hash[k]}
    if diff_values:
        print("Pliki, w ktorych rozni sie hash", diff_values)

    if len(only_in_dict)==0 and len(diff_values)==0:
        print("Wszystko OK")

def main():
    serwer = threading.Thread(target = hasher, args = (file_list_serwer, hash_serwer, serwer_path))
    dysk = threading.Thread(target = hasher, args = (file_list_dysk, hash_dysk, dysk_path))

    serwer.start()
    dysk.start()

    serwer.join()
    dysk.join()

    tester(hash_serwer, hash_dysk)

if __name__ == "__main__":
    main()
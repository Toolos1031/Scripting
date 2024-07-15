import os
import hashlib
import re
from pathlib import Path
import glob
from tqdm import tqdm



serwer_path = Path("E:\___Atlasus\skaning_przetworzony\@@2024-06-20-111416\AUTOSOLVE\GPS\BASE") #serwer
dysk_path = Path("E:/___Atlasus/test_hash/AUTOSOLVE/GPS/Base") #dysk

#tworzenie slownikow
hash_dysk = {}
hash_serwer = {}

print(dysk_path)
file_list_serwer = [f for f in serwer_path.glob("**/*") if f.is_file()]
file_list_dysk = [f for f in dysk_path.glob("**/*") if f.is_file()]

"""
#funkcja obliczajaca md5
def calculate_md5(file_path):
    # Create a new md5 hash object
    md5_hash = hashlib.md5()
     # Open the file in binary mode and read it in chunks
    with open(file_path, "rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            md5_hash.update(byte_block)
    # Return the hexadecimal digest of the hash
    return md5_hash.hexdigest()
"""

def new_MD5(file_path):
    cmd = f"certutil -hashfile {file_path} MD5"
    return_value = os.popen(cmd).read()

    return return_value.splitlines()[1]

for file in tqdm(file_list_serwer, total = len(file_list_serwer)):
    #hash_file = str(calculate_md5(file))
    hash_file = str(new_MD5(file))
    pattern=re.escape(str(serwer_path))
    short_path=re.sub(pattern, '', str(file))
    #dodajemy do listy
    hash_serwer[short_path]=hash_file

for file in tqdm(file_list_dysk, total = len(file_list_dysk)):
    #hash_file = str(calculate_md5(file))
    hash_file = str(new_MD5(file))
    pattern=re.escape(str(dysk_path))
    short_path=re.sub(pattern, '', str(file))
    #dodajemy do listy
    hash_dysk[short_path]=hash_file


#porownywanie obu slownikow
# Keys present in dict1 but not in dict2
only_in_dict1 = {k: hash_serwer[k] for k in hash_serwer if k not in hash_dysk}
if only_in_dict1:
    print("Pliki na dysku, ktorych nie ma na serwerze", only_in_dict1.keys())

# Keys present in both but with different values
diff_values = {k: (hash_dysk[k], hash_serwer[k]) for k in hash_dysk if k in hash_serwer and hash_dysk[k] != hash_serwer[k]}
if diff_values:
    print("Pliki, ktore roznia sie hash", diff_values)


if len(only_in_dict1)==0 and len(diff_values)==0:
    print("Wszystko OK")
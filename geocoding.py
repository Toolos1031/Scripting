import json
import pandas as pd
import requests
import time
import string
import numpy as np

def geocode_gugik(row):

    powiat = str(row["Powiat"]).strip()
    print(powiat)
    if powiat and powiat[0].isupper():
        print("Powiat starts with uppercase letter, using 'Powiat' as city.")
        city = str(row["Powiat"]).strip()
    else:
        city = str(row["Miejscowość"]).strip()
    street = str(row["Ulica"]).strip()
    number = str(row["Numer budynku"]).strip()

    if "ul." in street.lower():
        street = street.replace("ul.", "").strip()

    # Format required by GUGiK API: "Miasto, Ulica Numer"
    if pd.isna(row["Ulica"]) or street.lower() == 'nan' or not street:
        address = f"{city} {number}"

    else:
        address = f"{city}, {street} {number}"

    print(address)

    url = "https://services.gugik.gov.pl/uug/"
    params = {
        "request": "GetAddress",
        "address": address,
        "srid": "4326",
    }

    try:

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        response = requests.get(url, params = params, headers = headers, timeout = 10)
        if response.status_code == 200:
            data = response.json()

            results = data.get("results", {})
            if results:
                first_key = list(results.keys())[0]
                match = results[first_key]

                lat = float(match.get("y")) if match.get("y") else None
                lon = float(match.get("x")) if match.get("x") else None

                return pd.Series([lat, lon])

    except requests.RequestException as e:
        print(f"Request error for address '{address}': {e}")
    # BĘDZIEMY MILI DLA RZĄDOWEGO API XDDDDD
    time.sleep(0.1)

    # Return None if the adress wasn't found or an error occurred
    return pd.Series([None, None])

df = pd.read_csv(r"D:\geokodowanie_szkoly\rspo_2026_04_24.csv", encoding = "utf-8", sep = ";")

df.replace(r'^\s*$', np.nan, regex=True, inplace=True)

df.dropna(subset = ["Miejscowość", "Numer budynku"], how = "all", inplace = True)

print("Geocoding via GUGiK API in progress...")
df[["Latitude", "Longitude"]] = df.apply(geocode_gugik, axis=1)

df.to_csv(r"D:\geokodowanie_szkoly\rspo_2026_04_24_geocoded.csv", index=False, encoding="utf-8-sig", sep=";")
print("Geocoding completed. Results saved to 'rspo_2026_04_24_geocoded.csv'.")
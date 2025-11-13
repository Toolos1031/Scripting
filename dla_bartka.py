import pandas as pd
import re

path = r"Z:\_______Przenoszenie\Nowy folder (2)\dane Gorzów Wielkopolski.txt" #sciezka do pliku

with open(path, "r", encoding = "cp1250") as f: #import pliku i zaczytujemy go
    text = f.read()


blocks = re.split(r"=+\s*:\s*", text) #tam gdzie są te ==== to dzielimy na bloki
records = []    #lista do której dodamy później

for block in blocks:    #na każdym podzielonym bloczku
    data = {}   #robimy slownik
    current_prefix = "" #tutaj to miało ogarnąć znestowane sekcje xD

    for line in block.splitlines(): #W kazdej transakcji mamy klucz i wartosc to ogarniemy to jako slownik
        if ":" in line: # Jezeli linia ma jakies info dla nas a nie jest pusta albo jakas dziwna. Tu do zmiany bo dlugie opisy przez to sie nie zapisuja
            key, val = line.split(":", 1)   #dzielimy sobie na lewo i prawo od :
            key = key.strip() #czyszonko
            val = val.strip() #same

            if val == "": # wartosc jest pusta to mamy poczatek jakiejs sekcji
                current_prefix = key
                continue
            full_key = f"{current_prefix}_{key}" if current_prefix else key #tutaj sobie laczymy sekcje do klucza typu "Dzialki" + "identyfikator dzialki"
            data[full_key] = val

    if data: #jezeli cos zebralismy to wrzucamy do listy
        records.append(data)

df = pd.DataFrame(records) #robimy z tego tabele

df.to_csv(r"Z:\_______Przenoszenie\Nowy folder (2)\dane Gorzów Wielkopolski.csv", index = False, sep = ";", encoding = "cp1250") #zapis

print(df.columns.tolist())
print(df.head())
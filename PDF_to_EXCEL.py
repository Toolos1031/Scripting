from pypdf import PdfReader
import re
import pandas as pd


#Initialize PDFREADER class
reader = PdfReader(r"D:\Fotowoltaika\ORLEN PLOCK\plock_2_v2.pdf")

#Set patterns for regex
nazwa_pliku_pattern = r"Nazwa pliku:\s*(.*?)\s*Numer wskazania:"
numer_wskazania_pattern = r'Numer wskazania:\s*(.*?)\s*Szczegóły inspekcji'
numer_wskazania_pattern2 = r'Numer wskazania:\s*(.*?)\s*Rodzaj'
uszkodzenie_pattern = r"Uszkodzenie:\s*(.*?)\s*Lokalizacja:"
uszkodzenie_pattern2 = r"Rodzaj:\s*(.*?)\s*Lokalizacja:"
uszkodzenie_pattern3 = r"Rodzaj:\s*(.*)"
stol_panel_pattern = r"Panel:\s*(.*?)\s*Zdjęcie"
rzad_panel_pattern = r"Panel:\s*(.*?)\s*SQ1"
min_pattern = r"MIN\s*(.*?)\s*Średnia"
min_pattern2 = r"MIN\s*(.*?)\s*AVERAGE"
srednia_pattern = r"Średnia\s*(.*?)\s*MAX"
srednia_pattern2 = r"AVERAGE\s*(.*?)\s*MAX"
max_pattern = r"MAX\s*(.*?)\s*Pomiar"
max_pattern2 = r"MAX\s*(.*?)\s*℃"


#Rekomendacje

rec = {
    "Zabrudzenie" : "Umycie paneli",
    "Hot-Spot" : "Wymiana panela",
    "Hot Spot " : "Wymiana panela",
    "Hot spot" : "Wymiana panela",
    "Hot Spot" : "Wymiana panela",
    "Hot-spot" : "Wymiana panela",
    "Hot spot " : "Wymiana panela",
    "Dioda" : "Wymiana panela",
    "Puszka" : "Wymiana puszki",
    "Zacienienie" : "Wycinka",
    " Zacienienie" : "Wycinka"
}


#Initialize dataframe
columns = ["Numer wskazania", "Stół", "Panel", "Rodzaj uszkodzenia", "Rekomendacje", "Numer zdjęcia termalnego", "Numer zdjęcia RGB", "MIN", "SREDNIA", "MAX"]
df = pd.DataFrame(columns = columns)

#Some retarded splitting
def reg_split(text): 
    nazwa_pliku =  re.search(nazwa_pliku_pattern, text, re.DOTALL).group(1).strip()
    numer_wskazania = re.search(numer_wskazania_pattern, text, re.DOTALL).group(1).strip()
    if "Rodzaj" in numer_wskazania:
        numer_wskazania = re.search(numer_wskazania_pattern2, text, re.DOTALL).group(1).strip()
    try:
        uszkodzenie = re.search(uszkodzenie_pattern, text, re.DOTALL).group(1).strip()
    except AttributeError:
        try:
            uszkodzenie = re.search(uszkodzenie_pattern2, text, re.DOTALL).group(1).strip()
        except AttributeError:
            uszkodzenie = re.search(uszkodzenie_pattern3, text, re.DOTALL).group(1).strip()
    try:
        stol_panel = re.search(stol_panel_pattern, text, re.DOTALL).group(1).strip() #Depends if he used Stol czy Rzad
        if "MIN" in stol_panel:
            try:
                stol_panel = re.search(rzad_panel_pattern, text, re.DOTALL).group(1).strip()
            except:
                pass
    except AttributeError:
        stol_panel = re.search(rzad_panel_pattern, text, re.DOTALL).group(1).strip()

    nazwa_pliku_parts = nazwa_pliku.split("\n")

    if len(nazwa_pliku_parts) > 2: #Connect names together to get full names
        thermal = nazwa_pliku_parts[0] + nazwa_pliku_parts[1] + ".JPG"
        rgb = nazwa_pliku_parts[2] + nazwa_pliku_parts[3] + ".JPG"
    else:
        thermal = nazwa_pliku_parts[0] + nazwa_pliku_parts[1] + ".JPG"
        rgb = None

    uszkodzenie_parts = uszkodzenie.split("-")
    try: #Get rid of the space in Hot -Spot
        uszkodzenie_parts = uszkodzenie_parts[0] + uszkodzenie_parts[1]
    except IndexError:
        pass

    try: #In the case of multiple damages with \n symbol
        uszkodzenie = uszkodzenie_parts.replace("\n", ",")
    except AttributeError:
        pass
    
    symbol_list = [" – ", " –", " -", "– ", "–"] #Depends on how he wrote it

    for symbol in symbol_list:
        try:
            stol_panel1 = stol_panel.split(symbol)
            stol, panel = stol_panel1
            break
        except ValueError:
            pass

    try:
        min_pomiar =  re.search(min_pattern, text, re.DOTALL).group(1).strip()
    except:
        try:
            min_pomiar =  re.search(min_pattern2, text, re.DOTALL).group(1).strip()
        except:
            min_pomiar = None

    try:
        srednia_pomiar =  re.search(srednia_pattern, text, re.DOTALL).group(1).strip()
    except:
        try:
            srednia_pomiar =  re.search(srednia_pattern2, text, re.DOTALL).group(1).strip()
        except:
            srednia_pomiar = None

    try:
        max_pomiar =  re.search(max_pattern, text, re.DOTALL).group(1).strip()
    except:
        try:
            max_pomiar =  re.search(max_pattern2, text, re.DOTALL).group(1).strip()
        except:
            max_pomiar = None

    do_usuniecia = "Pomiar" #Try to remove this string
    do_usuniecia1 = "Pomiary"

    if do_usuniecia in panel or do_usuniecia1 in panel:
        panel = panel.rstrip("\nPomiar")
        panel = panel.rstrip("\nPomiary")

    if do_usuniecia in uszkodzenie or do_usuniecia1 in uszkodzenie:
        uszkodzenie = uszkodzenie.rstrip(",Pomiar")
        uszkodzenie = uszkodzenie.rstrip(",Pomiary")

    return(thermal, rgb, numer_wskazania, uszkodzenie, stol, panel, min_pomiar, srednia_pomiar, max_pomiar)

a = 1
#"""
for i in range(len(reader.pages)): 
    page = reader.pages[i]
    text = page.extract_text()
    rekomendacje = []
    try:
        thermal, rgb, numer_wskazania, uszkodzenie, stol, panel, min_pomiar, srednia_pomiar, max_pomiar = reg_split(text)
        for k in uszkodzenie.split(","): #Compare damage with recommendation dictionary
            if rec[k] in rekomendacje:
                pass
            else:
                rekomendacje.append(rec[k])
        
        if len(rekomendacje) > 1: #Make lists to string
            recommend = rekomendacje[0] + ", " + rekomendacje[1]
        elif len(rekomendacje) == 1:
            recommend = rekomendacje[0]

        print(f"Strona: {a}, \n Numer wskazania: {numer_wskazania}, \n Stół: {stol}, \n Panel: {panel}, \n Rodzaj uszkodzenia: {uszkodzenie}, \n Rekomendacje: {rekomendacje}, \n Numer zdjęcia termalnego: {thermal}, \n Numer zdjęcia RGB: {rgb}, \n\n\n")
        df.loc[i] = [numer_wskazania, stol, panel, uszkodzenie, recommend, thermal, rgb, min_pomiar, srednia_pomiar, max_pomiar] #Add new rows
    except AttributeError:
        print(f"No data we are looking for, page: {a}")
        pass
    a += 1


file_directory = r"D:\Fotowoltaika\ORLEN PLOCK\plock_2_pomiary.xlsx"
df.to_excel(file_directory)
print(df)
"""
page = reader.pages[5]

text = page.extract_text()
print(text)

thermal, rgb, numer_wskazania, uszkodzenie, stol, panel, min_pomiar, srednia_pomiar, max_pomiar = reg_split(text)

print(f"\n \n \n Strona: {a}, \n Numer wskazania: {numer_wskazania}, \n Stół: {stol}, \n Panel: {panel}, \n Rodzaj uszkodzenia: {uszkodzenie}, \n Numer zdjęcia termalnego: {thermal}, \n Numer zdjęcia RGB: {rgb}, \n MIN: {min_pomiar},  \n SREDNIA: {srednia_pomiar}, \n MAX: {max_pomiar} \n\n\n")


#"""
import pandas as pd


file_path = r"D:\fotowoltaika\wloclawek.xlsx"
out = r"D:\fotowoltaika\wloclawek_excel.xlsx"

column = ["Numer wskazania", "Sektor", "Stol", "Panel", "Rodzaj uszkodzenia", "Rekomendacje", "Thermo", "RBG"]


df = pd.read_excel(file_path)
df.columns = column

new_df = pd.DataFrame(columns=column)
#print(new_df)

#print(df)
a = 1

for cols, rows in df.iterrows():
    #print(rows["Panel"])

    row = rows["Panel"]
    row_1 = row.split(",")

    for i in row_1:

        new_df = new_df._append({"Numer wskazania" : rows["Numer wskazania"],
                                 "Sektor" : rows["Sektor"],
                                 "Stol" : rows["Stol"],
                                 "Panel" : i,
                                 "Rodzaj uszkodzenia" : rows["Rodzaj uszkodzenia"],
                                 "Rekomendacje" : rows["Rekomendacje"],
                                 "Thermo" : rows["Thermo"]}, ignore_index = True)
        #new_df["Numer wskazania"][a] = rows["Numer wskazania"]
        #new_df["Sektor"] = rows["Sektor"]
        #new_df["Stol"] = rows["Stol"]
        #new_df["Panel"] = i
        #new_df["Rodzaj uszkodzenia"] = rows["Rodzaj uszkodzenia"]
        #new_df["Rekomendacje"] = rows["Rekomendacje"]
        #new_df["Thermo"] = rows["Thermo"]
        #print(rows["Numer wskazania"])
        #print(new_df["Numer wskazania"])
        #new_df["RGB"] = rows["RGB"]
        a += 1


new_df.to_excel(out)

import Metashape

print(Metashape.version)

path = r"D:\Atlasus\Naloty\Dane\Dzien_5_6\kot-ser\2_Agi_Export\calibration_project.psx"

doc = Metashape.Document()
doc.open(path) #open existing document

doc.save(path) #save the project under new name (works similar to Save As operation and re-opens document if PSX format is used)
doc.save() #just saves the project under the same name
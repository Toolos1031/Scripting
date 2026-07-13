from PyPDF2 import PdfMerger

# Inicjalizacja narzędzia do łączenia
merger = PdfMerger()

# Dodawanie plików w pożądanej kolejności
merger.append(r"D:\__ORLEN\raport\okładka.pdf")
merger.append(r"D:\__ORLEN\raport\2026.04.21 Raport ORLEN.pdf")

# Zapisywanie gotowego pliku
merger.write(r"D:\__ORLEN\raport\Raport_ORLEN_Pelny.pdf")
merger.close()

print("Pliki zostały pomyślnie połączone!")
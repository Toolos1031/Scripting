import fitz
from PIL import Image
import os
from tqdm import tqdm


folder_path = r"Y:\______Wody_Polskie\Dane_Od_Klienta\Rastry\woj. wielkopolskie\pow. leszczyński\gm. Rydzyna\skany map ewidencji melioracji wodnych gm. Rydzyna\Kłoda"

pdfs = [file for file in os.listdir(folder_path) if file.endswith(".pdf")]

dpi = 300

for pdf in tqdm(pdfs, total = len(pdfs)):
    pdf_path = os.path.join(folder_path, pdf)
    pdf_file = fitz.open(pdf_path)
    
    page = pdf_file.load_page(0)
    pix = page.get_pixmap(dpi = dpi)

    out_folder = folder_path
    out_path = os.path.join(out_folder, pdf.split(".")[0] + ".jpg")

    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img.save(out_path, "JPEG")




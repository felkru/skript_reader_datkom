import fitz  # PyMuPDF
import os
from pathlib import Path

def convert_pdf_to_images(pdf_path, output_folder):
    # Ensure output folder exists
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Open the PDF
    print(f"Opening {pdf_path}...")
    doc = fitz.open(pdf_path)
    
    total_pages = len(doc)
    print(f"Total pages: {total_pages}")
    
    for i in range(total_pages):
        page = doc.load_page(i)
        # Increase resolution if needed. Default is 72 DPI. 
        # zoom_x = 2.0, zoom_y = 2.0 yields 144 DPI.
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        
        output_filename = f"slide_{i+1:03d}.png"
        output_file_path = output_path / output_filename
        
        pix.save(str(output_file_path))
        if (i + 1) % 10 == 0 or (i + 1) == total_pages:
            print(f"Converted {i+1}/{total_pages} pages...")

    doc.close()
    print(f"Successfully converted PDF to images in: {output_folder}")

if __name__ == "__main__":
    pdf_file = "merged.pdf"
    output_dir = "slides"
    
    if os.path.exists(pdf_file):
        convert_pdf_to_images(pdf_file, output_dir)
    else:
        print(f"Error: {pdf_file} not found in the current directory.")

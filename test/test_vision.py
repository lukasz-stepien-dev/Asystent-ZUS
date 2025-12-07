from backend.pdf_engine import convert_pdf_to_images
import os

file_path = "data/wypadek 1/karta wypadku 1.pdf"
if os.path.exists(file_path):
    with open(file_path, "rb") as f:
        images = convert_pdf_to_images(f)
        print(f"Converted {len(images)} images.")
else:
    print("File not found")

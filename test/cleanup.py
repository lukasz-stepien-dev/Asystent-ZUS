import os

files_to_delete = [
    "test_pdf_fill.py",
    "test_report_generation.py",
    "test_vision.py",
    "test_chroma.py"
]

for f in files_to_delete:
    try:
        if os.path.exists(f):
            os.remove(f)
            print(f"Deleted {f}")
        else:
            print(f"{f} not found")
    except Exception as e:
        print(f"Error deleting {f}: {e}")

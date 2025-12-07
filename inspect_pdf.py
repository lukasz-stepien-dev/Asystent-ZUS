import PyPDF2

def inspect_pdf_fields(pdf_path):
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        fields = reader.get_fields()
        if fields:
            for field_name, field_data in fields.items():
                print(f"Field: {field_name}, Type: {field_data.get('/FT')}")
        else:
            print("No form fields found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_pdf_fields("static/zawiadomienie_o_wypadku.pdf")

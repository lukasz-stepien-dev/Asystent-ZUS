from backend.pdf_engine import fill_accident_notification_pdf
import os

def test_fill_pdf():
    data = {
        "PESEL[0]": "12345678901",
        "Imię[0]": "Jan",
        "Nazwisko[0]": "Kowalski",
        "Datawyp[0]": "2023-10-27",
        "Miejscewyp[0]": "Warszawa, ul. Prosta 1"
    }
    
    pdf_content = fill_accident_notification_pdf(data)
    
    if pdf_content:
        with open("test_filled.pdf", "wb") as f:
            f.write(pdf_content)
        print("PDF generated successfully: test_filled.pdf")
    else:
        print("Failed to generate PDF")

if __name__ == "__main__":
    test_fill_pdf()

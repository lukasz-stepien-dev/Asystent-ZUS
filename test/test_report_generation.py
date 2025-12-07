from backend.pdf_engine import generate_accident_notification_pdf
import os

def test_generate_report():
    data = {
        "karta_wypadku": {
            "data_zdarzenia": "2023-10-27",
            "godzina_zdarzenia": "10:00",
            "miejsce_wypadku": "Warszawa, ul. Żółwia 1 (test polskich znaków: ąęśćżźńłó)",
            "planowana_godzina_rozpoczecia_pracy": "08:00",
            "planowana_godzina_zakonczenia_pracy": "16:00",
            "rodzaj_czynnosci_do_wypadku": "Praca biurowa",
            "opis_okolicznosci_i_przyczyn": "Poślizgnięcie się na mokrej podłodze. ĄĘŚĆŻŹŃŁÓ",
            "rodzaj_odniesionych_urazow": "Złamanie ręki",
            "pierwsza_pomoc_udzielono": "Tak",
            "placowka_medyczna": "Szpital Bielański",
            "rozpoznany_uraz_medyczny": "Złamanie kości promieniowej",
            "analiza_bhp": "Brak uwag"
        },
        "decyzja": "UZNAĆ",
        "uzasadnienie": "Wypadek przy pracy. Spełnia przesłanki ustawowe. ĄĘŚĆŻŹŃŁÓ",
        "niezgodnosci_lub_braki": "Brak"
    }
    
    pdf_content = generate_accident_notification_pdf(data)
    
    if pdf_content:
        with open("test_report.pdf", "wb") as f:
            f.write(pdf_content)
        print("PDF generated successfully: test_report.pdf")
    else:
        print("Failed to generate PDF")

if __name__ == "__main__":
    test_generate_report()

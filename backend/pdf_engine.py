import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import datetime
import re

def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        return f"Błąd odczytu PDF: {str(e)}"

def generate_accident_notification_pdf(accident_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='CustomNormal', parent=styles['Normal'], fontSize=10, leading=14))
    styles.add(ParagraphStyle(name='CustomHeading1', parent=styles['h1'], fontSize=16, leading=18, spaceAfter=12))
    styles.add(ParagraphStyle(name='CustomHeading2', parent=styles['h2'], fontSize=12, leading=14, spaceBefore=10,
                              spaceAfter=6))

    story = []
    story.append(Paragraph("<b>Zawiadomienie o Wypadku Przy Pracy</b>", styles['CustomHeading1']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Data generacji dokumentu:</b> {datetime.date.today().strftime('%d-%m-%Y')}",
                           styles['CustomNormal']))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Dane Wypadku:</b>", styles['CustomHeading2']))
    karta_wypadku = accident_data.get("karta_wypadku", {})
    if karta_wypadku:
        story.append(Paragraph(f"<b>Data zdarzenia:</b> {karta_wypadku.get('data_zdarzenia', 'Brak danych')}",
                               styles['CustomNormal']))
        story.append(Paragraph(f"<b>Godzina zdarzenia:</b> {karta_wypadku.get('godzina_zdarzenia', 'Brak danych')}",
                               styles['CustomNormal']))
        story.append(Paragraph(f"<b>Miejsce wypadku:</b> {karta_wypadku.get('miejsce_wypadku', 'Brak danych')}",
                               styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Planowana godzina rozpoczęcia pracy:</b> {karta_wypadku.get('planowana_godzina_rozpoczecia_pracy', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Planowana godzina zakończenia pracy:</b> {karta_wypadku.get('planowana_godzina_zakonczenia_pracy', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Rodzaj czynności do momentu wypadku:</b> {karta_wypadku.get('rodzaj_czynnosci_do_wypadku', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Opis okoliczności i przyczyn:</b> {karta_wypadku.get('opis_okolicznosci_i_przyczyn', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Rodzaj odniesionych urazów:</b> {karta_wypadku.get('rodzaj_odniesionych_urazow', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Pierwsza pomoc udzielono:</b> {karta_wypadku.get('pierwsza_pomoc_udzielono', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(Paragraph(f"<b>Placówka medyczna:</b> {karta_wypadku.get('placowka_medyczna', 'Brak danych')}",
                               styles['CustomNormal']))
        story.append(Paragraph(
            f"<b>Rozpoznany uraz medyczny:</b> {karta_wypadku.get('rozpoznany_uraz_medyczny', 'Brak danych')}",
            styles['CustomNormal']))
        story.append(
            Paragraph(f"<b>Analiza BHP:</b> {karta_wypadku.get('analiza_bhp', 'Brak danych')}", styles['CustomNormal']))
    else:
        story.append(Paragraph("Brak danych w Karcie Wypadku.", styles['CustomNormal']))
    story.append(Spacer(1, 12))

    if "decyzja" in accident_data:
        story.append(Paragraph(f"<b>Decyzja ZUS:</b> {accident_data['decyzja']}", styles['CustomNormal']))
    story.append(Spacer(1, 6))

    if "uzasadnienie" in accident_data:
        story.append(Paragraph("<b>Uzasadnienie:</b>", styles['CustomHeading2']))
        story.append(Paragraph(accident_data['uzasadnienie'], styles['CustomNormal']))
    story.append(Spacer(1, 6))

    if "niezgodnosci_lub_braki" in accident_data and accident_data['niezgodnosci_lub_braki'] != "Brak":
        story.append(Paragraph("<b>Wykryte niezgodności / Braki w dokumentacji:</b>", styles['CustomHeading2']))
        niezgodnosci_data = accident_data['niezgodnosci_lub_braki']
        if isinstance(niezgodnosci_data, list):
            niezgodnosci_text = "<br/>".join(niezgodnosci_data)
        else:
            niezgodnosci_text = str(niezgodnosci_data)
        story.append(Paragraph(niezgodnosci_text, styles['CustomNormal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def generate_explanation_pdf(chat_messages):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(name='ChatUser', parent=styles['Normal'], fontSize=10, leading=14, textColor='#333333'))
    styles.add(ParagraphStyle(name='ChatBot', parent=styles['Normal'], fontSize=10, leading=14, textColor='#0055AA'))
    styles.add(ParagraphStyle(name='CustomHeading1', parent=styles['h1'], fontSize=16, leading=18, spaceAfter=12))

    story = []
    story.append(Paragraph("<b>Wyjaśnienia Poszkodowanego (Transcript rozmowy z botem)</b>", styles['CustomHeading1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Data rozmowy:</b> {datetime.date.today().strftime('%d-%m-%Y')}", styles['Normal']))
    story.append(Spacer(1, 12))

    for msg in chat_messages:
        role = "Obywatel" if msg["role"] == "user" else "ZUS Bot"
        style = styles['ChatUser'] if msg["role"] == "user" else styles['ChatBot']

        content_text = msg['content']
        if msg["role"] == "user" and "Jesteś wirtualnym asystentem ZUS" in content_text:
            content_text = re.sub(r"Jesteś wirtualnym asystentem ZUS.*?(\n\n|$)", "", content_text,
                                  flags=re.DOTALL | re.IGNORECASE)
            content_text = content_text.strip()
            if not content_text:
                continue

        story.append(Paragraph(f"<b>{role}:</b> {content_text}", style))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def fill_accident_notification_pdf(data):
    input_pdf_path = "static/zawiadomienie_o_wypadku.pdf"
    output_buffer = BytesIO()
    
    try:
        reader = PyPDF2.PdfReader(input_pdf_path)
        writer = PyPDF2.PdfWriter()
        
        # Copy all pages
        for page in reader.pages:
            writer.add_page(page)
            
        # Update form fields
        for page in writer.pages:
            writer.update_page_form_field_values(page, data)
            
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer.getvalue()
    except Exception as e:
        print(f"Błąd wypełniania PDF: {e}")
        return None

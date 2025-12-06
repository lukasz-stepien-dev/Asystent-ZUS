import streamlit as st
from backend.ai_engine import get_citizen_chat_response, analyze_case_for_officer
from backend.pdf_engine import extract_text_from_pdf
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import datetime
import json

st.set_page_config(page_title="ZANT - System ZUS", layout="wide")
st.title("ZANT - System Wypadkowy ZUS")


def generate_accident_notification_pdf(accident_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph("<b>Zawiadomienie o Wypadku Przy Pracy</b>", styles['h1']))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"<b>Data zgłoszenia:</b> {datetime.date.today().strftime('%d-%m-%Y')}", styles['Normal']))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Dane Wypadku:</b>", styles['h2']))
    for key, value in accident_data.get("karta_wypadku", {}).items():
        story.append(Paragraph(f"<b>{key.replace('_', ' ').capitalize()}:</b> {value}", styles['Normal']))
    story.append(Spacer(1, 12))

    if "decyzja" in accident_data:
        story.append(Paragraph(f"<b>Decyzja ZUS:</b> {accident_data['decyzja']}", styles['Normal']))
    if "uzasadnienie" in accident_data:
        story.append(Paragraph("<b>Uzasadnienie:</b>", styles['h2']))
        story.append(Paragraph(accident_data['uzasadnienie'], styles['Normal']))

    if "niezgodnosci_lub_braki" in accident_data and accident_data['niezgodnosci_lub_braki'] != "Brak":
        story.append(Paragraph("<b>Wykryte niezgodności / Braki:</b>", styles['h2']))

        niezgodnosci_data = accident_data['niezgodnosci_lub_braki']
        if isinstance(niezgodnosci_data, list):
            niezgodnosci_text = ", ".join(niezgodnosci_data)
        else:
            niezgodnosci_text = str(niezgodnosci_data)

        story.append(Paragraph(niezgodnosci_text, styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_explanation_pdf(chat_messages):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph("<b>Wyjaśnienia Poszkodowanego (Transcript rozmowy z botem)</b>", styles['h1']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Data rozmowy:</b> {datetime.date.today().strftime('%d-%m-%Y')}", styles['Normal']))
    story.append(Spacer(1, 12))

    for msg in chat_messages:
        role = "Obywatel" if msg["role"] == "user" else "ZUS Bot"
        story.append(Paragraph(f"<b>{role}:</b> {msg['content']}", styles['Normal']))
        story.append(Spacer(1, 6))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


role = st.sidebar.radio("Wybierz moduł:", ["Obywatel (Zgłoszenie)", "Pracownik ZUS (Decyzja)"])

if role == "Obywatel (Zgłoszenie)":
    st.header("Zgłoś wypadek przy pracy")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "final_citizen_description" not in st.session_state:
        st.session_state.final_citizen_description = ""
    if "conversation_finished" not in st.session_state:
        st.session_state.conversation_finished = False

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.conversation_finished:
        prompt = st.chat_input("Opisz zdarzenie...")
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            response = get_citizen_chat_response(st.session_state.messages)

            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

            if "podsumowując" in response.lower() or "czy to wszystko" in response.lower() or "dziękuję za informacje" in response.lower():
                st.session_state.conversation_finished = True
                user_messages_content = [msg["content"] for msg in st.session_state.messages if msg["role"] == "user"]
                st.session_state.final_citizen_description = "\n".join(user_messages_content)
                st.success("Rozmowa zakończona. Możesz teraz pobrać dokumenty.")
    else:
        st.info("Rozmowa została zakończona. Możesz przejść do panelu pracownika ZUS, aby kontynuować.")

    if st.session_state.conversation_finished and st.session_state.messages:
        st.subheader("Pobierz dokumenty")

        explanation_pdf = generate_explanation_pdf(st.session_state.messages)
        st.download_button(
            label="Pobierz Wyjaśnienia Poszkodowanego (PDF)",
            data=explanation_pdf,
            file_name="wyjasnienia_poszkodowanego.pdf",
            mime="application/pdf"
        )

        st.markdown(
            "<i>Zawiadomienie o wypadku będzie dostępne do pobrania w module 'Pracownik ZUS (Decyzja)' po analizie sprawy.</i>")


elif role == "Pracownik ZUS (Decyzja)":
    st.header("Panel Orzecznika - Wsparcie Decyzji")

    st.markdown("### Dane z zgłoszenia obywatela")
    citizen_desc_from_chat = st.session_state.get("final_citizen_description", "")
    citizen_desc_input = st.text_area(
        "Opis zgłoszenia (możesz edytować lub wkleić z czatu)",
        value=citizen_desc_from_chat,
        height=200
    )

    st.markdown("### Wgraj dokumentację")
    uploaded_medical_file = st.file_uploader("Wgraj dokumentację medyczną (PDF)", type=['pdf'], key="medical_pdf")
    uploaded_workplace_file = st.file_uploader("Wgraj dokumentację miejsca pracy (PDF)", type=['pdf'],
                                               key="workplace_pdf")

    if st.button("Analizuj sprawę"):
        with st.spinner("Analiza orzecznictwa i dokumentacji..."):
            medical_pdf_text = ""
            if uploaded_medical_file:
                medical_pdf_text = extract_text_from_pdf(uploaded_medical_file)
            else:
                st.warning("Nie wgrano pliku PDF z dokumentacją medyczną – analiza będzie mniej kompletna.")

            workplace_pdf_text = ""
            if uploaded_workplace_file:
                workplace_pdf_text = extract_text_from_pdf(uploaded_workplace_file)
            else:
                st.warning("Nie wgrano pliku PDF z dokumentacją miejsca pracy – analiza będzie mniej kompletna.")

            if not citizen_desc_input:
                st.error("Proszę wprowadzić opis zgłoszenia od obywatela.")
            else:
                wynik = analyze_case_for_officer(citizen_desc_input, medical_pdf_text, workplace_pdf_text)
                st.session_state.zus_analysis_result = wynik  # Store result for PDF generation

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Rekomendacja")
                    decyzja = wynik.get("decyzja", "BRAK DANYCH")

                    if "UZNAĆ" in decyzja.upper():
                        st.success(f"✅ {decyzja}")
                    elif "ODMÓWIĆ" in decyzja.upper():
                        st.error(f"❌ {decyzja}")
                    elif "WYMAGA UZUPEŁNIENIA" in decyzja.upper():
                        st.warning(f"⚠️ {decyzja}")
                    else:
                        st.warning(f"⚠️ {decyzja}")

                with col2:
                    st.subheader("Uzasadnienie Prawne")
                    st.write(wynik.get("uzasadnienie", "Brak uzasadnienia"))

                st.subheader("Wykryte niezgodności / Braki")
                niezgodnosci = wynik.get("niezgodnosci_lub_braki", "Brak")
                if niezgodnosci == "Brak":
                    st.info("Brak wykrytych niezgodności lub braków.")
                else:
                    st.warning(niezgodnosci)

                st.subheader("Projekt Karty Wypadku")
                st.json(wynik.get("karta_wypadku", {}))

    if "zus_analysis_result" in st.session_state and st.session_state.zus_analysis_result:
        st.subheader("Pobierz Zawiadomienie o Wypadku")
        accident_notification_pdf = generate_accident_notification_pdf(st.session_state.zus_analysis_result)
        st.download_button(
            label="Pobierz Zawiadomienie o Wypadku (PDF)",
            data=accident_notification_pdf,
            file_name="zawiadomienie_o_wypadku.pdf",
            mime="application/pdf"
        )
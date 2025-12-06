import streamlit as st
from backend.ai_engine import analyze_case_for_officer
from backend.pdf_engine import extract_text_from_pdf, generate_accident_notification_pdf
import datetime

def officer_module():
    st.header("Panel Orzecznika - Wsparcie Decyzji")

    st.markdown("### Dane z zgłoszenia obywatela")
    citizen_desc_from_chat = st.session_state.get("final_citizen_description", "")
    citizen_desc_input = st.text_area(
        "Opis zgłoszenia (możesz edytować lub wkleić z czatu)",
        value=citizen_desc_from_chat,
        height=200
    )

    st.markdown("### Wgraj dokumentację")
    uploaded_medical_file = st.file_uploader("Wgraj dokumentację medyczną (zaświadczenie o stanie zdrowia) - PDF",
                                             type=['pdf'], key="medical_pdf")
    uploaded_workplace_file = st.file_uploader("Wgraj dokumentację miejsca pracy (zaświadczenie od pracodawcy) - PDF",
                                               type=['pdf'], key="workplace_pdf")

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
            file_name=f"zawiadomienie_o_wypadku_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
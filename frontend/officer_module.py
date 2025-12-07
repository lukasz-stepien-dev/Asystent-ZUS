import streamlit as st
from backend.ai_engine import analyze_case_for_officer
from backend.pdf_engine import extract_text_from_pdf, generate_accident_notification_pdf, convert_pdf_to_images
import datetime
import base64

def officer_module():
    st.header("Panel Orzecznika - Wsparcie Decyzji")

    st.markdown("### Dane z zgłoszenia obywatela")
    citizen_desc_from_chat = st.session_state.get("final_citizen_description", "")
    citizen_desc_input = st.text_area(
        "Opis zgłoszenia (możesz edytować lub wkleić z czatu)",
        value=citizen_desc_from_chat,
        placeholder="Wprowadź opis zgłoszenie...",
        height=200
    )

    st.markdown("### Wgraj dokumentację")
    st.info("Należy wgrać: opinię w sprawie kwalifikacji wypadku, zapis wyjaśnień, zawiadomienie o wypadku.")

    uploaded_files = st.file_uploader("Wgraj dokumenty (PDF) - bez limitu",
                                      type=['pdf'], accept_multiple_files=True, key="officer_docs")

    if st.button("Analizuj sprawę"):
        with st.spinner("Analiza orzecznictwa i dokumentacji (Vision)..."):
            documentation_text = ""
            documentation_images = []
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    uploaded_file.seek(0)
                    images = convert_pdf_to_images(uploaded_file)
                    documentation_images.extend(images)
                    
                    # Text extraction
                    uploaded_file.seek(0)
                    text = extract_text_from_pdf(uploaded_file)
                    documentation_text += f"\n--- DOKUMENT: {uploaded_file.name} ---\n{text}\n"
            else:
                st.warning("Nie wgrano żadnych dokumentów - analiza będzie mniej kompletna.")

            if not citizen_desc_input:
                st.error("Proszę wprowadzić opis zgłoszenia od obywatela.")
            else:
                wynik = analyze_case_for_officer(citizen_desc_input, documentation_images, documentation_text)
                st.session_state.zus_analysis_result = wynik 

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
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Pobierz Zawiadomienie o Wypadku (PDF)",
                data=accident_notification_pdf,
                file_name=f"zawiadomienie_o_wypadku_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col2:
            if st.button("🖨️ Drukuj Zawiadomienie", use_container_width=True):
                base64_pdf = base64.b64encode(accident_notification_pdf).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
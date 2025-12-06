import streamlit as st
from backend.ai_engine import get_citizen_chat_response, analyze_case_for_officer
from backend.pdf_engine import extract_text_from_pdf

st.set_page_config(page_title="ZANT - System ZUS", layout="wide")
st.title("ZANT - System Wypadkowy ZUS")

role = st.sidebar.radio("Wybierz moduł:", ["Obywatel (Zgłoszenie)", "Pracownik ZUS (Decyzja)"])

if role == "Obywatel (Zgłoszenie)":
    st.header("Zgłoś wypadek przy pracy")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Opisz zdarzenie..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        response = get_citizen_chat_response(st.session_state.messages)

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

elif role == "Pracownik ZUS (Decyzja)":
    st.header("Panel Orzecznika - Wsparcie Decyzji")

    uploaded_file = st.file_uploader("Wgraj dokumentację (PDF)", type=['pdf'])

    citizen_desc = st.text_area("Opis zgłoszenia (wpisz ręcznie lub wklej z czatu)")

    if st.button("Analizuj sprawę"):
        with st.spinner("Analiza orzecznictwa i dokumentacji..."):

            pdf_text = ""
            if uploaded_file:
                pdf_text = extract_text_from_pdf(uploaded_file)
            else:
                st.warning("Nie wgrano pliku PDF – analiza oparta tylko o opis.")

            wynik = analyze_case_for_officer(citizen_desc, pdf_text)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Rekomendacja")
                decyzja = wynik.get("decyzja", "BRAK DANYCH")

                if "UZNAĆ" in decyzja.upper():
                    st.success(f"✅ {decyzja}")
                elif "ODMÓWIĆ" in decyzja.upper():
                    st.error(f"❌ {decyzja}")
                else:
                    st.warning(f"⚠️ {decyzja}")

            with col2:
                st.subheader("Uzasadnienie Prawne")
                st.write(wynik.get("uzasadnienie", "Brak uzasadnienia"))

            st.subheader("Projekt Karty Wypadku")
            st.json(wynik.get("karta_wypadku", {}))
import streamlit as st
from backend.ai_engine import get_citizen_chat_response
from backend.pdf_engine import generate_explanation_pdf
import datetime

def citizen_module():
    st.header("Zgłoś wypadek przy pracy")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "final_citizen_description" not in st.session_state:
        st.session_state.final_citizen_description = ""
    if "conversation_finished" not in st.session_state:
        st.session_state.conversation_finished = False

    if not st.session_state.messages:
        initial_bot_message = "Witaj! Jestem wirtualnym asystentem ZUS i pomogę Ci zgłosić wypadek przy pracy. Pamiętaj, że wszystkie podane informacje powinny być zgodne z prawdą, ponieważ zostaną później porównane z dokumentacją. Aby rozpocząć, proszę opisz, co dokładnie się stało."
        st.session_state.messages.append({"role": "assistant", "content": initial_bot_message})

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

            if any(phrase in response.lower() for phrase in [
                "podsumowując", "dziękuję za informacje", "rozumiem wszystkie",
                "czy to wszystko", "wszystkie potrzebne dane zostały zebrane",
                "to koniec", "czy mogę w czymś jeszcze pomóc"
            ]):
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
            file_name=f"wyjasnienia_poszkodowanego_{datetime.date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )

        st.markdown(
            "<i>Zawiadomienie o wypadku będzie dostępne do pobrania w module 'Pracownik ZUS (Decyzja)' po analizie sprawy.</i>")
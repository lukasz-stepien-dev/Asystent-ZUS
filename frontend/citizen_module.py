import streamlit as st
from backend.ai_engine import get_citizen_chat_response, extract_accident_data_for_pdf
from backend.pdf_engine import generate_explanation_pdf, fill_accident_notification_pdf
from backend.prompts import CITIZEN_SYSTEM_PROMPT, BUSINESS_SYSTEM_PROMPT
import datetime
import base64

def citizen_module():
    st.header("Zgłoś wypadek przy pracy")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "final_citizen_description" not in st.session_state:
        st.session_state.final_citizen_description = ""
    if "conversation_finished" not in st.session_state:
        st.session_state.conversation_finished = False
    if "selected_path" not in st.session_state:
        st.session_state.selected_path = None
    if "processing" not in st.session_state:
        st.session_state.processing = False
    if "accident_notification_pdf" not in st.session_state:
        st.session_state.accident_notification_pdf = None

    if st.session_state.selected_path is None:
        st.write("Witaj! Jestem wirtualnym asystentem ZUS.")
        st.write("Wybierz rodzaj zgłoszenia:")
        
        col1, col2, _ = st.columns([1, 1, 3])
        
        with col1:
            if st.button("Zawiadomienie o wypadku", use_container_width=True):
                st.session_state.selected_path = "business"
                initial_bot_message = "Dzień dobry. Przyjmuję zgłoszenie wypadku osoby prowadzącej działalność. Pamiętaj, że wszystkie podane informacje powinny być zgodne z prawdą. Proszę opisz, co się stało."
                st.session_state.messages.append({"role": "assistant", "content": initial_bot_message})
                st.rerun()
                
        with col2:
            if st.button("Zapis wyjaśnień poszkodowanego", use_container_width=True):
                st.session_state.selected_path = "citizen"
                initial_bot_message = "Dzień dobry. Słucham Twoich wyjaśnień dotyczących wypadku. Pamiętaj, że wszystkie podane informacje powinny być zgodne z prawdą. Proszę opisz dokładnie przebieg zdarzenia."
                st.session_state.messages.append({"role": "assistant", "content": initial_bot_message})
                st.rerun()
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not st.session_state.conversation_finished:
        def disable_chat():
            st.session_state.processing = True

        prompt = st.chat_input("Opisz zdarzenie...", key="user_input", on_submit=disable_chat, disabled=st.session_state.processing)

        if st.session_state.processing and st.session_state.get("user_input"):
            prompt = st.session_state.user_input
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            system_prompt = BUSINESS_SYSTEM_PROMPT if st.session_state.selected_path == "business" else CITIZEN_SYSTEM_PROMPT
            response = get_citizen_chat_response(st.session_state.messages, system_prompt=system_prompt)

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

            st.session_state.processing = False
            st.rerun()
    else:
        st.info("Rozmowa została zakończona. Możesz przejść do panelu pracownika ZUS, aby kontynuować.")

    if st.session_state.conversation_finished and st.session_state.messages:
        st.subheader("Pobierz dokumenty")

        if st.session_state.selected_path == "citizen":
            explanation_pdf = generate_explanation_pdf(st.session_state.messages)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Pobierz Wyjaśnienia Poszkodowanego (PDF)",
                    data=explanation_pdf,
                    file_name=f"wyjasnienia_poszkodowanego_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            print_citizen = False
            with col2:
                if st.button("🖨️ Drukuj Wyjaśnienia", use_container_width=True):
                    print_citizen = True
            
            if print_citizen:
                base64_pdf = base64.b64encode(explanation_pdf).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)

        if st.session_state.selected_path == "business":
            if st.session_state.accident_notification_pdf is None:
                 with st.spinner("Generowanie Zawiadomienia o wypadku..."):
                    accident_data = extract_accident_data_for_pdf(st.session_state.messages)
                    st.session_state.accident_notification_pdf = fill_accident_notification_pdf(accident_data)
            
            if st.session_state.accident_notification_pdf:
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="Pobierz Zawiadomienie o Wypadku (PDF)",
                        data=st.session_state.accident_notification_pdf,
                        file_name=f"zawiadomienie_o_wypadku_{datetime.date.today().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                print_business = False
                with col2:
                    if st.button("🖨️ Drukuj Zawiadomienie", use_container_width=True):
                        print_business = True
                
                if print_business:
                    base64_pdf = base64.b64encode(st.session_state.accident_notification_pdf).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)

import streamlit as st
from frontend import citizen_module, officer_module
from backend.pdf_engine import fill_accident_notification_pdf

st.set_page_config(page_title="ZANT - System ZUS", layout="wide")

with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("ZANT - System Wypadkowy ZUS")

if "current_module" not in st.session_state:
    st.session_state.current_module = "obywatel"

def show_module():
    if st.session_state.current_module == "obywatel":
        citizen_module.citizen_module()
    elif st.session_state.current_module == "zus":
        officer_module.officer_module()

st.sidebar.image("static/zus_logo.png", use_container_width=True)

citizen_type = "primary" if st.session_state.current_module == "obywatel" else "secondary"
zus_type = "primary" if st.session_state.current_module == "zus" else "secondary"

if st.sidebar.button("👤\nObywatel", use_container_width=True, type=citizen_type):
    st.session_state.current_module = "obywatel"
    st.rerun()
if st.sidebar.button("🏢\nZUS", use_container_width=True, type=zus_type):
    st.session_state.current_module = "zus"
    st.rerun()

# with st.sidebar.expander("🔧 Debug / Testy"):
#     if st.button("🚀 Szybki test - Obywatel"):
#         st.session_state.current_module = "obywatel"
#         st.session_state.selected_path = "citizen"
#         st.session_state.conversation_finished = True
#         st.session_state.messages = [
#             {"role": "assistant", "content": "Dzień dobry. Słucham Twoich wyjaśnień..."},
#             {"role": "user", "content": "Złamałem nogę w pracy."},
#             {"role": "assistant", "content": "Rozumiem. Kiedy to się stało?"},
#             {"role": "user", "content": "Wczoraj o 14:00."},
#             {"role": "assistant", "content": "Dziękuję za informacje."}
#         ]
#         st.session_state.final_citizen_description = "Złamałem nogę w pracy. Wczoraj o 14:00."
#         st.rerun()

#     if st.button("🚀 Szybki test - Firma"):
#         st.session_state.current_module = "obywatel"
#         st.session_state.selected_path = "business"
#         st.session_state.conversation_finished = True
#         st.session_state.messages = [
#             {"role": "assistant", "content": "Dzień dobry. Przyjmuję zgłoszenie wypadku..."},
#             {"role": "user", "content": "Pracownik Jan Kowalski uległ wypadkowi."},
#             {"role": "assistant", "content": "Proszę podać szczegóły."},
#             {"role": "user", "content": "Spadł z drabiny."},
#             {"role": "assistant", "content": "Dziękuję za informacje."}
#         ]
#         st.session_state.final_citizen_description = "Pracownik Jan Kowalski uległ wypadkowi. Spadł z drabiny."
#         # Generate dummy PDF to skip AI generation
#         st.session_state.accident_notification_pdf = fill_accident_notification_pdf({})
#         st.rerun()

show_module()
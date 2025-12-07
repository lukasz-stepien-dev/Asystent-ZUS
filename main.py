import streamlit as st
from frontend import citizen_module, officer_module

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

st.sidebar.title("Nawigacja")
if st.sidebar.button("👤\nObywatel", use_container_width=True):
    st.session_state.current_module = "obywatel"
if st.sidebar.button("🏢\nZUS", use_container_width=True):
    st.session_state.current_module = "zus"

show_module()
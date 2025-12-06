import streamlit as st
from frontend import citizen_module, officer_module

st.set_page_config(page_title="ZANT - System ZUS", layout="wide")
st.title("ZANT - System Wypadkowy ZUS")

role = st.sidebar.radio("Wybierz moduł:", ["Obywatel (Zgłoszenie)", "Pracownik ZUS (Decyzja)"])

if role == "Obywatel (Zgłoszenie)":
    citizen_module.citizen_module()
elif role == "Pracownik ZUS (Decyzja)":
    officer_module.officer_module()
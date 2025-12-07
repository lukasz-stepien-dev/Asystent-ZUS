import streamlit as st
from frontend import citizen_module, officer_module

st.set_page_config(page_title="ZANT - System ZUS", layout="wide")

# Zmiana koloru paska bocznego (sidebar)
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #009c44;
        }
        [data-testid="stSidebar"] * {
            color: #ffffff !important;
            font-weight: bold !important;
        }
        [data-testid="stSidebar"] .stButton button {
            width: 100%;
            aspect-ratio: 1 / 1;
            color: #ffffff !important;
            border: 2px solid #ffffff;
            background-color: #007a33;
            font-weight: bold;
            font-size: 36px !important;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            white-space: pre-wrap;
            line-height: 1.5;
        }
        [data-testid="stSidebar"] .stButton button p {
            font-size: 36px !important;
        }
        [data-testid="stSidebar"] .stButton button:hover {
            background-color: #004d22;
            color: #ffffff !important;
            border-color: #ffffff;
        }
        [data-testid="stSidebar"] h1 {
            font-size: 40px !important;
            text-align: center;
        }
        /* Styl dla wszystkich przycisków (w tym w głównej części) */
        .stButton button {
            background-color: #009c44;
            color: #ffffff !important;
            border: none;
        }
        .stButton button:hover {
            background-color: #007a33;
            color: #ffffff !important;
        }
    </style>
""", unsafe_allow_html=True)

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
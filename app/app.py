import streamlit as st
import os

from pages.home import render_home_page
from pages.criar_audiencia import render_criar_audiencia_page
from pages.minhas_audiencias import render_minhas_audiencias_page
from pages.insights import render_insights_page

MAIN_DATA_TABLE = os.getenv("MAIN_DATA_TABLE")

st.set_page_config(
    page_title="BRB Audience Builder",
    page_icon="https://raw.githubusercontent.com/lcpassuncao/poc_banco/main/images/logomarca_brb.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS - BRB Branding: Black sidebar, Red buttons (#C3281E), Montserrat font
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

/* Global font */
html, body, .stApp, .stApp * {
    font-family: 'Montserrat', sans-serif !important;
}

/* Clean white background */
.stApp {
    background: white;
}

/* Adjust main content */
.main .block-container {
    margin-top: 2rem;
}

/* ==================== BLACK SIDEBAR ==================== */
.stSidebar, .stSidebar > div, .stSidebar .block-container {
    background-color: #000000 !important;
}

/* All text elements in sidebar white */
.stSidebar * {
    color: white !important;
}

.stSidebar .stMarkdown,
.stSidebar .stMarkdown *,
.stSidebar .markdown-text-container,
.stSidebar .markdown-text-container * {
    color: white !important;
}

.stSidebar h1, .stSidebar h2, .stSidebar h3, .stSidebar h4, .stSidebar h5, .stSidebar h6 {
    color: white !important;
}

.stSidebar p, .stSidebar span, .stSidebar div {
    color: white !important;
}

.stSidebar label {
    color: white !important;
}

.stSidebar svg, .stSidebar svg path {
    fill: white !important;
    stroke: white !important;
}

.stSidebar .stButton button {
    color: white !important;
    border-color: white !important;
}

.stSidebar .stTextInput input {
    color: white !important;
    border-color: rgba(255,255,255,0.3) !important;
}

/* Expander in sidebar */
.stSidebar .stExpander {
    background-color: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
}

.stSidebar [data-testid="stExpander"] div[data-testid="stExpanderDetails"] p,
.stSidebar [data-testid="stExpander"] div[data-testid="stExpanderDetails"] li,
.stSidebar [data-testid="stExpander"] div[data-testid="stExpanderDetails"] code,
.stSidebar [data-testid="stExpander"] div[data-testid="stExpanderDetails"] span {
    color: black !important;
}

/* Hide sidebar collapse button */
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Force sidebar always expanded */
section[data-testid="stSidebar"] {
    width: 21rem !important;
    min-width: 21rem !important;
    max-width: 21rem !important;
    transform: none !important;
    transition: none !important;
    margin-top: 0rem !important;
    z-index: 999;
    top: 0 !important;
}

section[data-testid="stSidebar"] > div {
    width: 21rem !important;
    transform: none !important;
    transition: none !important;
    padding-top: 1rem !important;
}

/* Logo container fixed at top of sidebar */
.brb-logo-container {
    position: fixed;
    top: 50px;
    left: 0;
    width: 21rem;
    background-color: #000000;
    z-index: 10000;
    padding: 1.2rem 1.5rem;
    box-sizing: border-box;
}

.brb-logo-container img {
    width: 200px;
}

/* Push sidebar content below fixed logo */
section[data-testid="stSidebar"] > div > div {
    margin-top: 5rem !important;
}

/* ==================== RED NAVIGATION BUTTONS ==================== */
div[data-testid="column"] > div > div > button {
    background-color: #C3281E !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.75rem 1.5rem !important;
    margin: 0.25rem !important;
    font-weight: 600 !important;
    font-family: 'Montserrat', sans-serif !important;
    letter-spacing: 1px !important;
    width: 100% !important;
    transition: background-color 0.2s ease !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

div[data-testid="column"] > div > div > button:hover {
    background-color: #A02018 !important;
    opacity: 1 !important;
}

div[data-testid="column"] > div > div > button[kind="primaryFormSubmit"],
div[data-testid="column"] > div > div > button[kind="primary"] {
    background-color: #C3281E !important;
    opacity: 1 !important;
    box-shadow: 0 2px 6px rgba(195,40,30,0.4) !important;
    font-weight: 700 !important;
}

/* ==================== PRIMARY BUTTONS (Calcular, Salvar, etc.) ==================== */
.stButton > button[kind="primary"],
button[kind="primaryFormSubmit"] {
    background-color: #C3281E !important;
    color: white !important;
    border: none !important;
    border-radius: 50px !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
}

.stButton > button[kind="primary"]:hover,
button[kind="primaryFormSubmit"]:hover {
    background-color: #A02018 !important;
}

/* Download button */
.stDownloadButton > button {
    background-color: #C3281E !important;
    border-color: #C3281E !important;
    color: white !important;
    border-radius: 50px !important;
}

/* ==================== FORM ELEMENTS ==================== */
.stSelectbox > div > div {
    border-color: #ddd !important;
}

.stSlider > div > div > div > div {
    background-color: #C3281E !important;
}

/* ==================== MISC ==================== */
.insights-title {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 1rem;
}

.demographic-section {
    background-color: white;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# --- Page routing ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "HOME"

# --- Sidebar with BRB Logo fixed at top ---
import base64, pathlib

logo_bytes = pathlib.Path("images/logomarca_brb.png").read_bytes()
logo_b64 = base64.b64encode(logo_bytes).decode()

st.sidebar.markdown(
    f"""
    <div class="brb-logo-container">
        <img src="data:image/png;base64,{logo_b64}" alt="BRB">
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")

# Load connection and date
from utils.databricks_utils import get_db_connection, get_last_modified_date

formatted_date = "Indisponivel"
conn = get_db_connection()

try:
    if conn:
        max_date = get_last_modified_date(conn, MAIN_DATA_TABLE)
        if hasattr(max_date, "strftime"):
            formatted_date = max_date.strftime("%d/%m/%Y")
        else:
            formatted_date = str(max_date)
except Exception as e:
    st.sidebar.warning("Nao foi possivel carregar a data de atualizacao.")

st.sidebar.markdown(f"**Base atualizada em:** {formatted_date}")

# --- Navigation bar ---
nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)

with nav_col1:
    if st.button("HOME", key="nav_home", type="primary" if st.session_state.current_page == "HOME" else "secondary"):
        st.session_state.current_page = "HOME"
        st.rerun()

with nav_col2:
    if st.button("CRIAR AUDIENCIA", key="nav_create", type="primary" if st.session_state.current_page == "CRIAR AUDIENCIA" else "secondary"):
        st.session_state.current_page = "CRIAR AUDIENCIA"
        st.rerun()

with nav_col3:
    if st.button("MINHAS AUDIENCIAS", key="nav_mine", type="primary" if st.session_state.current_page == "MINHAS AUDIENCIAS" else "secondary"):
        st.session_state.current_page = "MINHAS AUDIENCIAS"
        st.rerun()

with nav_col4:
    if st.button("INSIGHTS", key="nav_insights", type="primary" if st.session_state.current_page == "INSIGHTS" else "secondary"):
        st.session_state.current_page = "INSIGHTS"
        st.rerun()

# --- Page Content ---
if st.session_state.current_page == "HOME":
    render_home_page()
elif st.session_state.current_page == "CRIAR AUDIENCIA":
    render_criar_audiencia_page()
elif st.session_state.current_page == "MINHAS AUDIENCIAS":
    render_minhas_audiencias_page()
elif st.session_state.current_page == "INSIGHTS":
    render_insights_page()

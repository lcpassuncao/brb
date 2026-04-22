import streamlit as st
import os

MAIN_DATA_TABLE = os.getenv("MAIN_DATA_TABLE")
SAVED_AUDIENCE_TABLE = os.getenv("SAVED_AUDIENCE_TABLE")


def render_home_page():
    """Render the HOME page with BRB branding."""

    # Hero section - BRB Red + Black gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #C3281E 0%, #000000 100%); color: white; padding: 3rem 2rem 6rem 2rem; margin: -1rem -2rem 0rem -2rem; border-radius: 16px; position: relative;">
        <h1 style="color: white; margin-bottom: 1rem; font-size: 2.5rem; font-family: 'Montserrat', sans-serif; font-weight: 700; letter-spacing: 2px;">
            Bem-vindo(a) ao Audience Builder!
        </h1>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.1rem; line-height: 1.6; margin-bottom: 2rem; max-width: 700px; font-family: 'Montserrat', sans-serif;">
            O Audience Builder e uma ferramenta para gestores de marketing do BRB,
            permitindo criar e segmentar publicos para campanhas e acoes de marketing
            de forma pratica e rapida, usando dados cadastrais e comportamentais dos clientes.
        </p>
    </div>
    """, unsafe_allow_html=True)

    from utils.databricks_utils import get_db_connection, get_last_modified_date, run_query

    formatted_date = "Indisponivel"
    audience_count = 0
    total_leads = 0
    conn = get_db_connection()

    try:
        if conn:
            with st.spinner("Carregando dados..."):
                max_date = get_last_modified_date(conn, MAIN_DATA_TABLE)
                if hasattr(max_date, "strftime"):
                    formatted_date = max_date.strftime("%d/%m/%Y")
                else:
                    formatted_date = str(max_date)

                # Total leads
                df_leads = run_query(conn, f"SELECT COUNT(*) AS total FROM {MAIN_DATA_TABLE}")
                if not df_leads.empty:
                    total_leads = int(df_leads.iloc[0, 0])

                # Total saved audiences
                if SAVED_AUDIENCE_TABLE:
                    try:
                        df_aud = run_query(conn, f"SELECT COUNT(*) AS total FROM {SAVED_AUDIENCE_TABLE}")
                        if not df_aud.empty:
                            audience_count = int(df_aud.iloc[0, 0])
                    except Exception:
                        audience_count = 0
    except Exception as e:
        print(f"Error loading home data: {e}")

    # Metric cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; margin-top: -3rem; position: relative; z-index: 10; height: 60px; display: flex; align-items: center; justify-content: center;">
            <h3 style="color: #666; margin: 0; font-size: 0.95rem; font-weight: normal;">Ultima atualizacao</h3>
        </div>
        <div style="background-color: #f5f5f5; padding: 2rem 1.5rem; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; height: 120px; display: flex; align-items: center; justify-content: center;">
            <h2 style="color: #333; margin: 0; font-size: 2.5rem; font-weight: bold;">{formatted_date}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; margin-top: -3rem; position: relative; z-index: 10; height: 60px; display: flex; align-items: center; justify-content: center;">
            <h3 style="color: #666; margin: 0; font-size: 0.95rem; font-weight: normal;">Total de Leads</h3>
        </div>
        <div style="background-color: #f5f5f5; padding: 2rem 1.5rem; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; height: 120px; display: flex; align-items: center; justify-content: center;">
            <h2 style="color: #C3281E; margin: 0; font-size: 2.5rem; font-weight: bold;">{total_leads:,}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background-color: white; padding: 1.5rem; border-radius: 8px 8px 0 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; margin-top: -3rem; position: relative; z-index: 10; height: 60px; display: flex; align-items: center; justify-content: center;">
            <h3 style="color: #666; margin: 0; font-size: 0.95rem; font-weight: normal;">Audiencias salvas</h3>
        </div>
        <div style="background-color: #f5f5f5; padding: 2rem 1.5rem; border-radius: 0 0 8px 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); text-align: center; height: 120px; display: flex; align-items: center; justify-content: center;">
            <h2 style="color: #333; margin: 0; font-size: 2.5rem; font-weight: bold;">{audience_count}</h2>
        </div>
        """, unsafe_allow_html=True)

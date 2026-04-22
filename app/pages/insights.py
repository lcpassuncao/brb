import streamlit as st
import pandas as pd
import os
import re
import plotly.express as px
from utils.databricks_utils import get_db_connection, run_query, get_saved_audiences

SAVED_AUDIENCE_TABLE = os.getenv("SAVED_AUDIENCE_TABLE")
MAIN_DATA_TABLE = os.getenv("MAIN_DATA_TABLE")


def ensure_quotes_in_filter(filter_str):
    """Ensure proper quoting in SQL filter strings."""
    if not filter_str:
        return ""
    # For = Value (only if not already quoted or number)
    filter_str = re.sub(
        r"([=]\s*)([^\s')]+)",
        lambda m: f"{m.group(1)}'{m.group(2).strip()}'"
        if not m.group(2).startswith("'")
        and not m.group(2).replace(".", "", 1).isdigit()
        else m.group(0),
        filter_str,
    )
    return filter_str


@st.cache_data(ttl=300)
def get_audience_data_filtered(_conn, filter_sql: str):
    where_clause = filter_sql if filter_sql else "1=1"
    query = f"SELECT * FROM {MAIN_DATA_TABLE} WHERE {where_clause}"
    df = run_query(_conn, query)
    return df, query


@st.cache_data(ttl=300)
def get_chart_data_filtered(_conn, filter_sql: str):
    where_clause = filter_sql if filter_sql else "1=1"
    query = f"""
    SELECT
        tem_cartao_credito,
        tem_seguro,
        tem_capitalizacao,
        bandeira_cartao,
        nome_cartao_credito,
        COUNT(*) as total
    FROM {MAIN_DATA_TABLE}
    WHERE {where_clause}
    GROUP BY tem_cartao_credito, tem_seguro, tem_capitalizacao, bandeira_cartao, nome_cartao_credito
    """
    return run_query(_conn, query)


def render_insights_page():
    st.title("Insights da Audiencia")

    conn = get_db_connection()
    if not conn:
        st.error("Falha na conexao com Databricks.")
        st.stop()

    with st.spinner("Carregando audiencias salvas..."):
        audiences_df = get_saved_audiences(conn)

    if audiences_df.empty:
        st.warning("Nenhuma audiencia salva. Crie uma na pagina 'CRIAR AUDIENCIA'.")
        st.stop()

    if st.button("Recarregar Audiencias"):
        st.cache_data.clear()

    audience_names = ["Selecione uma Audiencia"] + audiences_df[
        "audience_name"
    ].tolist()
    selected_name = st.selectbox(
        "**Selecione a Audiencia para Analise:**",
        audience_names,
        index=0,
        key="selected_audience",
    )

    audience_data_df = pd.DataFrame()
    chart_data_df = pd.DataFrame()
    filter_corrected = ""

    if selected_name != "Selecione uma Audiencia":
        selected_row = audiences_df[audiences_df["audience_name"] == selected_name]
        if not selected_row.empty:
            raw_filter = selected_row["query_filter"].iloc[0]
            filter_corrected = ensure_quotes_in_filter(raw_filter)

            with st.spinner(f"Carregando dados para '{selected_name}'..."):
                chart_data_df = get_chart_data_filtered(conn, filter_corrected)

    # Download button
    col1, col2 = st.columns([1.5, 6.5])
    with col1:
        disable_download = (
            selected_name == "Selecione uma Audiencia" or filter_corrected == ""
        )
        if st.button(
            "Download Dados (CSV)",
            disabled=disable_download,
            type="primary",
            use_container_width=True,
            key=f"dl_btn_{selected_name}",
        ):
            with st.spinner("Gerando CSV..."):
                audience_data_df, _ = get_audience_data_filtered(conn, filter_corrected)
                if audience_data_df is not None and not audience_data_df.empty:
                    csv_data = audience_data_df.to_csv(index=False).encode("utf-8")
                    safe_name = "".join(
                        c if c.isalnum() else "_" for c in selected_name
                    )
                    file_name = f"brb_audiencia_{safe_name}.csv"
                    st.download_button(
                        label="Clique aqui para baixar",
                        data=csv_data,
                        file_name=file_name,
                        mime="text/csv",
                        key=f"real_dl_{selected_name}",
                    )
                else:
                    st.error("Nenhum dado para exportar.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Show filter
    if filter_corrected:
        st.markdown("##### Filtro Aplicado:")
        st.code(filter_corrected, language="sql")

    st.markdown("---")

    # KPIs
    st.markdown("### Metricas Principais")
    total_customers = (
        int(chart_data_df["total"].sum())
        if chart_data_df is not None and "total" in chart_data_df.columns
        else 0
    )

    kpi_col1, kpi_col2 = st.columns(2)
    with kpi_col1:
        st.markdown(
            f"""
        <div style="background-color: #f8f8f8; padding: 1.5rem; border-radius: 8px; text-align: center; border-left: 4px solid #C3281E;">
            <h4 style="color: #666; margin: 0 0 0.5rem 0;">Clientes na Audiencia</h4>
            <h2 style="color: #C3281E; margin: 0; font-size: 2.5rem;">{total_customers:,}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Distribuicao por Dimensao")

    if chart_data_df is not None and not chart_data_df.empty:
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            # Cartao de credito
            cc_data = (
                chart_data_df.groupby("tem_cartao_credito")["total"]
                .sum()
                .reset_index()
            )
            fig_cc = px.pie(
                cc_data,
                values="total",
                names="tem_cartao_credito",
                title="Cartao de Credito",
                color_discrete_sequence=["#C3281E", "#333333", "#888888"],
            )
            st.plotly_chart(fig_cc, use_container_width=True)

        with chart_col2:
            # Seguro
            seg_data = (
                chart_data_df.groupby("tem_seguro")["total"].sum().reset_index()
            )
            fig_seg = px.pie(
                seg_data,
                values="total",
                names="tem_seguro",
                title="Seguro",
                color_discrete_sequence=["#C3281E", "#333333", "#888888"],
            )
            st.plotly_chart(fig_seg, use_container_width=True)

        chart_col3, chart_col4 = st.columns(2)

        with chart_col3:
            # Capitalizacao
            cap_data = (
                chart_data_df.groupby("tem_capitalizacao")["total"]
                .sum()
                .reset_index()
            )
            fig_cap = px.pie(
                cap_data,
                values="total",
                names="tem_capitalizacao",
                title="Capitalizacao",
                color_discrete_sequence=["#C3281E", "#333333", "#888888"],
            )
            st.plotly_chart(fig_cap, use_container_width=True)

        with chart_col4:
            # Bandeira
            band_data = chart_data_df[
                chart_data_df["bandeira_cartao"].notna()
            ]
            if not band_data.empty:
                band_agg = (
                    band_data.groupby("bandeira_cartao")["total"]
                    .sum()
                    .reset_index()
                )
                fig_band = px.bar(
                    band_agg,
                    x="bandeira_cartao",
                    y="total",
                    text_auto=True,
                    title="Bandeira do Cartao",
                    labels={"bandeira_cartao": "Bandeira", "total": "Total"},
                    color_discrete_sequence=["#C3281E"],
                )
                st.plotly_chart(fig_band, use_container_width=True)
            else:
                st.info("Sem dados de bandeira.")

        # Nome do cartao
        nome_cc_data = chart_data_df[
            chart_data_df["nome_cartao_credito"].notna()
        ]
        if not nome_cc_data.empty:
            nome_agg = (
                nome_cc_data.groupby("nome_cartao_credito")["total"]
                .sum()
                .reset_index()
                .sort_values("total", ascending=True)
            )
            fig_nome = px.bar(
                nome_agg,
                x="total",
                y="nome_cartao_credito",
                orientation="h",
                text_auto=True,
                title="Nome do Cartao de Credito",
                labels={"nome_cartao_credito": "Cartao", "total": "Total"},
                color_discrete_sequence=["#C3281E"],
            )
            st.plotly_chart(fig_nome, use_container_width=True)
    else:
        if selected_name != "Selecione uma Audiencia":
            st.info("Nenhum dado disponivel para graficos.")
        else:
            st.info("Selecione uma audiencia para visualizar os insights.")

import streamlit as st
import os
from utils.databricks_utils import get_db_connection, run_query, execute_query

SAVED_AUDIENCE_TABLE = os.getenv("SAVED_AUDIENCE_TABLE")


def render_minhas_audiencias_page():
    """Renders the MINHAS AUDIENCIAS page."""

    st.markdown("# Minhas Audiencias")
    st.markdown("Veja e gerencie as audiencias que voce salvou.")

    conn = get_db_connection()
    if not conn:
        st.error("Nao foi possivel conectar ao Databricks.")
        st.stop()

    def refresh_data():
        st.cache_data.clear()

    def delete_audience(audience_name_to_delete: str):
        safe_name = audience_name_to_delete.replace("'", "''")
        delete_sql = f"DELETE FROM {SAVED_AUDIENCE_TABLE} WHERE audience_name = '{safe_name}'"
        success = execute_query(conn, delete_sql)
        if success:
            st.toast(f"Audiencia '{audience_name_to_delete}' deletada!")
            refresh_data()
        else:
            st.error(f"Falha ao deletar '{audience_name_to_delete}'.")

    st.button(
        "Atualizar Lista",
        on_click=refresh_data,
        help="Recarregar a lista de audiencias.",
    )

    query = f"SELECT audience_name, query_filter, created_at FROM {SAVED_AUDIENCE_TABLE} ORDER BY created_at DESC"

    with st.spinner("Carregando audiencias salvas..."):
        audiences_df = run_query(conn, query)

    if not audiences_df.empty:
        st.markdown(f"**Total de audiencias salvas: {len(audiences_df)}**")

        for index, row in audiences_df.iterrows():
            audience_name = row["audience_name"]
            query_filter = row["query_filter"]
            created_at = row["created_at"]
            if hasattr(created_at, "strftime"):
                created_at = created_at.strftime("%d/%m/%Y %H:%M")
            else:
                created_at = str(created_at)

            with st.expander(f"{audience_name} (Salvo em: {created_at})"):
                st.markdown("##### Filtros da Query:")
                st.code(query_filter, language="sql")
                st.markdown("---")
                st.button(
                    "Deletar Audiencia",
                    key=f"delete_{audience_name}",
                    help=f"Deletar permanentemente '{audience_name}'",
                    on_click=delete_audience,
                    args=(audience_name,),
                )
    else:
        st.info(
            "Nenhuma audiencia foi salva ainda. Crie uma na pagina 'CRIAR AUDIENCIA'."
        )

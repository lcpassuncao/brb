import streamlit as st
import pandas as pd
import os
from databricks import sql
from databricks.sdk.core import Config

MAIN_DATA_TABLE = os.getenv("MAIN_DATA_TABLE")
SAVED_AUDIENCE_TABLE = os.getenv("SAVED_AUDIENCE_TABLE")


@st.cache_resource
def get_db_connection():
    """Creates and caches a Databricks SQL connection."""
    try:
        cfg = Config()
        connection = sql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{os.getenv('DATABRICKS_WAREHOUSE_ID')}",
            credentials_provider=lambda: cfg.authenticate,
        )
        print("Connection to Databricks successful.")
        return connection
    except Exception as e:
        st.error(f"Failed to connect to Databricks: {e}")
        return None


@st.cache_data(ttl=600)
def run_query(_conn, query: str) -> pd.DataFrame:
    """Executes a SQL query and returns a Pandas DataFrame."""
    if _conn is None:
        st.warning("Cannot run query: No Databricks connection available.")
        return pd.DataFrame()
    try:
        with _conn.cursor() as cursor:
            cursor.execute(query)
            df = cursor.fetchall_arrow().to_pandas()
            return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()


def execute_query(_conn, query: str) -> bool:
    """Executes a command (INSERT, UPDATE, DELETE) that doesn't return data."""
    if _conn is None:
        st.error("Cannot execute command: No Databricks connection available.")
        return False
    try:
        with _conn.cursor() as cursor:
            cursor.execute(query)
        return True
    except Exception as e:
        st.error(f"Command execution failed: {e}")
        return False


def get_last_modified_date(_conn, table_name: str):
    """Gets the last modified date of a Delta Table."""
    query = f"""
    SELECT DATE(timestamp) AS lastModified
    FROM (DESCRIBE HISTORY {table_name})
    ORDER BY version DESC
    LIMIT 1;
    """
    df = run_query(_conn, query)
    if not df.empty:
        return df["lastModified"].iloc[0]
    return "N/A"


def get_filter_options(_conn):
    """Gets available filter values by querying distinct values from the leads table."""
    options = {}
    table = MAIN_DATA_TABLE

    filter_queries = {
        "Cartao de Credito": f"SELECT DISTINCT tem_cartao_credito FROM {table} WHERE tem_cartao_credito IS NOT NULL ORDER BY 1",
        "Seguro": f"SELECT DISTINCT tem_seguro FROM {table} WHERE tem_seguro IS NOT NULL ORDER BY 1",
        "Capitalizacao": f"SELECT DISTINCT tem_capitalizacao FROM {table} WHERE tem_capitalizacao IS NOT NULL ORDER BY 1",
        "Bandeira": f"SELECT DISTINCT bandeira_cartao FROM {table} WHERE bandeira_cartao IS NOT NULL ORDER BY 1",
        "Nome Cartao": f"SELECT DISTINCT nome_cartao_credito FROM {table} WHERE nome_cartao_credito IS NOT NULL ORDER BY 1",
    }

    for name, query in filter_queries.items():
        df = run_query(_conn, query)
        if not df.empty:
            options[name] = [str(v) for v in df.iloc[:, 0].tolist() if v is not None]
        else:
            options[name] = []

    return options


def get_saved_audiences(_conn):
    """Fetches the list of saved audience names and their filters."""
    query = f"SELECT audience_name, query_filter, created_at FROM {SAVED_AUDIENCE_TABLE} ORDER BY created_at DESC"
    return run_query(_conn, query)

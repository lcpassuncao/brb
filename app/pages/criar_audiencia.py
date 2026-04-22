import streamlit as st
import os
from utils.databricks_utils import get_db_connection, execute_query, run_query, get_filter_options

MAIN_DATA_TABLE = os.getenv("MAIN_DATA_TABLE")
SAVED_AUDIENCE_TABLE = os.getenv("SAVED_AUDIENCE_TABLE")

# Field to Column Mapping for BRB cadastro_leads
field_to_column_map = {
    "Cartao de Credito": "tem_cartao_credito",
    "Seguro": "tem_seguro",
    "Capitalizacao": "tem_capitalizacao",
    "Bandeira": "bandeira_cartao",
    "Nome Cartao": "nome_cartao_credito",
}

# Numeric range fields (handled differently)
RANGE_FIELDS = {
    "Saldo da Conta": "saldo_da_conta",
    "Dias sem Movimentacao": "qto_tempo_sem_movimentar_conta",
}


def render_criar_audiencia_page():
    """Renders the CRIAR AUDIENCIA page with dynamic filters."""

    if "show_volumetria" not in st.session_state:
        st.session_state.show_volumetria = False
    if "volumetria_count" not in st.session_state:
        st.session_state.volumetria_count = 0
    if "condition_rows" not in st.session_state:
        st.session_state.condition_rows = {
            0: {"field": "Selecione um campo", "value": "Selecione um valor"}
        }
    if "next_row_id" not in st.session_state:
        st.session_state.next_row_id = 1
    if "saldo_range" not in st.session_state:
        st.session_state.saldo_range = (0.0, 250000.0)
    if "dias_range" not in st.session_state:
        st.session_state.dias_range = (0, 150)

    conn = get_db_connection()
    if not conn:
        st.error("Falha na conexao com Databricks.")
        st.stop()

    with st.spinner("Carregando opcoes de filtro..."):
        filter_options_from_db = get_filter_options(conn)

    if not filter_options_from_db:
        st.warning("Nao foi possivel carregar as opcoes de filtro.")
        filter_options_from_db = {}

    # --- Sidebar Datapoints ---
    with st.sidebar:
        st.markdown("### Datapoints")
        st.markdown("*Segmentos e caracteristicas disponiveis.*")
        sorted_filter_names = sorted(filter_options_from_db.keys())
        for filter_name in sorted_filter_names:
            options_list = filter_options_from_db.get(filter_name, [])
            if options_list:
                with st.expander(filter_name):
                    markdown_content = "\n".join(
                        [f"- `{option}`" for option in options_list]
                    )
                    st.markdown(markdown_content)

    # --- Build SQL clause ---
    def build_filter_sql_clause():
        query_parts = []
        valid_conditions = 0

        # Categorical conditions
        for i, (row_id, row_data) in enumerate(
            st.session_state.condition_rows.items()
        ):
            selected_field = row_data.get("field")
            selected_value = row_data.get("value")

            if (
                selected_field
                and selected_field != "Selecione um campo"
                and selected_value
                and selected_value != "Selecione um valor"
            ):
                db_column = field_to_column_map.get(selected_field)
                if not db_column:
                    continue

                sql_value_escaped = selected_value.replace("'", "''")
                condition_sql = f"`{db_column}` = '{sql_value_escaped}'"

                if valid_conditions == 0:
                    query_parts.append(condition_sql)
                else:
                    query_parts.append(f"AND {condition_sql}")
                valid_conditions += 1

        # Range conditions
        saldo_min, saldo_max = st.session_state.saldo_range
        if saldo_min > 0 or saldo_max < 250000:
            cond = f"`saldo_da_conta` BETWEEN {saldo_min} AND {saldo_max}"
            if valid_conditions == 0:
                query_parts.append(cond)
            else:
                query_parts.append(f"AND {cond}")
            valid_conditions += 1

        dias_min, dias_max = st.session_state.dias_range
        if dias_min > 0 or dias_max < 150:
            cond = f"`qto_tempo_sem_movimentar_conta` BETWEEN {dias_min} AND {dias_max}"
            if valid_conditions == 0:
                query_parts.append(cond)
            else:
                query_parts.append(f"AND {cond}")
            valid_conditions += 1

        return "\n".join(query_parts), valid_conditions

    # --- Page UI ---
    st.markdown(
        '<h2 style="color: #333; margin-bottom: 2rem; font-family: Montserrat, sans-serif;">Query Builder</h2>',
        unsafe_allow_html=True,
    )

    st.markdown("**Nome da audiencia** *")
    audience_name = st.text_input(
        "Nome",
        placeholder="Digite o nome da audiencia",
        key="audience_name",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Range Filters ---
    st.markdown("##### Filtros por Faixa de Valor")
    range_col1, range_col2 = st.columns(2)

    with range_col1:
        saldo_range = st.slider(
            "Saldo da Conta (R$)",
            min_value=0.0,
            max_value=250000.0,
            value=st.session_state.saldo_range,
            step=1000.0,
            format="R$ %.0f",
            key="slider_saldo",
        )
        st.session_state.saldo_range = saldo_range

    with range_col2:
        dias_range = st.slider(
            "Dias sem Movimentacao",
            min_value=0,
            max_value=150,
            value=st.session_state.dias_range,
            step=1,
            key="slider_dias",
        )
        st.session_state.dias_range = dias_range

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("##### Filtros Categoricos")

    col1, col2 = st.columns([1, 8])
    with col1:

        def add_condition():
            new_id = st.session_state.next_row_id
            st.session_state.condition_rows[new_id] = {
                "field": "Selecione um campo",
                "value": "Selecione um valor",
            }
            st.session_state.next_row_id += 1

        st.button("+ Nova condicao", type="secondary", on_click=add_condition)

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Dynamic Filter Rows ---
    row_ids_to_render = list(st.session_state.condition_rows.keys())
    for i, row_id in enumerate(row_ids_to_render):
        if row_id not in st.session_state.condition_rows:
            continue
        logic_key = f"logic_{row_id}"
        field_key = f"field_{row_id}"
        value_key = f"value_{row_id}"
        delete_key = f"del_{row_id}"

        cond_col1, cond_col3, cond_col5, cond_col6 = st.columns([0.5, 1.5, 1.5, 0.3])

        with cond_col1:
            if i > 0:
                st.selectbox("Logic", ["E"], key=logic_key, label_visibility="collapsed")
            else:
                st.write("")

        with cond_col3:
            field_options = ["Selecione um campo"] + sorted(
                list(field_to_column_map.keys())
            )

            def field_changed_callback(r_id):
                st.session_state.condition_rows[r_id]["value"] = "Selecione um valor"

            current_field = st.session_state.condition_rows[row_id].get(
                "field", "Selecione um campo"
            )
            try:
                field_index = field_options.index(current_field)
            except ValueError:
                field_index = 0

            st.selectbox(
                "Field",
                field_options,
                key=field_key,
                label_visibility="collapsed",
                index=field_index,
                on_change=field_changed_callback,
                args=(row_id,),
            )
            st.session_state.condition_rows[row_id]["field"] = st.session_state[
                field_key
            ]

        with cond_col5:
            value_options = ["Selecione um valor"]
            is_value_disabled = True
            current_value_index = 0
            stored_field = st.session_state.condition_rows[row_id].get("field")

            if stored_field and stored_field != "Selecione um campo":
                current_values = filter_options_from_db.get(stored_field, [])
                if current_values:
                    value_options.extend(current_values)
                    is_value_disabled = False
                    stored_value = st.session_state.condition_rows[row_id].get(
                        "value", "Selecione um valor"
                    )
                    if stored_value in value_options:
                        try:
                            current_value_index = value_options.index(stored_value)
                        except ValueError:
                            current_value_index = 0
                    else:
                        current_value_index = 0
                        st.session_state.condition_rows[row_id][
                            "value"
                        ] = "Selecione um valor"

            def value_changed_callback(r_id, key):
                st.session_state.condition_rows[r_id]["value"] = st.session_state[key]

            st.selectbox(
                "Value",
                value_options,
                key=value_key,
                label_visibility="collapsed",
                disabled=is_value_disabled,
                index=current_value_index,
                on_change=value_changed_callback,
                args=(row_id, value_key),
            )

        with cond_col6:
            if len(st.session_state.condition_rows) > 1:

                def delete_condition(r_id):
                    if r_id in st.session_state.condition_rows:
                        del st.session_state.condition_rows[r_id]
                    for k in [f"logic_{r_id}", f"field_{r_id}", f"value_{r_id}"]:
                        if k in st.session_state:
                            del st.session_state[k]

                st.button(
                    "X",
                    key=delete_key,
                    help="Deletar",
                    on_click=delete_condition,
                    args=(row_id,),
                )

        if i < len(row_ids_to_render) - 1:
            st.empty()

    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Volumetria ---
    if st.session_state.show_volumetria:
        st.markdown("<br>", unsafe_allow_html=True)
        calculated_count = st.session_state.get("volumetria_count", 0)
        st.markdown(
            f"""
        <div style="border-top: 1px solid #ddd; padding-top: 1rem; margin-top: 1rem;">
            <h3 style="color: #666;">Volumetria Calculada</h3>
            <p style="font-size: 2.5rem; font-weight: bold; color: #C3281E;">{calculated_count:,}
                <span style="font-size: 1rem; color: #666;">clientes</span>
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # --- Action Buttons ---
    st.markdown("<br>", unsafe_allow_html=True)
    action_col1, action_col2, action_col3 = st.columns([1.5, 1.5, 5])

    with action_col1:
        if st.button("Calcular volumetria", type="primary"):
            where_clause_str, valid_conditions = build_filter_sql_clause()
            if valid_conditions == 0:
                st.warning("Adicione ao menos uma condicao valida.")
                st.session_state.show_volumetria = False
                st.session_state.volumetria_count = 0
            else:
                count_query = f"SELECT COUNT(*) as total_count FROM {MAIN_DATA_TABLE} WHERE {where_clause_str}"
                with st.spinner("Calculando..."):
                    count_result_df = run_query(conn, count_query)
                if (
                    count_result_df is not None
                    and not count_result_df.empty
                    and "total_count" in count_result_df.columns
                ):
                    st.session_state.volumetria_count = count_result_df[
                        "total_count"
                    ].iloc[0]
                    st.session_state.show_volumetria = True
                else:
                    st.session_state.volumetria_count = 0
                    st.session_state.show_volumetria = False
                    st.error("Falha ao calcular.")
            st.rerun()

    with action_col2:
        if st.button("Salvar Grupo", type="primary", disabled=not audience_name):
            if not audience_name:
                st.error("Nome obrigatorio.")
            else:
                final_query_string, valid_conditions = build_filter_sql_clause()
                if valid_conditions == 0:
                    st.warning("Adicione ao menos uma condicao valida.")
                else:
                    safe_audience_name = audience_name.replace("'", "''")

                    # Ensure saved audiences table exists
                    execute_query(
                        conn,
                        f"""CREATE TABLE IF NOT EXISTS {SAVED_AUDIENCE_TABLE} (
                            id BIGINT GENERATED ALWAYS AS IDENTITY,
                            audience_name STRING NOT NULL,
                            query_filter STRING,
                            created_at TIMESTAMP
                        )""",
                    )

                    check_query = f"SELECT COUNT(*) as count FROM {SAVED_AUDIENCE_TABLE} WHERE audience_name = '{safe_audience_name}'"
                    with st.spinner("Verificando nome..."):
                        result_df = run_query(conn, check_query)

                    if result_df is None:
                        st.error("Erro ao verificar.")
                    elif (
                        not result_df.empty and result_df["count"].iloc[0] > 0
                    ):
                        st.warning(
                            f"Nome '{audience_name}' ja existe. Escolha outro nome."
                        )
                    else:
                        safe_filter = (
                            final_query_string.replace("'", "''").replace("\n", " ")
                        )
                        insert_sql = f"""INSERT INTO {SAVED_AUDIENCE_TABLE} (audience_name, query_filter, created_at)
                            VALUES ('{safe_audience_name}', '{safe_filter}', current_timestamp())"""

                        with st.spinner("Salvando..."):
                            success = execute_query(conn, insert_sql)
                        if success:
                            st.success(f"Grupo '{audience_name}' salvo com sucesso!")
                            st.cache_data.clear()
                        else:
                            st.error("Falha ao salvar.")

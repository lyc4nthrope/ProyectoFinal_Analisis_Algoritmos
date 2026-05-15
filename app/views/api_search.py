"""Vista de búsqueda en OpenAlex API."""

import pandas as pd
import requests
import streamlit as st

from app.loader import load_api_cache, save_api_cache
from src.data_sources import ApiParser


def render() -> None:
    st.header("🔍 Búsqueda en OpenAlex")
    st.markdown("Busque artículos académicos en OpenAlex y agréguelos al corpus.")

    query = st.text_input(
        "Término de búsqueda",
        placeholder="Ej: machine learning, generative AI...",
        key="api_query",
    )

    max_results = st.slider(
        "Cantidad de resultados",
        min_value=5,
        max_value=200,
        value=25,
        step=5,
        key="api_max_results",
    )

    if st.button("🔍 Buscar en OpenAlex", type="primary"):
        if not query or not query.strip():
            st.warning("⚠️ Ingrese un término de búsqueda.")
        else:
            cached = load_api_cache(query, max_results)

            if cached is not None:
                st.session_state.api_results = cached
                st.session_state.api_from_cache = True
                st.info("📦 Resultados cacheados")
            else:
                st.session_state.api_from_cache = False
                with st.spinner("Buscando en OpenAlex..."):
                    try:
                        parser = ApiParser()
                        results = parser.search(query, max_results)
                        st.session_state.api_results = results
                        save_api_cache(query, max_results, results)
                        st.info("🌐 Búsqueda en vivo")
                    except (ConnectionError, requests.HTTPError) as e:
                        st.error(f"❌ Error al conectar con OpenAlex: {e}")
                        st.session_state.api_results = None
                    except Exception as e:
                        st.error(f"❌ Error inesperado: {e}")
                        st.session_state.api_results = None

    st.divider()

    if "api_results" in st.session_state and st.session_state.api_results:
        results = st.session_state.api_results
        st.subheader(f"Resultados ({len(results)})")

        df = pd.DataFrame(results)
        display_cols = {
            "title": "Título",
            "authors": "Autores",
            "year": "Año",
            "doi": "DOI",
            "journal": "Revista/Fuente",
        }
        available_cols = {k: v for k, v in display_cols.items() if k in df.columns}
        df_display = df[list(available_cols.keys())].copy()
        df_display.columns = list(available_cols.values())

        todos = st.checkbox("✅ Seleccionar todos", key="api_select_all")
        df_display["seleccionar"] = todos

        edited_df = st.data_editor(
            df_display,
            column_config={
                "seleccionar": st.column_config.CheckboxColumn(
                    "Sel.",
                    default=False,
                    width="small",
                ),
            },
            column_order=["seleccionar"] + list(available_cols.values()),
            hide_index=True,
            use_container_width=True,
            height=400,
        )

        selected_count = sum(
            1 for _, row in edited_df.iterrows() if row.get("seleccionar", False)
        )
        if selected_count > 0:
            st.caption(f"{selected_count} resultado(s) seleccionado(s)")

        if selected_count > 0:
            if st.button("📥 Integrar al corpus", type="primary"):
                selected = [
                    row for _, row in edited_df.iterrows()
                    if row.get("seleccionar", False)
                ]
                if not selected:
                    st.warning("Seleccioná al menos un artículo para integrar.")
                else:
                    from pathlib import Path

                    processed_dir = Path("data/processed")
                    processed_dir.mkdir(parents=True, exist_ok=True)
                    path = processed_dir / "unified.csv"

                    result_df = pd.DataFrame(selected)
                    if "seleccionar" in result_df.columns:
                        result_df = result_df.drop(columns=["seleccionar"])
                    result_df.to_csv(path, index=False)

                    st.cache_data.clear()
                    st.success(f"✅ {len(selected)} artículo(s) integrado(s) al corpus. Recargá la vista Inicio para verlos.")

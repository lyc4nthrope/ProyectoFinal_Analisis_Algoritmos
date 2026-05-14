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
        max_value=50,
        value=25,
        step=5,
        key="api_max_results",
    )

    if st.button("🔍 Buscar en OpenAlex", type="primary"):
        if not query or not query.strip():
            st.warning("⚠️ Ingrese un término de búsqueda.")
        else:
            cached = load_api_cache(query)

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
                        save_api_cache(query, results)
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

        if "api_selection" not in st.session_state:
            st.session_state.api_selection = [False] * len(results)

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
                selected_indices = [
                    i for i, (_, row) in enumerate(edited_df.iterrows())
                    if row.get("seleccionar", False)
                ]
                selected_articles = [results[i] for i in selected_indices]

                with st.spinner("Integrando resultados al corpus..."):
                    try:
                        from src.processing.unifier import fetch_and_merge_api, run

                        fetch_and_merge_api(
                            articles=[],
                            direct_results=selected_articles,
                        )

                        run()
                        st.success(
                            f"✅ {len(selected_articles)} resultado(s) integrado(s) "
                            "al corpus exitosamente"
                        )
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error al integrar: {e}")

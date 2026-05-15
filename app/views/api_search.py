"""Vista de búsqueda en OpenAlex API."""

import pandas as pd
import requests
import streamlit as st


from src.data_sources import ApiParser


def render() -> None:
    st.header("🔍 Búsqueda en OpenAlex")
    st.markdown("Busque artículos académicos en OpenAlex y agréguelos al corpus.")

    query = st.text_input(
        "Término de búsqueda",
        placeholder="Ej: machine learning, generative AI...",
        key="api_query",
    )

    page_size = st.slider(
        "Resultados por página",
        min_value=5,
        max_value=50,
        value=25,
        step=5,
        key="api_page_size",
    )

    if st.button("🔍 Buscar en OpenAlex", type="primary"):
        if not query or not query.strip():
            st.warning("⚠️ Ingrese un término de búsqueda.")
        else:
            st.session_state.api_results = []
            st.session_state.api_total = 0
            st.session_state.api_cursor = None
            st.session_state.api_from_cache = False

            with st.spinner("Buscando en OpenAlex..."):
                try:
                    parser = ApiParser()
                    data = parser.fetch_page(query, "*", page_size)
                    st.session_state.api_results = data["results"]
                    st.session_state.api_total = data["total"]
                    st.session_state.api_cursor = data["next_cursor"]
                    st.info("🌐 Búsqueda en vivo" if data["results"] else "Sin resultados")
                except (ConnectionError, requests.HTTPError) as e:
                    st.error(f"❌ Error al conectar con OpenAlex: {e}")

    st.divider()

    if "api_results" in st.session_state and st.session_state.api_results:
        results = st.session_state.api_results
        total = st.session_state.api_total
        loaded = len(results)
        st.subheader(f"Mostrando {loaded} de {total} resultados")

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

        if st.session_state.api_cursor and loaded < total:
            if st.button("📄 Cargar más resultados"):
                with st.spinner("Cargando más resultados..."):
                    try:
                        parser = ApiParser()
                        data = parser.fetch_page(query, st.session_state.api_cursor, page_size)
                        new_results = data["results"]
                        if new_results:
                            st.session_state.api_results.extend(new_results)
                            st.session_state.api_cursor = data["next_cursor"]
                            st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al cargar más resultados: {e}")

        if selected_count > 0:
            if st.button("📥 Integrar al corpus", type="primary"):
                selected_mask = [
                    row.get("seleccionar", False) for _, row in edited_df.iterrows()
                ]
                selected = [r for r, sel in zip(results, selected_mask) if sel]
                if not selected:
                    st.warning("Seleccioná al menos un artículo para integrar.")
                else:
                    from pathlib import Path

                    processed_dir = Path("data/processed")
                    processed_dir.mkdir(parents=True, exist_ok=True)
                    path = processed_dir / "unified.csv"

                    nuevos = pd.DataFrame(selected)
                    if path.exists():
                        existentes = pd.read_csv(path)
                        corpus = pd.concat([existentes, nuevos], ignore_index=True)
                        corpus = corpus.drop_duplicates(subset="doi", keep="first")
                    else:
                        corpus = nuevos

                    corpus.to_csv(path, index=False)
                    total_corpus = len(corpus)

                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.success(f"✅ {len(selected)} artículo(s) integrado(s). Corpus actualizado: {total_corpus} artículo(s) en total.")

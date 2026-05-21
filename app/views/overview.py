import pandas as pd
import streamlit as st

from app.loader import load_corpus
from src.repositories import clear_corpus, load_duplicates_df


def render() -> None:
    st.title("Corpus bibliográfico")
    df = load_corpus()

    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Cargar archivos' o 'Búsqueda API' para agregar artículos al corpus.")
        return

    dups_df = load_duplicates_df()
    years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int)
    journals = df["journal"].replace("", pd.NA).dropna()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Artículos únicos", len(df))
    col2.metric("Duplicados eliminados", len(dups_df))
    col3.metric("Revistas distintas", int(journals.nunique()))
    col4.metric("Año más antiguo", int(years.min()) if len(years) > 0 else "—")
    col5.metric("Año más reciente", int(years.max()) if len(years) > 0 else "—")

    if not dups_df.empty:
        with st.expander(f"Ver registros duplicados eliminados ({len(dups_df)})"):
            dup_cols = [c for c in ["title", "authors", "year", "source"] if c in dups_df.columns]
            st.dataframe(dups_df[dup_cols], hide_index=True, width="stretch")

    st.subheader("Todos los artículos")
    cols = ["title", "authors", "journal", "year", "doi"]
    if "source" in df.columns:
        cols.append("source")
    display = df[cols].copy()
    labels = ["Título", "Autores", "Revista", "Año", "DOI"]
    if "source" in df.columns:
        labels.append("Base de datos")
    display.columns = labels
    st.dataframe(display, width="stretch", hide_index=True)

    st.divider()
    with st.expander("⚠️ Zona de peligro"):
        st.warning("Borrar el corpus elimina TODOS los artículos integrados. Esta acción no se puede deshacer.")
        if st.button("🗑️ Borrar corpus"):
            st.session_state.confirmar_borrado = True

        if st.session_state.get("confirmar_borrado"):
            col_si, col_no = st.columns(2)
            with col_si:
                if st.button("✅ Sí, borrar todo", type="primary"):
                    clear_corpus()
                    st.cache_data.clear()
                    st.cache_resource.clear()
                    st.session_state.confirmar_borrado = False
                    st.rerun()
            with col_no:
                if st.button("❌ Cancelar"):
                    st.session_state.confirmar_borrado = False
                    st.rerun()

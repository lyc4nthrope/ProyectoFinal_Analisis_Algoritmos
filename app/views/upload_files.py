"""Vista para cargar archivos BibTeX de bases de datos académicas."""

import pandas as pd
import streamlit as st

from src.config import RAW_DIR
from src.processing.unifier import run as run_unifier


_KNOWN_SOURCES = [
    "ACM Digital Library",
    "ScienceDirect",
    "SAGE Journals",
    "Academic Search Ultimate",
    "IEEE Xplore",
    "Otra fuente",
]


def _source_folder_name(label: str) -> str:
    return label.lower().replace(" ", "_")


def _show_current_sources() -> None:
    st.subheader("Fuentes cargadas actualmente")
    if not RAW_DIR.exists() or not any(RAW_DIR.iterdir()):
        st.info("No hay archivos en data/raw/ todavía.")
        return

    rows = []
    for source_dir in sorted(RAW_DIR.iterdir()):
        if not source_dir.is_dir():
            continue
        files = [f for f in source_dir.iterdir() if f.suffix.lower() in {".bib", ".bibtex"}]
        if files:
            for f in files:
                rows.append({"Fuente": source_dir.name, "Archivo": f.name})

    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else:
        st.info("No hay archivos .bib en data/raw/.")


def render() -> None:
    st.title("Cargar archivos bibliográficos")
    st.markdown(
        "Sube archivos `.bib` exportados desde bases de datos académicas "
        "(ACM, ScienceDirect, SAGE, etc.). El sistema los unificará y eliminará duplicados automáticamente."
    )

    _show_current_sources()

    st.divider()
    st.subheader("Subir nuevo archivo")

    source_label = st.selectbox("Base de datos origen", _KNOWN_SOURCES)
    if source_label == "Otra fuente":
        source_label = st.text_input("Nombre de la fuente", placeholder="Ej: Web of Science")

    uploaded = st.file_uploader(
        "Archivo BibTeX (.bib / .bibtex)",
        type=["bib", "bibtex"],
        accept_multiple_files=False,
    )

    if uploaded and st.button("📥 Cargar y procesar", type="primary"):
        if not source_label or not source_label.strip():
            st.warning("Ingresa el nombre de la fuente.")
            return

        folder_name = _source_folder_name(source_label)
        dest_dir = RAW_DIR / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / uploaded.name

        with open(dest_path, "wb") as f:
            f.write(uploaded.getbuffer())

        with st.spinner("Procesando y unificando corpus..."):
            try:
                run_unifier()
            except Exception as e:
                st.error(f"Error al procesar: {e}")
                return

        st.cache_data.clear()
        st.cache_resource.clear()

        from src.repositories import load_corpus_df, load_duplicates_df
        unified = load_corpus_df()
        dups = load_duplicates_df()

        st.success(
            f"Archivo procesado correctamente. "
            f"Corpus unificado: **{len(unified)} artículos únicos**, "
            f"**{len(dups)} duplicados** eliminados."
        )
        st.rerun()

"""Vista para cargar archivos BibTeX de bases de datos académicas."""

# Importa pandas para mostrar la tabla de archivos cargados
import pandas as pd
# Importa Streamlit para construir la interfaz de carga
import streamlit as st

# Importa la ruta donde se guardan los archivos BibTeX originales
from src.config import RAW_DIR
# Importa el pipeline que procesa y unifica los archivos BibTeX
from src.processing.unifier import run as run_unifier


# Lista de bases de datos académicas conocidas para el selector de fuente
_KNOWN_SOURCES = [
    "ACM Digital Library",
    "ScienceDirect",
    "SAGE Journals",
    "Academic Search Ultimate",
    "IEEE Xplore",
    "Otra fuente",
]


def _source_folder_name(label: str) -> str:
    # Convierte el nombre de la fuente a nombre de carpeta: minúsculas con guiones bajos
    return label.lower().replace(" ", "_")


def _show_current_sources() -> None:
    st.subheader("Fuentes cargadas actualmente")
    # Si no existe el directorio o está vacío, informa que no hay archivos
    if not RAW_DIR.exists() or not any(RAW_DIR.iterdir()):
        st.info("No hay archivos en data/raw/ todavía.")
        return

    rows = []
    # Recorre las subcarpetas de data/raw/ (cada una representa una fuente)
    for source_dir in sorted(RAW_DIR.iterdir()):
        if not source_dir.is_dir():
            continue
        # Filtra solo los archivos BibTeX dentro de la carpeta de la fuente
        files = [f for f in source_dir.iterdir() if f.suffix.lower() in {".bib", ".bibtex"}]
        if files:
            for f in files:
                rows.append({"Fuente": source_dir.name, "Archivo": f.name})

    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    else:
        st.info("No hay archivos .bib en data/raw/.")


def render() -> None:
    st.title("Cargar archivos bibliográficos")
    st.markdown(
        "Sube archivos `.bib` exportados desde bases de datos académicas "
        "(ACM, ScienceDirect, SAGE, etc.). El sistema los unificará y eliminará duplicados automáticamente."
    )

    # Muestra las fuentes que ya están cargadas en el sistema
    _show_current_sources()

    st.divider()
    st.subheader("Subir nuevo archivo")

    # Selector de base de datos origen del archivo BibTeX
    source_label = st.selectbox("Base de datos origen", _KNOWN_SOURCES)
    if source_label == "Otra fuente":
        # Permite escribir un nombre personalizado si elige "Otra fuente"
        source_label = st.text_input("Nombre de la fuente", placeholder="Ej: Web of Science")

    # Widget de carga de archivo: acepta solo .bib y .bibtex
    uploaded = st.file_uploader(
        "Archivo BibTeX (.bib / .bibtex)",
        type=["bib", "bibtex"],
        accept_multiple_files=False,
    )

    if uploaded and st.button("📥 Cargar y procesar", type="primary"):
        # Valida que se haya seleccionado una fuente antes de procesar
        if not source_label or not source_label.strip():
            st.warning("Ingresa el nombre de la fuente.")
            return

        # Determina el nombre de la carpeta de destino para el archivo
        folder_name = _source_folder_name(source_label)
        dest_dir = RAW_DIR / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / uploaded.name

        # Guarda el archivo subido en el disco
        with open(dest_path, "wb") as f:
            f.write(uploaded.getbuffer())

        # Ejecuta el pipeline de unificación y deduplicación
        with st.spinner("Procesando y unificando corpus..."):
            try:
                run_unifier()
            except Exception as e:
                st.error(f"Error al procesar: {e}")
                return

        # Limpia el caché de Streamlit para que la vista se actualice con los nuevos datos
        st.cache_data.clear()
        st.cache_resource.clear()

        # Lee los resultados del pipeline para mostrar el resumen al usuario
        from src.repositories import load_corpus_df, load_duplicates_df
        unified = load_corpus_df()
        dups = load_duplicates_df()

        # Muestra el resumen del resultado y recarga la vista
        st.success(
            f"Archivo procesado correctamente. "
            f"Corpus unificado: **{len(unified)} artículos únicos**, "
            f"**{len(dups)} duplicados** eliminados."
        )
        st.rerun()

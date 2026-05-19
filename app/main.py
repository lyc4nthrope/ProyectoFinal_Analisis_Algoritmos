import matplotlib
matplotlib.use("Agg")

import streamlit as st

st.set_page_config(
    page_title="Bibliometría GenAI",
    layout="wide",
)

from app.views import api_search, clustering, concepts, export_pdf, overview, similarity, upload_files, visualization

_PAGES = {
    "Inicio": overview,
    "Cargar archivos": upload_files,
    "Búsqueda API": api_search,
    "Similitud": similarity,
    "Conceptos": concepts,
    "Clustering": clustering,
    "Visualizaciones": visualization,
    "Exportar PDF": export_pdf,
}

with st.sidebar:
    st.title("Bibliometría GenAI")
    st.caption(
        "Universidad del Quindío  \n"
        "Análisis de Algoritmos  \n\n"
        "Daniel Stiven Perez Cordoba  \n"
        "Cristhian Eduardo Osorio Restrepo"
    )
    st.divider()
    page_name = st.radio("Sección", list(_PAGES.keys()), label_visibility="collapsed")

_PAGES[page_name].render()

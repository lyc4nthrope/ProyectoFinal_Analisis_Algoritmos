import matplotlib
matplotlib.use("Agg")

import streamlit as st
from streamlit_option_menu import option_menu

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

_ICONS = [
    "house",
    "cloud-upload",
    "search",
    "diagram-2",
    "lightbulb",
    "diagram-3",
    "bar-chart-line",
    "file-earmark-pdf",
]

with st.sidebar:
    page_name = option_menu(
        menu_title="Bibliometría GenAI",
        options=list(_PAGES.keys()),
        icons=_ICONS,
        menu_icon="book",
        default_index=0,
    )
    st.caption(
        "Universidad del Quindío  \n"
        "Análisis de Algoritmos  \n\n"
        "Daniel Stiven Perez Cordoba  \n"
        "Cristhian Eduardo Osorio Restrepo"
    )

_PAGES[page_name].render()

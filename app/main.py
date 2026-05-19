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
    st.title("Bibliometría GenAI")
    st.caption(
        "Universidad del Quindío  \n"
        "Análisis de Algoritmos  \n\n"
        "Daniel Stiven Perez Cordoba  \n"
        "Cristhian Eduardo Osorio Restrepo"
    )
    st.divider()
    page_name = option_menu(
        menu_title=None,
        options=list(_PAGES.keys()),
        icons=_ICONS,
        default_index=0,
        styles={
            "container": {"padding": "0", "margin-top": "-20px", "background-color": "transparent"},
            "nav-link": {"font-size": "0.9rem", "text-align": "left", "margin": "1px 0"},
            "nav-link-selected": {"background-color": "rgba(255,255,255,0.12)", "font-weight": "600"},
        },
    )

_PAGES[page_name].render()

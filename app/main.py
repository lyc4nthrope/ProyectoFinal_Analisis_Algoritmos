import matplotlib
matplotlib.use("Agg")

import streamlit as st

from app.views import clustering, concepts, export_pdf, overview, similarity, visualization

st.set_page_config(
    page_title="Bibliometría GenAI",
    layout="wide",
)

_PAGES = {
    "Inicio": overview,
    "Similitud": similarity,
    "Conceptos": concepts,
    "Clustering": clustering,
    "Visualizaciones": visualization,
    "Exportar PDF": export_pdf,
}

with st.sidebar:
    st.title("Bibliometría GenAI")
    st.caption("Universidad del Quindío — Análisis de Algoritmos")
    st.divider()
    page_name = st.radio("Sección", list(_PAGES.keys()), label_visibility="collapsed")

_PAGES[page_name].render()

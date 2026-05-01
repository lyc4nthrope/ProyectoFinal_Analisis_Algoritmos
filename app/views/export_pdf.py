import matplotlib.pyplot as plt
import streamlit as st

from app.loader import load_corpus
from src.visualization.pdf_exporter import export_report
from src.visualization.timeline_chart import build_year_timeline, build_journal_timeline
from src.visualization.wordcloud_chart import build_wordcloud_figure


def render() -> None:
    st.title("Exportar informe PDF")
    st.write("Selecciona las visualizaciones a incluir en el informe.")

    include_year = st.checkbox("Publicaciones por año", value=True)
    include_journal = st.checkbox("Publicaciones por revista (top 10)", value=True)
    include_wordcloud = st.checkbox("Nube de palabras", value=True)

    if not st.button("Generar PDF", type="primary"):
        return

    if not any([include_year, include_journal, include_wordcloud]):
        st.warning("Selecciona al menos una visualización.")
        return

    df = load_corpus()
    abstracts = df["abstract"].tolist()
    keywords = df["keywords"].tolist()

    figures = []
    matplotlib_figs = []

    with st.spinner("Generando PDF..."):
        if include_year:
            figures.append(("Publicaciones por año", build_year_timeline(df)))
        if include_journal:
            figures.append(("Publicaciones por revista (top 10)", build_journal_timeline(df)))
        if include_wordcloud:
            fig_wc = build_wordcloud_figure(abstracts, keywords)
            figures.append(("Nube de palabras — abstracts y keywords", fig_wc))
            matplotlib_figs.append(fig_wc)

        output_path = export_report(figures, filename="informe_bibliometrico.pdf")

    for fig in matplotlib_figs:
        plt.close(fig)

    st.success(f"PDF generado correctamente ({output_path.stat().st_size // 1024} KB).")
    with open(output_path, "rb") as f:
        st.download_button(
            label="Descargar PDF",
            data=f.read(),
            file_name="informe_bibliometrico.pdf",
            mime="application/pdf",
        )

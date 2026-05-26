# Importa matplotlib para cerrar las figuras después de usarlas (evita memory leaks)
import matplotlib.pyplot as plt
# Importa Streamlit para construir la interfaz de exportación
import streamlit as st

# Importa el loader del corpus con caché
from app.loader import load_corpus
# Importa las versiones matplotlib (estáticas) para el PDF
from src.visualization.geo_heatmap import build_country_counts, build_heatmap_figure_mpl
# Importa la función principal de exportación a PDF
from src.visualization.pdf_exporter import export_report
# Importa las gráficas de timeline en versión matplotlib para PDF
from src.visualization.timeline_chart import build_year_timeline_mpl, build_journal_timeline_mpl
# Importa la nube de palabras (matplotlib, compatible con PDF)
from src.visualization.wordcloud_chart import build_wordcloud_figure


def render() -> None:
    st.title("Exportar informe PDF")
    st.write("Selecciona las visualizaciones a incluir en el informe.")

    # Checkboxes para que el usuario elija qué visualizaciones incluir
    include_year = st.checkbox("Publicaciones por año", value=True)
    include_journal = st.checkbox("Publicaciones por revista (top 10)", value=True)
    include_wordcloud = st.checkbox("Nube de palabras", value=True)
    include_geo = st.checkbox("Mapa geográfico (primer autor)", value=True)
    st.caption(
        "Nota: país inferido desde DOI y afiliación del primer autor vía CrossRef. "
        "Puede haber registros sin resolución geográfica."
    )

    # Si no se presiona el botón, no hace nada (evita generar el PDF al cargar la página)
    if not st.button("Generar PDF", type="primary"):
        return

    # Valida que se haya seleccionado al menos una visualización
    if not any([include_year, include_journal, include_wordcloud, include_geo]):
        st.warning("Selecciona al menos una visualización.")
        return

    # Carga el corpus para generar las figuras
    df = load_corpus()
    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return
    abstracts = df["abstract"].tolist()
    keywords = df["keywords"].tolist()

    # Lista de figuras a incluir: (título, figura_matplotlib)
    figures = []
    # Nota metodológica que aparece en el PDF antes de las figuras
    notes = [
        (
            "Nota metodológica",
            [
                "Las visualizaciones se generan directamente desde unified.csv y corpus cargado en la aplicación.",
                "El mapa geográfico infiere país del primer autor usando DOI, CrossRef y afiliación disponible.",
                "Si un DOI no resuelve o la afiliación no contiene país reconocible, el registro se excluye del mapa.",
            ],
        ),
    ]

    # Genera cada figura seleccionada y la agrega a la lista
    with st.spinner("Generando PDF..."):
        if include_year:
            figures.append(("Publicaciones por año", build_year_timeline_mpl(df)))
        if include_journal:
            figures.append(("Publicaciones por revista (top 10)", build_journal_timeline_mpl(df)))
        if include_wordcloud:
            fig_wc = build_wordcloud_figure(abstracts, keywords)
            figures.append(("Nube de palabras — abstracts y keywords", fig_wc))
        if include_geo:
            # El mapa requiere resolver países via CrossRef (puede tardar)
            counts = build_country_counts(df)
            if counts.empty:
                st.warning("No se pudo resolver información geográfica suficiente para el PDF.")
            else:
                figures.append(("Distribución geográfica (primer autor)", build_heatmap_figure_mpl(counts)))

        # Llama al exportador para generar el PDF con todas las figuras seleccionadas
        output_path = export_report(
            figures,
            filename="informe_bibliometrico.pdf",
            notes=notes,
        )

    # Cierra todas las figuras matplotlib para liberar memoria
    for _, fig in figures:
        plt.close(fig)

    # Muestra el tamaño del PDF generado y un botón de descarga
    st.success(f"PDF generado correctamente ({output_path.stat().st_size // 1024} KB).")
    with open(output_path, "rb") as f:
        st.download_button(
            label="Descargar PDF",
            data=f.read(),
            file_name="informe_bibliometrico.pdf",
            mime="application/pdf",
        )

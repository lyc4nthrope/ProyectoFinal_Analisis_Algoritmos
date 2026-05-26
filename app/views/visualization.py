# Importa matplotlib para cerrar las figuras después de mostrarlas (evita memory leaks)
import matplotlib.pyplot as plt
# Importa Streamlit para construir la interfaz de visualizaciones
import streamlit as st

# Importa el loader del corpus con caché de Streamlit
from app.loader import load_corpus
# Importa las funciones para el mapa geográfico
from src.visualization.geo_heatmap import build_country_counts, build_heatmap_figure
# Importa las funciones para las gráficas de publicaciones por año y revista
from src.visualization.timeline_chart import build_year_timeline, build_journal_timeline
# Importa la función para la nube de palabras
from src.visualization.wordcloud_chart import build_wordcloud_figure


def render() -> None:
    st.title("Visualizaciones bibliométricas")

    # Carga el corpus desde el caché de Streamlit
    df = load_corpus()
    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return
    # Extrae los abstracts y keywords para la nube de palabras
    abstracts = df["abstract"].tolist()
    keywords = df["keywords"].tolist()

    # Gráfico interactivo de publicaciones por año (Plotly)
    st.subheader("Publicaciones por año")
    st.plotly_chart(build_year_timeline(df), width="stretch")

    # Gráfico interactivo de publicaciones por revista (top 10, Plotly)
    st.subheader("Publicaciones por revista (top 10)")
    st.plotly_chart(build_journal_timeline(df), width="stretch")

    # Nube de palabras con los términos más frecuentes en abstracts y keywords
    st.subheader("Nube de palabras — abstracts y keywords")
    with st.spinner("Generando nube de palabras..."):
        fig_wc = build_wordcloud_figure(abstracts, keywords)
    st.pyplot(fig_wc)
    # Cierra la figura de matplotlib para liberar memoria
    plt.close(fig_wc)

    # Mapa geográfico con el país del primer autor de cada artículo
    st.subheader("Distribución geográfica (primer autor)")
    st.info(
        "Requiere consultas a la API de CrossRef. "
        "Los resultados se almacenan en caché local; la primera ejecución puede tardar varios minutos. "
        "El país se infiere desde DOI y afiliación del primer autor, por lo que puede haber casos no resueltos."
    )
    # Se carga bajo demanda con un botón para no hacer llamadas innecesarias a CrossRef
    if st.button("Cargar mapa geográfico"):
        with st.spinner("Resolviendo países desde CrossRef..."):
            counts = build_country_counts(df)

        if counts.empty:
            st.warning("No se pudieron resolver países para los DOIs del corpus.")
        else:
            # Muestra el mapa coroplético interactivo de Plotly
            st.plotly_chart(build_heatmap_figure(counts), width="stretch")
            # Tabla de respaldo con los números exactos por país
            st.dataframe(counts.rename(columns={"country": "País", "count": "Artículos"}),
                         width="stretch", hide_index=True)

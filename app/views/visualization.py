import matplotlib.pyplot as plt
import streamlit as st

from app.loader import load_corpus
from src.visualization.geo_heatmap import build_country_counts, build_heatmap_figure
from src.visualization.timeline_chart import build_year_timeline, build_journal_timeline
from src.visualization.wordcloud_chart import build_wordcloud_figure


def render() -> None:
    st.title("Visualizaciones bibliométricas")

    df = load_corpus()
    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return
    abstracts = df["abstract"].tolist()
    keywords = df["keywords"].tolist()

    st.subheader("Publicaciones por año")
    st.plotly_chart(build_year_timeline(df), width="stretch")

    st.subheader("Publicaciones por revista (top 10)")
    st.plotly_chart(build_journal_timeline(df), width="stretch")

    st.subheader("Nube de palabras — abstracts y keywords")
    with st.spinner("Generando nube de palabras..."):
        fig_wc = build_wordcloud_figure(abstracts, keywords)
    st.pyplot(fig_wc)
    plt.close(fig_wc)

    st.subheader("Distribución geográfica (primer autor)")
    st.info(
        "Requiere consultas a la API de CrossRef. "
        "Los resultados se almacenan en caché local; la primera ejecución puede tardar varios minutos. "
        "El país se infiere desde DOI y afiliación del primer autor, por lo que puede haber casos no resueltos."
    )
    if st.button("Cargar mapa geográfico"):
        with st.spinner("Resolviendo países desde CrossRef..."):
            counts = build_country_counts(df)

        if counts.empty:
            st.warning("No se pudieron resolver países para los DOIs del corpus.")
        else:
            st.plotly_chart(build_heatmap_figure(counts), width="stretch")
            st.dataframe(counts.rename(columns={"country": "País", "count": "Artículos"}),
                         width="stretch", hide_index=True)

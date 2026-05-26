# Importa matplotlib para cerrar la figura del dendrograma y liberar memoria
import matplotlib.pyplot as plt
# Importa pandas para construir la tabla de comparación de métodos
import pandas as pd
# Importa Streamlit para construir la interfaz de clustering
import streamlit as st

# Importa los analizadores con caché de Streamlit
from app.loader import get_clustering_analyzer, load_corpus
# Importa el diccionario con los métodos de enlace disponibles
from src.clustering.hierarchical import LINKAGE_METHODS


def render() -> None:
    st.title("Clustering jerárquico")

    # Obtiene el analizador de clustering (ya inicializado desde el caché)
    analyzer = get_clustering_analyzer()
    if analyzer is None:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return

    # Placeholder para mensajes de progreso durante el clustering
    progress_placeholder = st.empty()

    def on_progress(msg: str) -> None:
        # Callback que actualiza el mensaje de progreso en la interfaz
        progress_placeholder.info(f"⏳ {msg}")

    # Ejecuta los 3 métodos de clustering (o retorna del caché si ya se calculó)
    with st.spinner("Procesando..."):
        all_results = analyzer.run_all(progress_callback=on_progress)

    progress_placeholder.success(f"✅ Clustering completado en {len(analyzer.timing)} pasos.")

    # Informa la estrategia usada: full (≤5000 docs) o two-tier (>5000 docs)
    n_clusters = analyzer.n_clusters
    if analyzer.strategy == "two-tier":
        st.info(
            f"📊 Corpus grande ({analyzer.n_documents:,} docs): se usó **K-Means** "
            f"para reducir a {n_clusters} clusters, y luego clustering jerárquico "
            f"sobre los centroides. El dendrograma muestra {n_clusters} hojas.",
        )
    else:
        st.caption(f"Dendrograma con {n_clusters} documentos hoja.")

    # Muestra los tiempos de ejecución en un expandible
    with st.expander("⏱️ Tiempos de ejecución"):
        st.code("\n".join(analyzer.timing))

    # Identifica el mejor método por correlación cofenética
    best = analyzer.best_method()

    # Tabla comparativa: todos los métodos ordenados por correlación cofenética
    st.subheader("Comparación de métodos — correlación cofenética")
    comparison_df = pd.DataFrame([
        {
            "Método": r.method_name,
            "Correlación cofenética": r.cophenetic_correlation,
            "Mejor": "Si" if r.method_key == best.method_key else "",
        }
        for r in sorted(all_results.values(), key=lambda r: r.cophenetic_correlation, reverse=True)
    ])
    st.dataframe(comparison_df, width="stretch", hide_index=True)
    st.info(
        f"Método con mayor coherencia: **{best.method_name}** "
        f"(correlación cofenética = {best.cophenetic_correlation})"
    )

    # Selector de método para ver el dendrograma correspondiente
    st.subheader("Dendrograma")
    method_key = st.radio(
        "Método de enlace",
        options=list(LINKAGE_METHODS.keys()),
        format_func=lambda k: LINKAGE_METHODS[k],  # Muestra el nombre descriptivo
        horizontal=True,
    )

    # Genera y muestra el dendrograma del método seleccionado
    with st.spinner("Generando dendrograma..."):
        fig = analyzer.get_dendrogram_figure(method_key)

    st.pyplot(fig)
    # Cierra la figura para liberar memoria después de mostrarla
    plt.close(fig)

    # Selector de cluster para explorar los documentos asignados a cada grupo
    if analyzer.cluster_assignments:
        st.subheader("Documentos por cluster")

        counts = analyzer.cluster_counts
        cluster_options = analyzer.cluster_ids

        # Selectbox que muestra el ID y la cantidad de documentos de cada cluster
        selected_cluster = st.selectbox(
            "Seleccioná un cluster para ver sus documentos:",
            options=cluster_options,
            format_func=lambda cid: f"Cluster #{cid} ({counts[cid]} documentos)",
            key="cluster_selector",
        )

        # Obtiene los índices de los documentos del cluster seleccionado
        doc_indices = analyzer.get_cluster_doc_indices(selected_cluster)
        if doc_indices:
            # Carga el corpus completo para mostrar los metadatos de los documentos
            df = load_corpus()
            if not df.empty:
                # Extrae las filas del corpus correspondientes al cluster
                cluster_df = df.iloc[doc_indices].reset_index(drop=True)
                show_cols = ["title", "authors", "year", "doi"]
                available = [c for c in show_cols if c in cluster_df.columns]
                display = cluster_df[available].copy()
                display.columns = ["Título", "Autores", "Año", "DOI"][:len(available)]
                st.dataframe(display, width="stretch", hide_index=True, height=400)
                st.caption(f"{len(doc_indices)} documento(s) en este cluster.")
            else:
                # Fallback: si el corpus no cargó, muestra solo los títulos del analyzer
                st.dataframe(
                    pd.DataFrame({"Título": analyzer.get_titles_for_indices(doc_indices)}),
                    width="stretch", hide_index=True, height=400,
                )

    # Expandible con los pasos del algoritmo del método seleccionado actualmente
    with st.expander("Ver pasos del algoritmo"):
        st.text("\n".join(all_results[method_key].steps))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app.loader import get_clustering_analyzer, load_corpus
from src.clustering.hierarchical import LINKAGE_METHODS


def render() -> None:
    st.title("Clustering jerárquico")

    analyzer = get_clustering_analyzer()
    if analyzer is None:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return

    progress_placeholder = st.empty()

    def on_progress(msg: str) -> None:
        progress_placeholder.info(f"⏳ {msg}")

    with st.spinner("Procesando..."):
        all_results = analyzer.run_all(progress_callback=on_progress)

    progress_placeholder.success(f"✅ Clustering completado en {len(analyzer.timing)} pasos.")

    # Info de estrategia
    n_clusters = analyzer.n_clusters
    if analyzer.strategy == "two-tier":
        st.info(
            f"📊 Corpus grande ({analyzer._corpus.n_docs:,} docs): se usó **K-Means** "
            f"para reducir a {n_clusters} clusters, y luego clustering jerárquico "
            f"sobre los centroides. El dendrograma muestra {n_clusters} hojas.",
        )
    else:
        st.caption(f"Dendrograma con {n_clusters} documentos hoja.")

    with st.expander("⏱️ Tiempos de ejecución"):
        st.code("\n".join(analyzer.timing))

    best = analyzer.best_method()

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

    st.subheader("Dendrograma")
    method_key = st.radio(
        "Método de enlace",
        options=list(LINKAGE_METHODS.keys()),
        format_func=lambda k: LINKAGE_METHODS[k],
        horizontal=True,
    )

    with st.spinner("Generando dendrograma..."):
        fig = analyzer.get_dendrogram_figure(method_key)

    st.pyplot(fig)
    plt.close(fig)

    # ── Documentos por cluster ──────────────────────────────────────────
    if analyzer.cluster_assignments:
        st.subheader("Documentos por cluster")

        counts = analyzer.cluster_counts
        cluster_options = analyzer.cluster_ids

        selected_cluster = st.selectbox(
            "Seleccioná un cluster para ver sus documentos:",
            options=cluster_options,
            format_func=lambda cid: f"Cluster #{cid} ({counts[cid]} documentos)",
            key="cluster_selector",
        )

        doc_indices = analyzer.get_cluster_doc_indices(selected_cluster)
        if doc_indices:
            # Cargar el corpus para mostrar info detallada
            df = load_corpus()
            if not df.empty:
                cluster_df = df.iloc[doc_indices].reset_index(drop=True)
                show_cols = ["title", "authors", "year", "doi"]
                available = [c for c in show_cols if c in cluster_df.columns]
                display = cluster_df[available].copy()
                display.columns = ["Título", "Autores", "Año", "DOI"][:len(available)]
                st.dataframe(display, width="stretch", hide_index=True, height=400)
                st.caption(f"{len(doc_indices)} documento(s) en este cluster.")
            else:
                # Fallback: mostrar solo títulos desde el analyzer
                st.dataframe(
                    pd.DataFrame({"Título": [analyzer._titles[i] for i in doc_indices]}),
                    width="stretch", hide_index=True, height=400,
                )

    with st.expander("Ver pasos del algoritmo"):
        st.text("\n".join(all_results[method_key].steps))

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from app.loader import get_clustering_analyzer
from src.clustering.hierarchical import LINKAGE_METHODS


def render() -> None:
    st.title("Clustering jerárquico")

    analyzer = get_clustering_analyzer()

    with st.spinner("Calculando los tres métodos de agrupamiento..."):
        all_results = analyzer.run_all()

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

    with st.expander("Ver pasos del algoritmo"):
        st.text("\n".join(all_results[method_key].steps))

import pandas as pd
import streamlit as st

from app.loader import get_similarity_analyzer, load_corpus


def render() -> None:
    st.title("Análisis de similitud")
    st.caption("Compara dos artículos usando 6 algoritmos de similitud textual.")

    df = load_corpus()
    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return
    titles = df["title"].tolist()
    abstracts = df["abstract"].tolist()

    col1, col2 = st.columns(2)
    with col1:
        idx_a = st.selectbox(
            "Artículo A",
            range(len(titles)),
            format_func=lambda i: titles[i],
            key="sim_a",
        )
    with col2:
        idx_b = st.selectbox(
            "Artículo B",
            range(len(titles)),
            format_func=lambda i: titles[i],
            key="sim_b",
            index=min(1, max(0, len(titles) - 1)),
        )

    if idx_a == idx_b:
        st.warning("Selecciona dos artículos diferentes.")
        return

    if st.button("Comparar", type="primary"):
        with st.spinner("Calculando similitud (el primer cálculo carga el modelo de embeddings)..."):
            analyzer = get_similarity_analyzer()
            results = analyzer.compare(abstracts[idx_a], abstracts[idx_b])

        results_sorted = sorted(results, key=lambda r: r.score, reverse=True)

        st.subheader("Resultados")
        rows = [{"Algoritmo": r.algorithm, "Score": r.score} for r in results_sorted]
        st.dataframe(
            pd.DataFrame(rows).style.format({"Score": "{:.4f}"}),
            width="stretch",
            hide_index=True,
        )

        st.subheader("Pasos de cálculo")
        for r in results_sorted:
            with st.expander(f"{r.algorithm} — score: {r.score:.4f}"):
                st.text("\n".join(r.steps))

import time

import pandas as pd
import streamlit as st

from app.loader import get_similarity_analyzer, load_corpus
from src.similarity.base_similarity import CancelToken


def _algo_dropdown_options(analyzer) -> list[str]:
    return [
        f"{option['name']} — {option['complexity_time']}"
        for option in analyzer.algorithm_options
    ]


def _parse_algo_name(dropdown_value: str) -> str:
    return dropdown_value.split(" — ")[0]


def render() -> None:
    st.title("Análisis de similitud")
    st.caption("Compará artículos académicos usando 6 algoritmos de similitud textual.")

    df = load_corpus()
    if df.empty:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return

    titles = df["title"].tolist()
    texts = df["abstract"].tolist()

    analyzer = get_similarity_analyzer()
    if analyzer is None:
        st.warning("No se pudo inicializar el analizador de similitud.")
        return

    if "sim_cancel_token" not in st.session_state:
        st.session_state.sim_cancel_token = None

    tab1, tab2, tab3 = st.tabs(["Comparar 2", "Encontrar similares", "Matriz N×N"])

    with tab1:
        _render_tab_compare(titles, texts, analyzer)

    with tab2:
        _render_tab_find_similar(titles, texts, analyzer)

    with tab3:
        _render_tab_matrix(titles, texts, analyzer)


def _render_tab_compare(
    titles: list[str],
    texts: list[str],
    analyzer,
) -> None:
    assert analyzer is not None
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
        st.warning("Seleccioná dos artículos diferentes.")
        return

    if st.button("Comparar", type="primary"):
        with st.spinner("Calculando similitud (el primer cálculo carga el modelo de embeddings)..."):
            results = analyzer.compare(texts[idx_a], texts[idx_b])

        results_sorted = sorted(results, key=lambda r: r.score, reverse=True)

        st.subheader("Resultados")
        rows = []
        for r in results_sorted:
            rows.append({
                "Algoritmo": r.algorithm,
                "Score": r.score,
                "Tiempo (ms)": f"{r.time_ms:.1f}",
                "Complejidad (tiempo)": r.complexity_time,
                "Complejidad (espacio)": r.complexity_space,
            })
        st.dataframe(
            pd.DataFrame(rows).style.format({"Score": "{:.4f}"}),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Pasos de cálculo")
        for r in results_sorted:
            with st.expander(f"{r.algorithm} — score: {r.score:.4f} — {r.time_ms:.1f}ms"):
                st.text("\n".join(r.steps))


def _render_tab_find_similar(
    titles: list[str],
    texts: list[str],
    analyzer,
) -> None:
    assert analyzer is not None
    idx = st.selectbox(
        "Artículo (texto de consulta)",
        range(len(titles)),
        format_func=lambda i: titles[i],
        key="find_idx",
    )

    k = st.slider("Cantidad de resultados (k)", min_value=1, max_value=50, value=10)

    if st.session_state.sim_cancel_token is not None:
        if st.button("⏹️ Cancelar"):
            st.session_state.sim_cancel_token.cancel()
            st.session_state.sim_cancel_token = None
            st.rerun()

    if st.button("Buscar similares", type="primary"):
        cancel_token = CancelToken()
        st.session_state.sim_cancel_token = cancel_token

        try:
            t0 = time.time()
            with st.spinner("Buscando documentos similares..."):
                results = analyzer.find_most_similar(
                    text=texts[idx],
                    corpus_texts=texts,
                    corpus_titles=titles,
                    k=k,
                    cancel_token=cancel_token,
                )
            elapsed = time.time() - t0

            if cancel_token.is_cancelled:
                st.warning("⏹️ Operación cancelada por el usuario.")
                return

            for algo_name, algo_results in results.items():
                st.subheader(algo_name)

                data = []
                for r in algo_results:
                    data.append({
                        "Título": r.title,
                        "Score": r.score,
                    })
                st.dataframe(
                    pd.DataFrame(data).style.format({"Score": "{:.4f}"}),
                    use_container_width=True,
                    hide_index=True,
                )

                with st.expander(f"Pasos de cálculo — {algo_name}"):
                    for r in algo_results:
                        st.markdown(f"**{r.title}** — score: {r.score:.4f}")
                        st.text("\n".join(r.steps))

            st.success(f"✅ Completado en {elapsed:.1f}s")
        finally:
            if st.session_state.sim_cancel_token is cancel_token:
                st.session_state.sim_cancel_token = None


def _render_tab_matrix(
    titles: list[str],
    texts: list[str],
    analyzer,
) -> None:
    assert analyzer is not None
    selected = st.multiselect(
        "Seleccionar artículos para la matriz de similitud",
        range(len(titles)),
        format_func=lambda i: (titles[i][:80] + "...") if len(titles[i]) > 80 else titles[i],
        key="matrix_sel",
    )
    N = len(selected)

    if N > 0:
        st.caption(f"Seleccionados: {N} artículo{'s' if N != 1 else ''}")

    if 0 < N < 3:
        st.warning("Seleccioná al menos 3 artículos para generar la matriz.")
        return

    if N > 50:
        st.warning("⚠️ Más de 50 artículos seleccionados — el cálculo puede ser lento. Se recomienda seleccionar menos artículos o usar 1 solo algoritmo.")

    algo_options = _algo_dropdown_options(analyzer)

    if N <= 10:
        dropdown_options = ["--- Todos los algoritmos ---"] + algo_options
        algo_default = 0
    else:
        dropdown_options = algo_options
        algo_default = 0

    if len(dropdown_options) > 0:
        selected_dropdown = st.selectbox(
            "Algoritmo" + (" (obligatorio)" if N > 10 else " (opcional)"),
            dropdown_options,
            index=algo_default,
            key="matrix_algo",
        )
    else:
        selected_dropdown = None

    if 0 < N < 3:
        return

    if st.session_state.sim_cancel_token is not None:
        if st.button("⏹️ Cancelar"):
            st.session_state.sim_cancel_token.cancel()
            st.session_state.sim_cancel_token = None
            st.rerun()

    if st.button("Calcular matriz", type="primary"):
        selected_texts = [texts[i] for i in selected]
        selected_titles = [titles[i] for i in selected]

        if N > 10 and (selected_dropdown is None or selected_dropdown == ""):
            st.error("Seleccioná un algoritmo específico para continuar.")
            return

        if selected_dropdown and selected_dropdown != "--- Todos los algoritmos ---":
            algorithms_to_run = [_parse_algo_name(selected_dropdown)]
        else:
            algorithms_to_run = [_parse_algo_name(opt) for opt in algo_options]

        cancel_token = CancelToken()
        st.session_state.sim_cancel_token = cancel_token

        try:
            total_t0 = time.time()
            progress_bar = st.progress(0)
            status = st.empty()

            for i, algo_name in enumerate(algorithms_to_run):
                if cancel_token.is_cancelled:
                    break

                status.text(f"📊 Calculando {algo_name}...")

                result = analyzer.compute_matrix_single(
                    algo_name,
                    selected_texts,
                    cancel_token=cancel_token,
                )

                if result is None:
                    continue

                matrix, elapsed_ms = result
                elapsed_s = elapsed_ms / 1000

                df_matrix = pd.DataFrame(
                    matrix,
                    index=[t[:30] + "..." for t in selected_titles],
                    columns=[t[:30] + "..." for t in selected_titles],
                )
                st.subheader(f"{algo_name} — {elapsed_s:.2f}s")
                st.dataframe(
                    df_matrix.style.background_gradient(cmap="YlOrRd", axis=None),
                    use_container_width=True,
                )

                progress_bar.progress((i + 1) / len(algorithms_to_run))

            total_elapsed = time.time() - total_t0

            if cancel_token.is_cancelled:
                st.warning("⏹️ Operación cancelada.")
            else:
                st.success(f"✅ Completado en {total_elapsed:.1f}s")

            progress_bar.empty()

        finally:
            if st.session_state.sim_cancel_token is cancel_token:
                st.session_state.sim_cancel_token = None

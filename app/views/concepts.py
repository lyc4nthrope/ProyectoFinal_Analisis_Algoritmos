import pandas as pd
import plotly.express as px
import streamlit as st

from app.loader import get_concept_analyzer


def render() -> None:
    st.title("Análisis de conceptos GenAI")

    analyzer = get_concept_analyzer()

    st.subheader("Frecuencia de conceptos en el corpus")
    freq_results = analyzer.frequency_analysis()

    freq_df = pd.DataFrame([
        {
            "Concepto": r.concept,
            "Ocurrencias totales": r.total_occurrences,
            "Documentos que lo mencionan": r.document_count,
        }
        for r in freq_results
    ])

    fig = px.bar(
        freq_df,
        x="Concepto",
        y="Ocurrencias totales",
        color="Ocurrencias totales",
        color_continuous_scale="Blues",
        title=f"Categoría: {analyzer.category}",
        labels={"Concepto": "Concepto", "Ocurrencias totales": "Ocurrencias"},
    )
    fig.update_layout(xaxis_tickangle=-40, coloraxis_showscale=False, height=420)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(freq_df, width="stretch", hide_index=True)

    st.subheader("Términos asociados extraídos por TF-IDF")
    with st.spinner("Extrayendo términos..."):
        extraction = analyzer.extract_new_words()

    words_df = pd.DataFrame([
        {"Término": w.term, "Score TF-IDF": w.score}
        for w in extraction.words
    ])
    st.dataframe(
        words_df.style.format({"Score TF-IDF": "{:.4f}"}),
        width="stretch",
        hide_index=True,
    )

    with st.expander("Ver pasos del proceso TF-IDF"):
        st.text("\n".join(extraction.steps))

    st.subheader("Evaluación: Precision / Recall / F1")
    pr = analyzer.evaluate_precision()

    col1, col2, col3 = st.columns(3)
    col1.metric("Precision", f"{pr.precision:.2%}")
    col2.metric("Recall", f"{pr.recall:.2%}")
    col3.metric("F1-Score", f"{pr.f1:.2%}")

    with st.expander("Ver pasos de evaluación"):
        st.text("\n".join(pr.steps))

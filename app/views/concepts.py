# Importa pandas para construir los DataFrames de conceptos y términos
import pandas as pd
# Importa plotly express para el gráfico de barras interactivo
import plotly.express as px
# Importa Streamlit para construir la interfaz
import streamlit as st

# Importa el analizador de conceptos desde el loader con caché de Streamlit
from app.loader import get_concept_analyzer


def render() -> None:
    st.title("Análisis de conceptos GenAI")

    # Obtiene el analizador de conceptos (ya entrenado desde el caché)
    analyzer = get_concept_analyzer()
    if analyzer is None:
        st.warning("📭 No hay datos en el corpus. Usá la sección 'Búsqueda API' para buscar artículos e integrarlos al corpus.")
        return

    # Calcula la frecuencia de cada uno de los 15 conceptos del dominio en el corpus
    st.subheader("Frecuencia de conceptos en el corpus")
    freq_results = analyzer.frequency_analysis()

    # Construye el DataFrame de frecuencias para la tabla y el gráfico
    freq_df = pd.DataFrame([
        {
            "Concepto": r.concept,
            "Ocurrencias totales": r.total_occurrences,
            "Documentos que lo mencionan": r.document_count,
        }
        for r in freq_results
    ])

    # Gráfico de barras: X = concepto, Y = ocurrencias totales, color = cantidad
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
    # Tabla complementaria con los números exactos
    st.dataframe(freq_df, width="stretch", hide_index=True)

    # Extrae los términos más representativos del corpus usando TF-IDF
    st.subheader("Términos asociados extraídos por TF-IDF")
    with st.spinner("Extrayendo términos..."):
        extraction = analyzer.extract_new_words()

    # Tabla de términos extraídos con su score TF-IDF
    words_df = pd.DataFrame([
        {"Término": w.term, "Score TF-IDF": w.score}
        for w in extraction.words
    ])
    st.dataframe(
        words_df.style.format({"Score TF-IDF": "{:.4f}"}),
        width="stretch",
        hide_index=True,
    )

    # Expandible con la explicación matemática paso a paso del proceso TF-IDF
    with st.expander("Ver pasos del proceso TF-IDF"):
        st.text("\n".join(extraction.steps))

    # Muestra las métricas de evaluación: Precision, Recall y F1
    st.subheader("Evaluación: Precision / Recall / F1")
    pr = analyzer.evaluate_precision()

    col1, col2, col3 = st.columns(3)
    col1.metric("Precision", f"{pr.precision:.2%}")
    col2.metric("Recall", f"{pr.recall:.2%}")
    col3.metric("F1-Score", f"{pr.f1:.2%}")

    # Expandible con la explicación de cómo se calcularon las métricas
    with st.expander("Ver pasos de evaluación"):
        st.text("\n".join(pr.steps))

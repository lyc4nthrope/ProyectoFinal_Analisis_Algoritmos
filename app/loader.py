# Importa Streamlit para usar los decoradores de caché
import streamlit as st
# Importa pandas para el tipo de retorno del corpus
import pandas as pd

# Importa los analizadores que se crean una vez y se comparten en toda la sesión
from src.analysis.concept_analyzer import ConceptAnalyzer
from src.clustering.clustering_analyzer import ClusteringAnalyzer
# Importa la función de carga del corpus desde el repositorio
from src.repositories import load_corpus_df
# Importa el analizador de similitud textual
from src.similarity.similarity_analyzer import SimilarityAnalyzer


@st.cache_data
def load_corpus() -> pd.DataFrame:
    # Intenta cargar el corpus desde el CSV procesado
    df = load_corpus_df()
    if df.empty:
        # Si no hay corpus, ejecuta el pipeline de unificación para generarlo
        from src.processing.unifier import run
        run()
        df = load_corpus_df()
    return df
    # @st.cache_data: Streamlit almacena en caché el resultado; solo recalcula si los datos cambian


@st.cache_resource
def get_similarity_analyzer() -> SimilarityAnalyzer | None:
    # Carga el corpus y crea el analizador de similitud con los abstracts
    df = load_corpus()
    if df.empty:
        return None
    # SimilarityAnalyzer entrena los 6 algoritmos al crearse (puede tardar la primera vez)
    return SimilarityAnalyzer(df["abstract"].tolist())
    # @st.cache_resource: el objeto se reutiliza entre todas las peticiones sin recrearlo


@st.cache_resource
def get_concept_analyzer() -> ConceptAnalyzer | None:
    # Carga el corpus y crea el analizador de conceptos con los abstracts
    df = load_corpus()
    if df.empty:
        return None
    return ConceptAnalyzer(df["abstract"].tolist())


@st.cache_resource
def get_clustering_analyzer() -> ClusteringAnalyzer | None:
    # Carga el corpus y crea el analizador de clustering con abstracts y títulos
    df = load_corpus()
    if df.empty:
        return None
    # ClusteringAnalyzer necesita los títulos para etiquetar el dendrograma
    return ClusteringAnalyzer(df["abstract"].tolist(), df["title"].tolist())

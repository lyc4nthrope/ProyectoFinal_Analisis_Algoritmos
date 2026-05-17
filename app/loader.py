import streamlit as st
import pandas as pd

from src.analysis.concept_analyzer import ConceptAnalyzer
from src.clustering.clustering_analyzer import ClusteringAnalyzer
from src.repositories import load_corpus_df
from src.similarity.similarity_analyzer import SimilarityAnalyzer


@st.cache_data
def load_corpus() -> pd.DataFrame:
    df = load_corpus_df()
    if df.empty:
        from src.processing.unifier import run
        run()
        df = load_corpus_df()
    return df


@st.cache_resource
def get_similarity_analyzer() -> SimilarityAnalyzer | None:
    df = load_corpus()
    if df.empty:
        return None
    return SimilarityAnalyzer(df["abstract"].tolist())


@st.cache_resource
def get_concept_analyzer() -> ConceptAnalyzer | None:
    df = load_corpus()
    if df.empty:
        return None
    return ConceptAnalyzer(df["abstract"].tolist())


@st.cache_resource
def get_clustering_analyzer() -> ClusteringAnalyzer | None:
    df = load_corpus()
    if df.empty:
        return None
    return ClusteringAnalyzer(df["abstract"].tolist(), df["title"].tolist())

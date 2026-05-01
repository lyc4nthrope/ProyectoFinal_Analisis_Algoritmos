import streamlit as st
import pandas as pd

from src.config import PROCESSED_DIR
from src.analysis.concept_analyzer import ConceptAnalyzer
from src.clustering.clustering_analyzer import ClusteringAnalyzer
from src.similarity.similarity_analyzer import SimilarityAnalyzer


@st.cache_data
def load_corpus() -> pd.DataFrame:
    path = PROCESSED_DIR / "unified.csv"
    if not path.exists():
        from src.processing.unifier import run
        run()
    return pd.read_csv(path).fillna("")


@st.cache_resource
def get_similarity_analyzer() -> SimilarityAnalyzer:
    abstracts = load_corpus()["abstract"].tolist()
    return SimilarityAnalyzer(abstracts)


@st.cache_resource
def get_concept_analyzer() -> ConceptAnalyzer:
    abstracts = load_corpus()["abstract"].tolist()
    return ConceptAnalyzer(abstracts)


@st.cache_resource
def get_clustering_analyzer() -> ClusteringAnalyzer:
    df = load_corpus()
    return ClusteringAnalyzer(df["abstract"].tolist(), df["title"].tolist())

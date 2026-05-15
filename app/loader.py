import hashlib
import json
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd

from src.config import PROCESSED_DIR, RAW_DIR
from src.analysis.concept_analyzer import ConceptAnalyzer
from src.clustering.clustering_analyzer import ClusteringAnalyzer
from src.similarity.similarity_analyzer import SimilarityAnalyzer


@st.cache_data
def load_corpus() -> pd.DataFrame:
    path = PROCESSED_DIR / "unified.csv"
    if not path.exists():
        from src.processing.unifier import run
        run()
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path).fillna("")


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


def save_api_cache(query: str, max_results: int, results: list[dict]) -> None:
    cache_dir = RAW_DIR / "api_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    raw = f"{query}|{max_results}"
    hash_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
    cache_file = cache_dir / f"{hash_key}.json"

    cache_data = {
        "query": query,
        "max_results": max_results,
        "cached_at": datetime.now().isoformat(),
        "results": results,
    }

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)


def load_api_cache(query: str, max_results: int) -> list[dict] | None:
    cache_dir = RAW_DIR / "api_cache"
    raw = f"{query}|{max_results}"
    hash_key = hashlib.sha256(raw.encode()).hexdigest()[:16]
    cache_file = cache_dir / f"{hash_key}.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["results"]
    except (json.JSONDecodeError, KeyError, IOError):
        return None

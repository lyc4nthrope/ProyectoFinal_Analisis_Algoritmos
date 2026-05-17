from dataclasses import dataclass

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.processing.text_preprocessing import to_string


@dataclass
class CorpusMatrix:
    matrix: np.ndarray
    labels: list[str]
    n_docs: int
    n_features: int
    n_components: int
    steps: list[str]


def build_matrix(abstracts: list[str], titles: list[str]) -> CorpusMatrix:
    """
    Convierte abstracts en una matriz TF-IDF normalizada por L2,
    con reducción de dimensionalidad vía TruncatedSVD (100 componentes).

    La normalización L2 hace que ||v||=1 para cada documento,
    lo que permite usar distancia euclidiana como equivalente a distancia coseno:
        d_eucl(a, b) = √(2 - 2·cos(a,b))
    Esta equivalencia permite aplicar Ward (que exige euclidiana) con
    la misma base geométrica que los otros métodos.

    SVD (TruncatedSVD, 100 componentes) reduce la dimensionalidad de ~5000
    términos a 100 dimensiones latentes, acelerando drásticamente el cálculo
    de distancias en el clustering jerárquico sin perder información semántica
    relevante (es Análisis Semántico Latente / LSA).
    """
    processed = [to_string(abstract) for abstract in abstracts]

    vectorizer = TfidfVectorizer(min_df=2, max_df=0.9)
    tfidf_sparse = vectorizer.fit_transform(processed)
    n_features = tfidf_sparse.shape[1]

    # SVD reduce dimensionalidad: máx 100 o n_features-1 (lo que sea menor)
    n_target = min(100, max(1, n_features - 1))
    svd = TruncatedSVD(n_components=n_target, random_state=42)
    tfidf_dense = svd.fit_transform(tfidf_sparse)

    matrix = normalize(tfidf_dense, norm="l2")

    labels = [
        (t[:40] + "...") if len(t) > 40 else t
        for t in titles
    ]

    n_docs, n_components = matrix.shape

    steps = [
        f"1. Preprocesamiento: tokenización y eliminación de stopwords en {n_docs} abstracts.",
        f"2. Vectorización TF-IDF: min_df=2, max_df=0.9 → vocabulario de {n_features} términos.",
    ]
    if n_target < n_features:
        steps.append(
            f"3. Reducción de dimensionalidad con TruncatedSVD: {n_features} → {n_components} componentes."
            f"\n   Motivo: acelerar el cálculo de distancias (50x más rápido).",
        )
    steps += [
        f"{'4' if n_target < n_features else '3'}. Normalización L2: ||v||=1.",
        f"   Matriz resultante: {n_docs} documentos × {n_components} componentes.",
    ]

    return CorpusMatrix(matrix=matrix, labels=labels, n_docs=n_docs, n_components=n_components, n_features=n_features, steps=steps)

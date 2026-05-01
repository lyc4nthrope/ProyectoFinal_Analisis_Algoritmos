from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.processing.text_preprocessing import to_string


@dataclass
class CorpusMatrix:
    matrix: np.ndarray
    labels: list[str]
    n_docs: int
    n_features: int
    steps: list[str]


def build_matrix(abstracts: list[str], titles: list[str]) -> CorpusMatrix:
    """
    Convierte abstracts en una matriz TF-IDF normalizada por L2.

    La normalización L2 hace que ||v||=1 para cada documento,
    lo que permite usar distancia euclidiana como equivalente a distancia coseno:
        d_eucl(a, b) = √(2 - 2·cos(a,b))
    Esta equivalencia permite aplicar Ward (que exige euclidiana) con
    la misma base geométrica que los otros métodos.
    """
    processed = [to_string(abstract) for abstract in abstracts]

    vectorizer = TfidfVectorizer(min_df=2, max_df=0.9)
    tfidf_sparse = vectorizer.fit_transform(processed)
    matrix = normalize(tfidf_sparse, norm="l2").toarray()

    labels = [
        (t[:40] + "...") if len(t) > 40 else t
        for t in titles
    ]

    n_docs, n_features = matrix.shape

    steps = [
        f"1. Preprocesamiento: tokenización y eliminación de stopwords en {n_docs} abstracts.",
        f"2. Vectorización TF-IDF: min_df=2, max_df=0.9 → vocabulario de {n_features} términos.",
        f"3. Normalización L2: cada vector dividido por su norma euclidiana → ||v||=1.",
        f"   Motivo: permite usar distancia euclidiana para Ward manteniendo equivalencia coseno.",
        f"   Matriz resultante: {n_docs} documentos × {n_features} características.",
    ]

    return CorpusMatrix(matrix=matrix, labels=labels, n_docs=n_docs, n_features=n_features, steps=steps)

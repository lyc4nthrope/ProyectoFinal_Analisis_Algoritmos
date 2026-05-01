import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.processing.text_preprocessing import to_string
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

_N_COMPONENTS = 100


class LSISimilarity(BaseSimilarity):
    """
    Latent Semantic Indexing (LSI) — también llamado LSA (Latent Semantic Analysis).
    Aplica Descomposición en Valores Singulares (SVD) sobre la matriz TF-IDF del corpus
    para capturar relaciones semánticas latentes entre términos y documentos.

    Pasos:
      1. Construir matriz TF-IDF M de tamaño (N_documentos × V_vocabulario)
      2. SVD: M ≈ U × Σ × Vᵀ  (reducir a k dimensiones)
      3. Proyectar documentos al espacio semántico reducido: D = U × Σ
      4. Similitud coseno en el espacio semántico
    """

    def __init__(self, n_components: int = _N_COMPONENTS) -> None:
        self._n_components = n_components
        self._vectorizer: TfidfVectorizer | None = None
        self._svd: TruncatedSVD | None = None
        self._corpus_matrix: np.ndarray | None = None

    @property
    def name(self) -> str:
        return "LSI / LSA (SVD semántico)"

    def fit(self, corpus: list[str]) -> "LSISimilarity":
        processed = [to_string(text) for text in corpus]
        n_components = min(self._n_components, len(processed) - 1)

        self._vectorizer = TfidfVectorizer()
        tfidf_matrix = self._vectorizer.fit_transform(processed)

        self._svd = TruncatedSVD(n_components=n_components, random_state=42)
        self._corpus_matrix = normalize(self._svd.fit_transform(tfidf_matrix))
        return self

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        if self._vectorizer is None or self._svd is None:
            self.fit([text_a, text_b])

        proc_a = to_string(text_a)
        proc_b = to_string(text_b)

        tfidf_vectors = self._vectorizer.transform([proc_a, proc_b])
        semantic_vectors = normalize(self._svd.transform(tfidf_vectors))

        vec_a = semantic_vectors[0]
        vec_b = semantic_vectors[1]
        score = round(float(np.dot(vec_a, vec_b)), 4)
        score = max(0.0, score)

        vocab_size = len(self._vectorizer.vocabulary_)
        k = self._svd.n_components
        variance = round(float(self._svd.explained_variance_ratio_.sum()) * 100, 2)

        steps = [
            f"1. Preprocesamiento: tokenización y eliminación de stopwords.",
            f"2. Vectorización TF-IDF: vocabulario de {vocab_size} términos.",
            f"3. SVD truncado: M ({vocab_size} términos) → espacio semántico de {k} dimensiones.",
            f"   Varianza explicada por las {k} dimensiones: {variance}%",
            f"   M ≈ U × Σ × Vᵀ  →  proyección: D = U × Σ (normalizada por fila)",
            f"4. Proyección de textos nuevos al espacio semántico: v = SVD.transform(tfidf(texto))",
            f"5. Similitud coseno en espacio semántico:",
            f"   cos(A, B) = A · B = {score}  (vectores ya normalizados → ||A||=||B||=1)",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

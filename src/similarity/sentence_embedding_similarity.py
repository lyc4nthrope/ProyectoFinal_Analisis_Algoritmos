import numpy as np
from sentence_transformers import SentenceTransformer

from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

_MODEL_NAME = "all-MiniLM-L6-v2"


class SentenceEmbeddingSimilarity(BaseSimilarity):
    """
    Similitud semántica mediante Sentence Embeddings (modelos de lenguaje preentrenados).
    Usa 'all-MiniLM-L6-v2': modelo transformer liviano entrenado en 1B+ pares de oraciones.
    Produce vectores densos de 384 dimensiones que capturan significado semántico profundo.
    Similitud: coseno entre los vectores de embedding.

    Optimización de corpus: fit() pre-codifica todos los documentos en un solo batch,
    almacenándolos en un dict {texto: embedding}. compute_pair() hace lookup O(1) en ese
    dict en lugar de re-codificar. compute_matrix() codifica todos los textos en un batch
    y calcula la matriz completa sin duplicar codificaciones.
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._corpus_embeddings: dict[str, np.ndarray] = {}

    @property
    def name(self) -> str:
        return f"Sentence Embeddings ({self._model_name})"

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def fit(self, corpus: list[str]) -> "SentenceEmbeddingSimilarity":
        """Pre-codifica el corpus completo en un solo batch: O(N) llamadas al encoder."""
        model = self._load_model()
        embeddings = model.encode(corpus, normalize_embeddings=True, show_progress_bar=False)
        self._corpus_embeddings = dict(zip(corpus, embeddings))
        return self

    def _get_embedding(self, text: str) -> np.ndarray:
        """Retorna embedding cacheado O(1) o codifica el texto bajo demanda."""
        if text in self._corpus_embeddings:
            return self._corpus_embeddings[text]
        return self._load_model().encode([text], normalize_embeddings=True)[0]

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        vec_a = self._get_embedding(text_a)
        vec_b = self._get_embedding(text_b)
        score = round(float(np.dot(vec_a, vec_b)), 4)
        score = max(0.0, score)

        steps = [
            f"1. Modelo: {self._model_name} — transformer preentrenado en pares de oraciones.",
            f"   Dimensiones del embedding: {len(vec_a)}",
            f"2. Codificación: cada texto es procesado por el transformer (o recuperado del cache).",
            f"   fit() pre-codifica el corpus completo en un batch → lookup O(1) por texto.",
            f"3. Normalización L2: ||embedding|| = 1 para ambos vectores.",
            f"   Permite usar producto punto directo como equivalente al coseno.",
            f"4. Similitud coseno = A · B = {score}",
            f"   (equivalente a cos(A,B) cuando ambos vectores están normalizados L2)",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        """
        Codifica todos los textos en un único batch y construye la matriz completa.
        Complejidad: O(N) codificaciones en lugar de O(N²) del método base.
        """
        embeddings = self._load_model().encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        n = len(texts)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                score = round(float(np.dot(embeddings[i], embeddings[j])), 4)
                score = max(0.0, score)
                matrix[i][j] = score
                matrix[j][i] = score
        return matrix

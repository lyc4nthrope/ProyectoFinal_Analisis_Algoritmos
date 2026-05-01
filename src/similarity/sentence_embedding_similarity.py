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
    """

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def name(self) -> str:
        return f"Sentence Embeddings ({self._model_name})"

    def _load_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        model = self._load_model()
        embeddings = model.encode([text_a, text_b], normalize_embeddings=True)

        vec_a = embeddings[0]
        vec_b = embeddings[1]
        score = round(float(np.dot(vec_a, vec_b)), 4)
        score = max(0.0, score)

        steps = [
            f"1. Modelo: {self._model_name} — transformer preentrenado en pares de oraciones.",
            f"   Dimensiones del embedding: {len(vec_a)}",
            f"2. Codificación: cada texto completo es procesado por el transformer.",
            f"   El token [CLS] final del encoder representa el significado semántico del texto.",
            f"3. Normalización L2: ||embedding|| = 1 para ambos vectores.",
            f"   Esto permite usar producto punto directo como similitud coseno.",
            f"4. Similitud coseno = A · B = {score}",
            f"   (equivalente a cos(A,B) cuando ambos vectores están normalizados)",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

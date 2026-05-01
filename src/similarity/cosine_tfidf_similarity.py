import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.processing.text_preprocessing import to_string
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult


class CosineTFIDFSimilarity(BaseSimilarity):
    """
    Similitud del coseno sobre vectores TF-IDF.
    TF(t, d)  = frecuencia del término t en el documento d
    IDF(t)    = log(N / df(t))  donde N = total de documentos, df = documentos con t
    TF-IDF(t, d) = TF(t, d) × IDF(t)
    cosine(A, B) = (A · B) / (||A|| × ||B||)
    Complejidad: O(V) donde V es el tamaño del vocabulario.
    """

    def __init__(self) -> None:
        self._vectorizer: TfidfVectorizer | None = None

    @property
    def name(self) -> str:
        return "Cosine TF-IDF"

    def fit(self, corpus: list[str]) -> "CosineTFIDFSimilarity":
        processed = [to_string(text) for text in corpus]
        self._vectorizer = TfidfVectorizer()
        self._vectorizer.fit(processed)
        return self

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        proc_a = to_string(text_a)
        proc_b = to_string(text_b)

        if self._vectorizer is None:
            raise RuntimeError(
                "CosineTFIDFSimilarity debe ser ajustado con fit() antes de llamar compute_pair()."
            )

        vectors = self._vectorizer.transform([proc_a, proc_b])
        score = round(float(cosine_similarity(vectors[0], vectors[1])[0][0]), 4)

        vec_a = vectors[0].toarray()[0]
        vec_b = vectors[1].toarray()[0]
        nonzero_a = int(np.count_nonzero(vec_a))
        nonzero_b = int(np.count_nonzero(vec_b))
        dot = float(np.dot(vec_a, vec_b))
        norm_a = float(np.linalg.norm(vec_a))
        norm_b = float(np.linalg.norm(vec_b))

        steps = [
            f"1. Preprocesamiento: tokenización y eliminación de stopwords.",
            f"2. Vectorización TF-IDF sobre vocabulario del corpus ({len(self._vectorizer.vocabulary_)} términos).",
            f"   Vector A: {nonzero_a} términos con peso > 0",
            f"   Vector B: {nonzero_b} términos con peso > 0",
            f"3. Producto punto A · B = {dot:.6f}",
            f"4. Norma euclidiana: ||A|| = {norm_a:.6f}, ||B|| = {norm_b:.6f}",
            f"5. cosine(A, B) = {dot:.6f} / ({norm_a:.6f} × {norm_b:.6f})",
            f"   = {dot:.6f} / {norm_a * norm_b:.6f} = {score}",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

# Importa numpy para cálculos vectoriales eficientes
import numpy as np
# Importa el vectorizador TF-IDF de scikit-learn para convertir texto en vectores
from sklearn.feature_extraction.text import TfidfVectorizer
# Importa la función de similitud coseno de scikit-learn
from sklearn.metrics.pairwise import cosine_similarity

# Importa la función que convierte texto a string de tokens normalizados
from src.processing.text_preprocessing import to_string
# Importa la clase base y la estructura de resultado
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

    COMPLEXITY_TIME = "O(V)"
    COMPLEXITY_SPACE = "O(V)"

    def __init__(self) -> None:
        # El vectorizador se inicializa en None; se crea al llamar fit()
        self._vectorizer: TfidfVectorizer | None = None

    @property
    def name(self) -> str:
        return "Cosine TF-IDF"

    def fit(self, corpus: list[str]) -> "CosineTFIDFSimilarity":
        # Preprocesa todos los documentos del corpus (tokeniza + elimina stopwords)
        processed = [to_string(text) for text in corpus]
        # Crea y entrena el vectorizador TF-IDF sobre el corpus completo
        # Esto aprende el vocabulario y los pesos IDF de cada término
        self._vectorizer = TfidfVectorizer()
        self._vectorizer.fit(processed)
        return self

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        # Preprocesa ambos textos con el mismo pipeline del corpus
        proc_a = to_string(text_a)
        proc_b = to_string(text_b)

        # El vectorizador debe haberse entrenado con fit() antes de usarlo
        if self._vectorizer is None:
            raise RuntimeError(
                "CosineTFIDFSimilarity debe ser ajustado con fit() antes de llamar compute_pair()."
            )

        # Transforma ambos textos al espacio vectorial TF-IDF entrenado
        vectors = self._vectorizer.transform([proc_a, proc_b])
        # Calcula la similitud coseno entre los dos vectores sparse
        score = round(float(cosine_similarity(vectors[0], vectors[1])[0][0]), 4)

        # Convierte los vectores sparse a densos para calcular métricas de la explicación
        vec_a = vectors[0].toarray()[0]
        vec_b = vectors[1].toarray()[0]
        nonzero_a = int(np.count_nonzero(vec_a))
        nonzero_b = int(np.count_nonzero(vec_b))
        dot = float(np.dot(vec_a, vec_b))
        norm_a = float(np.linalg.norm(vec_a))
        norm_b = float(np.linalg.norm(vec_b))

        # Genera la explicación matemática paso a paso
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

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        # Importación local para evitar dependencia circular al usar el override
        from sklearn.metrics.pairwise import cosine_similarity
        # Vectoriza todos los textos de una sola vez (más eficiente que de a pares)
        processed = [to_string(t) for t in texts]
        vectors = self._vectorizer.transform(processed)
        # Calcula la matriz de similitud coseno completa en una sola operación matricial
        matrix = cosine_similarity(vectors)
        return [[round(float(v), 4) for v in row] for row in matrix]

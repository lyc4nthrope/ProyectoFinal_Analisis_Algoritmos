# Importa numpy para operaciones matriciales (producto punto, normalización)
import numpy as np
# Importa TruncatedSVD para la descomposición en valores singulares (SVD reducida)
from sklearn.decomposition import TruncatedSVD
# Importa TfidfVectorizer para construir la matriz TF-IDF del corpus
from sklearn.feature_extraction.text import TfidfVectorizer
# Importa normalize para normalizar L2 los vectores semánticos
from sklearn.preprocessing import normalize

# Importa el preprocesador de texto
from src.processing.text_preprocessing import to_string
# Importa la clase base y la estructura de resultado
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

# Número de componentes semánticas latentes por defecto (dimensiones del espacio reducido)
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

    COMPLEXITY_TIME = "O(N·V·k)"
    COMPLEXITY_SPACE = "O(N·k)"

    def __init__(self, n_components: int = _N_COMPONENTS) -> None:
        # Número de dimensiones del espacio semántico latente
        self._n_components = n_components
        # Vectorizador TF-IDF que aprende el vocabulario del corpus
        self._vectorizer: TfidfVectorizer | None = None
        # Modelo SVD que aprende las k dimensiones semánticas
        self._svd: TruncatedSVD | None = None
        # Matriz del corpus proyectada al espacio semántico (N_docs × k)
        self._corpus_matrix: np.ndarray | None = None

    @property
    def name(self) -> str:
        return "LSI / LSA (SVD semántico)"

    def fit(self, corpus: list[str]) -> "LSISimilarity":
        # Preprocesa todos los documentos del corpus
        processed = [to_string(text) for text in corpus]
        # SVD no puede tener más componentes que documentos - 1
        n_components = min(self._n_components, len(processed) - 1)

        # Construye la matriz TF-IDF del corpus y aprende el vocabulario
        self._vectorizer = TfidfVectorizer()
        tfidf_matrix = self._vectorizer.fit_transform(processed)

        # Aplica SVD truncado para reducir a k dimensiones semánticas latentes
        # random_state=42 garantiza reproducibilidad
        self._svd = TruncatedSVD(n_components=n_components, random_state=42)
        # Proyecta el corpus al espacio semántico y normaliza cada fila a norma L2 = 1
        self._corpus_matrix = normalize(self._svd.fit_transform(tfidf_matrix))
        return self

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        # Si no se llamó fit(), entrena automáticamente con los dos textos
        if self._vectorizer is None or self._svd is None:
            self.fit([text_a, text_b])

        # Preprocesa los textos nuevos
        proc_a = to_string(text_a)
        proc_b = to_string(text_b)

        # Vectoriza los textos al espacio TF-IDF del corpus
        tfidf_vectors = self._vectorizer.transform([proc_a, proc_b])
        # Proyecta al espacio semántico y normaliza L2
        semantic_vectors = normalize(self._svd.transform(tfidf_vectors))

        vec_a = semantic_vectors[0]
        vec_b = semantic_vectors[1]
        # La similitud coseno de vectores normalizados L2 es igual al producto punto
        score = round(float(np.dot(vec_a, vec_b)), 4)
        # Recorta a 0 en caso de valores negativos por efectos numéricos del SVD
        score = max(0.0, score)

        # Estadísticas del modelo para la explicación
        vocab_size = len(self._vectorizer.vocabulary_)
        k = self._svd.n_components
        variance = round(float(self._svd.explained_variance_ratio_.sum()) * 100, 2)

        # Explicación matemática paso a paso del proceso LSI/LSA
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

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        # Vectoriza todos los textos a la vez (más eficiente que de a pares)
        processed = [to_string(t) for t in texts]
        tfidf = self._vectorizer.transform(processed)
        # Proyecta al espacio semántico y normaliza L2
        semantic = normalize(self._svd.transform(tfidf))
        # La matriz de similitud es el producto matricial: semantic @ semantic.T
        matrix = np.dot(semantic, semantic.T)
        # Recorta valores negativos y redondea
        return [[round(float(max(0.0, v)), 4) for v in row] for row in matrix]

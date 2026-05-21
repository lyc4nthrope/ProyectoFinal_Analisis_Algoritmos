import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False

from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

_MODEL_NAME = "all-MiniLM-L6-v2"


class SentenceEmbeddingSimilarity(BaseSimilarity):
    """
    Similitud semántica mediante Sentence Embeddings (modelos de lenguaje preentrenados).
    Usa 'all-MiniLM-L6-v2': modelo transformer liviano entrenado en 1B+ pares de oraciones.
    Produce vectores densos de 384 dimensiones que capturan significado semántico profundo.
    Similitud: coseno entre los vectores de embedding.

    Lazy loading: el modelo se descarga y el corpus se codifica en el primer
    compute_pair() o compute_matrix(), no en fit(). Esto evita bloquear la UI
    al crear el SimilarityAnalyzer.
    """

    COMPLEXITY_TIME = "O(N·d)"
    COMPLEXITY_SPACE = "O(N·d)"

    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._corpus_embeddings: dict[str, np.ndarray] = {}
        self._lazy_corpus: list[str] | None = None
        self._fallback_vectorizer: TfidfVectorizer | None = None
        self._fallback_reason: str | None = None

    @property
    def name(self) -> str:
        return f"Sentence Embeddings ({self._model_name})"

    def _load_model(self) -> "SentenceTransformer":
        if not _HAS_SENTENCE_TRANSFORMERS:
            raise RuntimeError("sentence-transformers no instalado — usando fallback TF-IDF")
        if self._model is None:
            self._model = SentenceTransformer(self._model_name, local_files_only=True)
        return self._model

    def _use_fallback(self, reason: Exception | str) -> None:
        if self._fallback_vectorizer is not None:
            return
        corpus = self._lazy_corpus or []
        texts = [text if text and text.strip() else "empty document" for text in corpus]
        if not texts:
            texts = ["empty document"]
        self._fallback_vectorizer = TfidfVectorizer(stop_words="english", norm="l2")
        matrix = self._fallback_vectorizer.fit_transform(texts).toarray()
        self._corpus_embeddings = {
            text: matrix[index] for index, text in enumerate(corpus)
        }
        self._lazy_corpus = None
        self._fallback_reason = str(reason)

    def _ensure_encoded(self) -> None:
        """Codifica el corpus completo en batch si no está ya cacheado (lazy)."""
        if self._corpus_embeddings:
            return
        if self._lazy_corpus is not None and len(self._lazy_corpus) > 0:
            try:
                model = self._load_model()
                embeddings = model.encode(
                    self._lazy_corpus,
                    normalize_embeddings=True,
                    show_progress_bar=False,
                )
                self._corpus_embeddings = dict(zip(self._lazy_corpus, embeddings))
                self._lazy_corpus = None  # liberar memoria
            except Exception as exc:
                self._use_fallback(exc)

    def fit(self, corpus: list[str]) -> "SentenceEmbeddingSimilarity":
        """Almacena el corpus para codificación diferida (lazy loading).
        El modelo NO se descarga acá — se descarga en el primer compute_pair()
        o compute_matrix(). Esto evita bloquear la UI al crear el analyzer."""
        self._lazy_corpus = corpus
        return self

    def _get_embedding(self, text: str) -> np.ndarray:
        """Retorna embedding cacheado O(1) o codifica el texto bajo demanda."""
        self._ensure_encoded()
        if text in self._corpus_embeddings:
            return self._corpus_embeddings[text]
        if self._fallback_vectorizer is not None:
            return self._fallback_vectorizer.transform([text]).toarray()[0]
        try:
            return self._load_model().encode([text], normalize_embeddings=True)[0]
        except Exception as exc:
            self._use_fallback(exc)
            return self._get_embedding(text)

    def _build_steps(self, vec_a: np.ndarray, score: float) -> list[str]:
        if self._fallback_vectorizer is not None:
            return [
                f"1. Modo offline: no hubo modelo local '{self._model_name}', se usa TF-IDF como respaldo.",
                f"   Motivo: {self._fallback_reason}",
                f"2. Vectorización: cada texto se transforma a un vector TF-IDF normalizado L2.",
                f"   Dimensiones del vector: {len(vec_a)}",
                f"3. Similitud coseno = A · B = {score}",
                f"   El respaldo mantiene puntajes comparables en rango [0, 1].",
            ]
        return [
            f"1. Modelo: {self._model_name} — transformer preentrenado en pares de oraciones.",
            f"   Dimensiones del embedding: {len(vec_a)}",
            f"2. Codificación: cada texto es procesado por el transformer (o recuperado del cache).",
            f"   fit() pre-codifica el corpus completo en un batch → lookup O(1) por texto.",
            f"3. Normalización L2: ||embedding|| = 1 para ambos vectores.",
            f"   Permite usar producto punto directo como equivalente al coseno.",
            f"4. Similitud coseno = A · B = {score}",
            f"   (equivalente a cos(A,B) cuando ambos vectores están normalizados L2)",
        ]

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        self._ensure_encoded()
        vec_a = self._get_embedding(text_a)
        vec_b = self._get_embedding(text_b)
        score = round(float(np.dot(vec_a, vec_b)), 4)
        score = max(0.0, score)
        return SimilarityResult(algorithm=self.name, score=score, steps=self._build_steps(vec_a, score))

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        """
        Codifica todos los textos en un único batch y construye la matriz completa.
        Complejidad: O(N) codificaciones en lugar de O(N²) del método base.
        """
        self._ensure_encoded()
        if self._fallback_vectorizer is not None:
            embeddings = self._fallback_vectorizer.transform(texts).toarray()
        else:
            try:
                embeddings = self._load_model().encode(
                    texts, normalize_embeddings=True, show_progress_bar=False,
                )
            except Exception as exc:
                self._use_fallback(exc)
                embeddings = self._fallback_vectorizer.transform(texts).toarray()
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

# Importa numpy para operaciones matriciales y producto punto
import numpy as np
# Importa TfidfVectorizer como alternativa cuando el modelo de embeddings no está disponible
from sklearn.feature_extraction.text import TfidfVectorizer

# Intenta importar SentenceTransformer; si no está instalado, activa el modo fallback TF-IDF
try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False

# Importa la clase base y la estructura de resultado
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

# Nombre del modelo preentrenado: transformer liviano de 384 dimensiones
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
        # Nombre del modelo de SentenceTransformers a cargar
        self._model_name = model_name
        # Instancia del modelo (None hasta la primera llamada, lazy loading)
        self._model: SentenceTransformer | None = None
        # Cache de embeddings: {texto: vector numpy} para evitar re-codificación
        self._corpus_embeddings: dict[str, np.ndarray] = {}
        # Corpus guardado para codificación diferida (se limpia después de codificar)
        self._lazy_corpus: list[str] | None = None
        # Vectorizador TF-IDF de respaldo cuando el modelo no está disponible offline
        self._fallback_vectorizer: TfidfVectorizer | None = None
        # Motivo por el que se activó el fallback (para mostrar en la explicación)
        self._fallback_reason: str | None = None

    @property
    def name(self) -> str:
        return f"Sentence Embeddings ({self._model_name})"

    def _load_model(self) -> "SentenceTransformer":
        # Falla rápido si la librería no está instalada
        if not _HAS_SENTENCE_TRANSFORMERS:
            raise RuntimeError("sentence-transformers no instalado — usando fallback TF-IDF")
        # Carga el modelo solo si no está ya en memoria
        if self._model is None:
            # local_files_only=True: solo usa el modelo si está cacheado localmente
            self._model = SentenceTransformer(self._model_name, local_files_only=True)
        return self._model

    def _use_fallback(self, reason: Exception | str) -> None:
        # Si ya hay un fallback activo, no lo reinicializa
        if self._fallback_vectorizer is not None:
            return
        # Usa el corpus guardado para entrenar el TF-IDF de respaldo
        corpus = self._lazy_corpus or []
        # Reemplaza textos vacíos con un texto placeholder para evitar errores
        texts = [text if text and text.strip() else "empty document" for text in corpus]
        if not texts:
            texts = ["empty document"]
        # Entrena el vectorizador TF-IDF normalizado L2 como alternativa al embedding
        self._fallback_vectorizer = TfidfVectorizer(stop_words="english", norm="l2")
        matrix = self._fallback_vectorizer.fit_transform(texts).toarray()
        # Construye el cache de embeddings con los vectores TF-IDF
        self._corpus_embeddings = {
            text: matrix[index] for index, text in enumerate(corpus)
        }
        # Libera el corpus ya no necesario
        self._lazy_corpus = None
        # Guarda el motivo del fallback para mostrarlo en la explicación
        self._fallback_reason = str(reason)

    def _ensure_encoded(self) -> None:
        """Codifica el corpus completo en batch si no está ya cacheado (lazy)."""
        # Si ya hay embeddings cacheados, no hace nada
        if self._corpus_embeddings:
            return
        if self._lazy_corpus is not None and len(self._lazy_corpus) > 0:
            try:
                model = self._load_model()
                # Codifica todo el corpus de una sola vez (batch encoding, más eficiente)
                embeddings = model.encode(
                    self._lazy_corpus,
                    normalize_embeddings=True,  # Normaliza L2 para usar producto punto como coseno
                    show_progress_bar=False,
                )
                # Guarda los embeddings en el cache asociando texto → vector
                self._corpus_embeddings = dict(zip(self._lazy_corpus, embeddings))
                self._lazy_corpus = None  # liberar memoria
            except Exception as exc:
                # Si el modelo no está disponible, activa el modo fallback TF-IDF
                self._use_fallback(exc)

    def fit(self, corpus: list[str]) -> "SentenceEmbeddingSimilarity":
        """Almacena el corpus para codificación diferida (lazy loading).
        El modelo NO se descarga acá — se descarga en el primer compute_pair()
        o compute_matrix(). Esto evita bloquear la UI al crear el analyzer."""
        # Guarda el corpus para codificarlo después en la primera petición real
        self._lazy_corpus = corpus
        return self

    def _get_embedding(self, text: str) -> np.ndarray:
        """Retorna embedding cacheado O(1) o codifica el texto bajo demanda."""
        # Asegura que el corpus ya esté codificado antes de buscar
        self._ensure_encoded()
        # Busca en el cache (textos ya procesados en fit())
        if text in self._corpus_embeddings:
            return self._corpus_embeddings[text]
        # Si el fallback está activo, usa TF-IDF para textos nuevos
        if self._fallback_vectorizer is not None:
            return self._fallback_vectorizer.transform([text]).toarray()[0]
        # Si el texto no está en el cache, lo codifica directamente con el modelo
        try:
            return self._load_model().encode([text], normalize_embeddings=True)[0]
        except Exception as exc:
            # Si falla, activa el fallback y reintenta
            self._use_fallback(exc)
            return self._get_embedding(text)

    def _build_steps(self, vec_a: np.ndarray, score: float) -> list[str]:
        # Si está en modo fallback, muestra la explicación del TF-IDF alternativo
        if self._fallback_vectorizer is not None:
            return [
                f"1. Modo offline: no hubo modelo local '{self._model_name}', se usa TF-IDF como respaldo.",
                f"   Motivo: {self._fallback_reason}",
                f"2. Vectorización: cada texto se transforma a un vector TF-IDF normalizado L2.",
                f"   Dimensiones del vector: {len(vec_a)}",
                f"3. Similitud coseno = A · B = {score}",
                f"   El respaldo mantiene puntajes comparables en rango [0, 1].",
            ]
        # Explicación para el modo normal con el modelo transformer
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
        # Asegura que el corpus esté codificado antes de comparar
        self._ensure_encoded()
        # Obtiene los embeddings de cada texto (desde el cache o codificando en el momento)
        vec_a = self._get_embedding(text_a)
        vec_b = self._get_embedding(text_b)
        # El producto punto de vectores normalizados L2 es igual al coseno
        score = round(float(np.dot(vec_a, vec_b)), 4)
        # Recorta a 0 para evitar valores negativos por efectos numéricos
        score = max(0.0, score)
        return SimilarityResult(algorithm=self.name, score=score, steps=self._build_steps(vec_a, score))

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        """
        Codifica todos los textos en un único batch y construye la matriz completa.
        Complejidad: O(N) codificaciones en lugar de O(N²) del método base.
        """
        # Asegura que el corpus esté codificado antes de calcular la matriz
        self._ensure_encoded()
        if self._fallback_vectorizer is not None:
            # Modo fallback: vectoriza todos los textos con TF-IDF
            embeddings = self._fallback_vectorizer.transform(texts).toarray()
        else:
            try:
                # Codifica todos los textos en un solo batch para máxima eficiencia
                embeddings = self._load_model().encode(
                    texts, normalize_embeddings=True, show_progress_bar=False,
                )
            except Exception as exc:
                # Si falla, activa el fallback y reintenta
                self._use_fallback(exc)
                embeddings = self._fallback_vectorizer.transform(texts).toarray()
        n = len(texts)
        # Construye la matriz N×N calculando el producto punto entre cada par
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0  # Un texto es idéntico a sí mismo
            for j in range(i + 1, n):
                score = round(float(np.dot(embeddings[i], embeddings[j])), 4)
                score = max(0.0, score)
                # La matriz es simétrica: M[i][j] = M[j][i]
                matrix[i][j] = score
                matrix[j][i] = score
        return matrix

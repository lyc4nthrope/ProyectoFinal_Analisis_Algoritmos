# Importa math para la función logaritmo (usada en el cálculo de IDF)
import math

# Importa la función de tokenización con eliminación de stopwords
from src.processing.text_preprocessing import tokenize
# Importa la clase base y la estructura de resultado
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

# Parámetro k1: controla la saturación de frecuencias de términos (valores típicos: 1.2–2.0)
_K1 = 1.5
# Parámetro b: controla la penalización por longitud de documento (0=sin penalización, 1=máxima)
_B = 0.75


class BM25Similarity(BaseSimilarity):
    """
    Similitud basada en Okapi BM25.
    BM25 es una función de ranking probabilística que extiende TF-IDF
    penalizando términos muy frecuentes y documentos muy largos.

    BM25(q, d) = Σ IDF(t) × [TF(t,d) × (k1+1)] / [TF(t,d) + k1×(1-b+b×|d|/avgdl)]

    Para similitud simétrica: promedia score(A→B) y score(B→A), normalizado al máximo del corpus.
    """

    COMPLEXITY_TIME = "O(N²·L)"
    COMPLEXITY_SPACE = "O(N + V)"

    def __init__(self) -> None:
        # Corpus tokenizado, guardado para calcular estadísticas (IDF, avgdl)
        self._corpus_tokens: list[list[str]] = []
        # Longitud promedio de documentos en el corpus (avgdl en la fórmula BM25)
        self._avg_dl: float = 0.0
        # Diccionario de pesos IDF para cada término del vocabulario
        self._idf: dict[str, float] = {}
        # Score máximo observado en el corpus, usado para normalizar a [0, 1]
        self._max_score: float = 1.0

    @property
    def name(self) -> str:
        return "BM25 (Okapi)"

    def fit(self, corpus: list[str]) -> "BM25Similarity":
        # Tokeniza todos los documentos del corpus
        self._corpus_tokens = [tokenize(doc) for doc in corpus]
        # Calcula la longitud promedio de documentos en tokens
        self._avg_dl = (
            sum(len(t) for t in self._corpus_tokens) / len(self._corpus_tokens)
            if self._corpus_tokens else 1.0
        )
        # Calcula los pesos IDF y la frecuencia de documentos para cada término
        self._idf, self._df = self._compute_idf(self._corpus_tokens)
        # Calcula el score máximo posible: BM25 de cada documento consigo mismo
        # solo usando términos que aparezcan en al menos 2 documentos (df >= 2)
        max_self = 0.0
        for tokens in self._corpus_tokens:
            filtered = [t for t in tokens if self._df.get(t, 0) >= 2]
            if filtered:
                score = self._bm25_score(filtered, filtered)
                if score > max_self:
                    max_self = score
        # Guarda el score máximo para normalizar; mínimo 1.0 para evitar división por cero
        self._max_score = max_self if max_self > 0 else 1.0
        return self

    def _compute_idf(self, tokenized_corpus: list[list[str]]) -> tuple[dict[str, float], dict[str, int]]:
        n = len(tokenized_corpus)
        # Cuenta en cuántos documentos aparece cada término (document frequency)
        df: dict[str, int] = {}
        for tokens in tokenized_corpus:
            for term in set(tokens):  # set() evita contar el mismo término dos veces por documento
                df[term] = df.get(term, 0) + 1
        # Fórmula IDF de BM25: log((N - df + 0.5) / (df + 0.5) + 1)
        # El +1 garantiza que IDF sea siempre positivo
        idf = {
            term: math.log((n - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }
        return idf, df

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        doc_len = len(doc_tokens)
        avg_dl = self._avg_dl if self._avg_dl > 0 else 1.0
        # Cuenta la frecuencia de cada término en el documento
        tf_map: dict[str, int] = {}
        for token in doc_tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        score = 0.0
        for term in query_tokens:
            # Si el término no tiene IDF calculado, se omite (no estaba en el corpus)
            if term not in self._idf:
                continue
            tf = tf_map.get(term, 0)
            # Numerador BM25: TF normalizado con saturación (k1+1)
            numerator = tf * (_K1 + 1)
            # Denominador BM25: penaliza documentos largos con el parámetro b
            denominator = tf + _K1 * (1 - _B + _B * doc_len / avg_dl)
            # Suma la contribución de este término al score total
            score += self._idf[term] * (numerator / denominator)
        return score

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        tokens_a = tokenize(text_a)
        tokens_b = tokenize(text_b)

        # Si no se llamó fit(), entrena automáticamente con los dos textos
        if not self._idf:
            self.fit([text_a, text_b])

        # Calcula BM25 en ambas direcciones (A como query sobre B, y B sobre A)
        score_ab = self._bm25_score(tokens_a, tokens_b)
        score_ba = self._bm25_score(tokens_b, tokens_a)
        # Promedia los dos scores para obtener una similitud simétrica
        raw_score = (score_ab + score_ba) / 2
        # Normaliza al rango [0, 1] usando el score máximo del corpus
        score = round(min(raw_score / self._max_score, 1.0), 4) if self._max_score > 0 else 0.0

        # Genera la explicación matemática paso a paso
        steps = [
            f"1. Preprocesamiento: tokenización con eliminación de stopwords.",
            f"   Tokens A ({len(tokens_a)}): {tokens_a[:6]}...",
            f"   Tokens B ({len(tokens_b)}): {tokens_b[:6]}...",
            f"2. Parámetros BM25: k1={_K1}, b={_B}, avgdl={self._avg_dl:.1f} palabras",
            f"3. BM25(A→B): A como query, B como documento = {score_ab:.4f}",
            "   Para cada término t en A: IDF(t) × [TF(t,B)×(k1+1)] / [TF(t,B) + k1×(1-b+b×|B|/avgdl)]",
            f"4. BM25(B→A): B como query, A como documento = {score_ba:.4f}",
            f"5. Score bidireccional = ({score_ab:.4f} + {score_ba:.4f}) / 2 = {raw_score:.4f}",
            f"6. Normalización sobre corpus: {raw_score:.4f} / {self._max_score:.4f} = {score}",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

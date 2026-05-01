import math

from src.processing.text_preprocessing import tokenize
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult

_K1 = 1.5
_B = 0.75


class BM25Similarity(BaseSimilarity):
    """
    Similitud basada en Okapi BM25.
    BM25 es una función de ranking probabilística que extiende TF-IDF
    penalizando términos muy frecuentes y documentos muy largos.

    BM25(q, d) = Σ IDF(t) × [TF(t,d) × (k1+1)] / [TF(t,d) + k1×(1-b+b×|d|/avgdl)]

    Para similitud simétrica: promedia score(A→B) y score(B→A), normalizado al máximo del corpus.
    """

    def __init__(self) -> None:
        self._corpus_tokens: list[list[str]] = []
        self._avg_dl: float = 0.0
        self._idf: dict[str, float] = {}
        self._max_score: float = 1.0

    @property
    def name(self) -> str:
        return "BM25 (Okapi)"

    def fit(self, corpus: list[str]) -> "BM25Similarity":
        self._corpus_tokens = [tokenize(doc) for doc in corpus]
        self._avg_dl = (
            sum(len(t) for t in self._corpus_tokens) / len(self._corpus_tokens)
            if self._corpus_tokens else 1.0
        )
        self._idf = self._compute_idf(self._corpus_tokens)
        all_scores = [
            self._bm25_score(t_a, t_b)
            for t_a in self._corpus_tokens
            for t_b in self._corpus_tokens
            if t_a is not t_b
        ]
        self._max_score = max(all_scores) if all_scores else 1.0
        return self

    def _compute_idf(self, tokenized_corpus: list[list[str]]) -> dict[str, float]:
        n = len(tokenized_corpus)
        df: dict[str, int] = {}
        for tokens in tokenized_corpus:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        return {
            term: math.log((n - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        doc_len = len(doc_tokens)
        avg_dl = self._avg_dl if self._avg_dl > 0 else 1.0
        tf_map: dict[str, int] = {}
        for token in doc_tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        score = 0.0
        for term in query_tokens:
            if term not in self._idf:
                continue
            tf = tf_map.get(term, 0)
            numerator = tf * (_K1 + 1)
            denominator = tf + _K1 * (1 - _B + _B * doc_len / avg_dl)
            score += self._idf[term] * (numerator / denominator)
        return score

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        tokens_a = tokenize(text_a)
        tokens_b = tokenize(text_b)

        if not self._idf:
            self.fit([text_a, text_b])

        score_ab = self._bm25_score(tokens_a, tokens_b)
        score_ba = self._bm25_score(tokens_b, tokens_a)
        raw_score = (score_ab + score_ba) / 2
        score = round(min(raw_score / self._max_score, 1.0), 4) if self._max_score > 0 else 0.0

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

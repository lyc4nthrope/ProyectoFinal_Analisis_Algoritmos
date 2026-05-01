from src.similarity.base_similarity import BaseSimilarity, SimilarityResult
from src.similarity.levenshtein_similarity import LevenshteinSimilarity
from src.similarity.jaccard_similarity import JaccardSimilarity
from src.similarity.cosine_tfidf_similarity import CosineTFIDFSimilarity
from src.similarity.bm25_similarity import BM25Similarity
from src.similarity.lsi_similarity import LSISimilarity
from src.similarity.sentence_embedding_similarity import SentenceEmbeddingSimilarity


def _build_algorithms(corpus: list[str]) -> list[BaseSimilarity]:
    algorithms: list[BaseSimilarity] = [
        LevenshteinSimilarity(),
        JaccardSimilarity(),
        CosineTFIDFSimilarity(),
        BM25Similarity(),
        LSISimilarity(),
        SentenceEmbeddingSimilarity(),
    ]
    for algo in algorithms:
        algo.fit(corpus)
    return algorithms


class SimilarityAnalyzer:
    def __init__(self, corpus: list[str]) -> None:
        self._algorithms = _build_algorithms(corpus)

    def compare(self, text_a: str, text_b: str) -> list[SimilarityResult]:
        return [algo.compute_pair(text_a, text_b) for algo in self._algorithms]

    def compare_matrix(self, texts: list[str]) -> dict[str, list[list[float]]]:
        return {algo.name: algo.compute_matrix(texts) for algo in self._algorithms}

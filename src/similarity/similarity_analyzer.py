import heapq
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.similarity.base_similarity import BaseSimilarity, SimilarityResult, CancelToken, ProgressCallback
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
        results: list[SimilarityResult] = []
        for algo in self._algorithms:
            t0 = time.time()
            result = algo.compute_pair(text_a, text_b)
            elapsed_ms = (time.time() - t0) * 1000
            result.time_ms = elapsed_ms
            result.complexity_time = getattr(algo, 'COMPLEXITY_TIME', '')
            result.complexity_space = getattr(algo, 'COMPLEXITY_SPACE', '')
            results.append(result)
        return results

    def compare_matrix(self, texts: list[str]) -> dict[str, list[list[float]]]:
        return {algo.name: algo.compute_matrix(texts) for algo in self._algorithms}

    def find_most_similar(
        self,
        text: str,
        corpus_texts: list[str],
        corpus_titles: list[str],
        k: int = 10,
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, list[SimilarityResult]]:
        results: dict[str, list[SimilarityResult]] = {}

        for algo in self._algorithms:
            if cancel_token and cancel_token.is_cancelled:
                break

            algo_name = algo.name
            if progress_callback:
                progress_callback(algo_name, "Buscando documentos similares...")

            t0 = time.time()

            heap: list[tuple[float, int]] = []

            for i, corpus_text in enumerate(corpus_texts):
                if cancel_token and cancel_token.is_cancelled:
                    break

                result = algo.compute_pair(text, corpus_text)

                if len(heap) < k:
                    heapq.heappush(heap, (result.score, i))
                elif result.score > heap[0][0]:
                    heapq.heapreplace(heap, (result.score, i))

            if cancel_token and cancel_token.is_cancelled:
                break

            top_k = sorted(heap, key=lambda x: -x[0])

            algo_results: list[SimilarityResult] = []
            for score, idx in top_k:
                corpus_result = algo.compute_pair(text, corpus_texts[idx])
                corpus_result.time_ms = (time.time() - t0) * 1000 / len(top_k)
                corpus_result.complexity_time = getattr(algo, 'COMPLEXITY_TIME', '')
                corpus_result.complexity_space = getattr(algo, 'COMPLEXITY_SPACE', '')
                corpus_result.title = corpus_titles[idx] if idx < len(corpus_titles) else ""
                algo_results.append(corpus_result)

            elapsed_ms = (time.time() - t0) * 1000
            results[algo_name] = algo_results

        return results

    def compare_all_async(
        self,
        text_a: str,
        text_b: str,
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> list[SimilarityResult]:
        results: list[SimilarityResult] = []

        for algo in self._algorithms:
            if cancel_token and cancel_token.is_cancelled:
                break

            algo_name = algo.name
            if progress_callback:
                progress_callback(algo_name, "Calculando...")

            t0 = time.time()
            result = algo.compute_pair(text_a, text_b)
            elapsed_ms = (time.time() - t0) * 1000

            result.time_ms = elapsed_ms
            result.complexity_time = getattr(algo, 'COMPLEXITY_TIME', '')
            result.complexity_space = getattr(algo, 'COMPLEXITY_SPACE', '')
            results.append(result)

        return results

    def compare_matrix_async(
        self,
        texts: list[str],
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, tuple[list[list[float]], float]]:
        results: dict[str, tuple[list[list[float]], float]] = {}

        for algo in self._algorithms:
            if cancel_token and cancel_token.is_cancelled:
                break

            algo_name = algo.name
            if progress_callback:
                progress_callback(algo_name, "Calculando matriz de similitud...")

            t0 = time.time()
            matrix = algo.compute_matrix(texts)
            elapsed_ms = (time.time() - t0) * 1000

            results[algo_name] = (matrix, elapsed_ms)

        return results

    def compute_matrix_single(
        self,
        algorithm_name: str,
        texts: list[str],
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[list[list[float]], float] | None:
        for algo in self._algorithms:
            if algo.name == algorithm_name:
                if cancel_token and cancel_token.is_cancelled:
                    return None
                if progress_callback:
                    progress_callback(algo.name, "Calculando matriz de similitud...")
                t0 = time.time()
                matrix = algo.compute_matrix(texts)
                elapsed_ms = (time.time() - t0) * 1000
                return (matrix, elapsed_ms)
        return None

    @property
    def algorithm_options(self) -> list[dict[str, str]]:
        return [
            {
                "name": algo.name,
                "complexity_time": getattr(algo, "COMPLEXITY_TIME", "?"),
                "complexity_space": getattr(algo, "COMPLEXITY_SPACE", "?"),
            }
            for algo in self._algorithms
        ]

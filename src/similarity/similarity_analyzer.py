# Importa heapq para mantener eficientemente los top-k resultados durante la búsqueda
import heapq
# Importa time para medir el tiempo de ejecución de cada algoritmo
import time

# Importa la clase base y los tipos de soporte para similitud
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult, CancelToken, ProgressCallback
# Importa cada uno de los 6 algoritmos de similitud implementados
from src.similarity.levenshtein_similarity import LevenshteinSimilarity
from src.similarity.jaccard_similarity import JaccardSimilarity
from src.similarity.cosine_tfidf_similarity import CosineTFIDFSimilarity
from src.similarity.bm25_similarity import BM25Similarity
from src.similarity.lsi_similarity import LSISimilarity
from src.similarity.sentence_embedding_similarity import SentenceEmbeddingSimilarity


def _build_algorithms(corpus: list[str]) -> list[BaseSimilarity]:
    # Instancia los 6 algoritmos en orden: 4 clásicos + 2 con IA
    algorithms: list[BaseSimilarity] = [
        LevenshteinSimilarity(),
        JaccardSimilarity(),
        CosineTFIDFSimilarity(),
        BM25Similarity(),
        LSISimilarity(),
        SentenceEmbeddingSimilarity(),
    ]
    # Entrena cada algoritmo con el corpus completo (fit registra estadísticas del corpus)
    for algo in algorithms:
        algo.fit(corpus)
    return algorithms


def _annotate(algo: BaseSimilarity, result: SimilarityResult, elapsed_ms: float) -> SimilarityResult:
    # Agrega el tiempo de ejecución medido al resultado
    result.time_ms = elapsed_ms
    # Agrega las complejidades teóricas del algoritmo al resultado (para mostrar en UI)
    result.complexity_time = getattr(algo, "COMPLEXITY_TIME", "")
    result.complexity_space = getattr(algo, "COMPLEXITY_SPACE", "")
    return result


class SimilarityAnalyzer:
    def __init__(self, corpus: list[str]) -> None:
        # Inicializa y entrena los 6 algoritmos con el corpus dado
        self._algorithms = _build_algorithms(corpus)

    def compare(self, text_a: str, text_b: str) -> list[SimilarityResult]:
        # Ejecuta los 6 algoritmos sobre el par de textos y mide el tiempo de cada uno
        results: list[SimilarityResult] = []
        for algo in self._algorithms:
            t0 = time.time()
            result = algo.compute_pair(text_a, text_b)
            # Anota el tiempo transcurrido en milisegundos
            results.append(_annotate(algo, result, (time.time() - t0) * 1000))
        return results

    def find_most_similar(
        self,
        text: str,
        corpus_texts: list[str],
        corpus_titles: list[str],
        k: int = 10,
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> dict[str, list[SimilarityResult]]:
        # Diccionario de resultados: nombre_algoritmo → lista de top-k artículos más similares
        results: dict[str, list[SimilarityResult]] = {}

        for algo in self._algorithms:
            # Verifica si el usuario canceló la operación antes de cada algoritmo
            if cancel_token and cancel_token.is_cancelled:
                break

            # Notifica el progreso a la interfaz (si hay callback)
            if progress_callback:
                progress_callback(algo.name, "Buscando documentos similares...")

            t0 = time.time()
            # Heap mínimo para mantener los top-k artículos más similares eficientemente
            heap: list[tuple[float, int]] = []
            # Cache de resultados por índice para evitar recalcular al final
            result_cache: dict[int, SimilarityResult] = {}

            for i, corpus_text in enumerate(corpus_texts):
                # Verifica cancelación dentro del bucle interno
                if cancel_token and cancel_token.is_cancelled:
                    break

                # Calcula la similitud entre el texto de consulta y el artículo i
                result = algo.compute_pair(text, corpus_text)
                result_cache[i] = result

                # Mantiene el heap de tamaño máximo k con los mejores scores
                if len(heap) < k:
                    heapq.heappush(heap, (result.score, i))
                elif result.score > heap[0][0]:
                    # Si el nuevo score supera al mínimo del heap, lo reemplaza
                    heapq.heapreplace(heap, (result.score, i))

            if cancel_token and cancel_token.is_cancelled:
                break

            elapsed_ms = (time.time() - t0) * 1000
            # Ordena los top-k de mayor a menor score
            top_k = sorted(heap, key=lambda x: -x[0])

            algo_results: list[SimilarityResult] = []
            for _score, idx in top_k:
                r = result_cache[idx]
                # Asocia el título del artículo al resultado para mostrarlo en la UI
                r.title = corpus_titles[idx] if idx < len(corpus_titles) else ""
                algo_results.append(_annotate(algo, r, elapsed_ms / max(len(top_k), 1)))

            results[algo.name] = algo_results

        return results

    def compute_matrix_single(
        self,
        algorithm_name: str,
        texts: list[str],
        cancel_token: CancelToken | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> tuple[list[list[float]], float] | None:
        # Busca el algoritmo por nombre entre los 6 disponibles
        for algo in self._algorithms:
            if algo.name == algorithm_name:
                # Verifica cancelación antes de iniciar el cálculo
                if cancel_token and cancel_token.is_cancelled:
                    return None
                if progress_callback:
                    progress_callback(algo.name, "Calculando matriz de similitud...")
                t0 = time.time()
                # Calcula la matriz completa N×N usando el override del algoritmo
                matrix = algo.compute_matrix(texts)
                # Retorna la matriz y el tiempo en milisegundos
                return (matrix, (time.time() - t0) * 1000)
        # Si el nombre no se encontró, retorna None
        return None

    @property
    def algorithm_options(self) -> list[dict[str, str]]:
        # Retorna la información de cada algoritmo para poblar los selectores de la UI
        return [
            {
                "name": algo.name,
                "complexity_time": getattr(algo, "COMPLEXITY_TIME", "?"),
                "complexity_space": getattr(algo, "COMPLEXITY_SPACE", "?"),
            }
            for algo in self._algorithms
        ]

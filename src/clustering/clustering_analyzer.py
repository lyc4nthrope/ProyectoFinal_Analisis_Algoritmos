from matplotlib.figure import Figure

from src.clustering.vectorizer import build_matrix, CorpusMatrix
from src.clustering.hierarchical import HierarchicalClustering, ClusteringResult, LINKAGE_METHODS
from src.clustering.dendrogram import build_dendrogram_figure


class ClusteringAnalyzer:
    def __init__(self, abstracts: list[str], titles: list[str]) -> None:
        self._corpus: CorpusMatrix = build_matrix(abstracts, titles)
        self._results: dict[str, ClusteringResult] | None = None

    def run_all(self) -> dict[str, ClusteringResult]:
        if self._results is None:
            self._results = {
                method: HierarchicalClustering(method).fit(self._corpus.matrix)
                for method in LINKAGE_METHODS
            }
        return self._results

    def best_method(self) -> ClusteringResult:
        return max(self.run_all().values(), key=lambda r: r.cophenetic_correlation)

    def get_dendrogram_figure(self, method: str) -> Figure:
        results = self.run_all()
        if method not in results:
            raise ValueError(f"Método '{method}' no encontrado. Opciones: {list(results.keys())}")
        return build_dendrogram_figure(results[method], self._corpus.labels)

    @property
    def preprocessing_steps(self) -> list[str]:
        return self._corpus.steps

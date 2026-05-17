import time
from collections import Counter

from matplotlib.figure import Figure
from scipy.cluster.hierarchy import fcluster
from scipy.spatial.distance import pdist
from sklearn.cluster import MiniBatchKMeans

from src.clustering.vectorizer import build_matrix, CorpusMatrix
from src.clustering.hierarchical import HierarchicalClustering, ClusteringResult, LINKAGE_METHODS
from src.clustering.dendrogram import build_dendrogram_figure

# Umbral: sobre 5.000 docs usamos two-tier (K-Means + jerárquico sobre centroides).
# Debajo usamos jerárquico completo sobre toda la matriz.
TWO_TIER_THRESHOLD = 5_000
MAX_CLUSTERS = 500


class ClusteringAnalyzer:
    def __init__(self, abstracts: list[str], titles: list[str]) -> None:
        self._corpus: CorpusMatrix = build_matrix(abstracts, titles)
        self._titles: list[str] = titles
        self._results: dict[str, ClusteringResult] | None = None
        self._timing: list[str] = []
        self._dendrogram_labels: list[str] = []
        self._strategy: str = ""
        self._cluster_assignments: list[int] | None = None
        self._max_cluster_id: int = 0

    # ── Estrategia principal ──────────────────────────────────────────

    def run_all(self, progress_callback=None) -> dict[str, ClusteringResult]:
        if self._results is not None:
            return self._results

        self._timing = []
        n = self._corpus.n_docs

        if n > TWO_TIER_THRESHOLD:
            return self._run_all_two_tier(n, progress_callback)
        return self._run_all_full(n, progress_callback)

    # ── Estrategia 1: Full hierarchical (≤ 5.000 docs) ────────────────

    def _run_all_full(self, n: int, progress_callback) -> dict[str, ClusteringResult]:
        self._strategy = "full"
        self._dendrogram_labels = self._corpus.labels

        t0 = time.time()
        dist = pdist(self._corpus.matrix, metric="euclidean")
        self._timing.append(f"Matriz de distancias ({n} docs): {time.time() - t0:.1f}s")

        if progress_callback:
            progress_callback("Calculando distancias entre documentos...")

        self._results = {}
        for i, method in enumerate(LINKAGE_METHODS):
            name = LINKAGE_METHODS[method]
            t0 = time.time()
            if progress_callback:
                progress_callback(f"Agrupando con {name} ({i + 1}/{len(LINKAGE_METHODS)})...")

            self._results[method] = HierarchicalClustering(method).fit(
                self._corpus.matrix, precomputed_dist=dist,
            )
            self._timing.append(f"{name}: {time.time() - t0:.1f}s")

        # Asignaciones planas desde el mejor método (máx 500 clusters)
        k = min(n, MAX_CLUSTERS)
        best_key = max(self._results, key=lambda m: self._results[m].cophenetic_correlation)
        self._cluster_assignments = fcluster(
            self._results[best_key].linkage_matrix, k, criterion="maxclust",
        ).tolist()
        self._max_cluster_id = max(self._cluster_assignments) if self._cluster_assignments else 0

        total = sum(float(t.split(": ")[-1].replace("s", "")) for t in self._timing)
        self._timing.append(f"Total: {total:.1f}s")
        return self._results

    # ── Estrategia 2: Two-tier (> 5.000 docs) ─────────────────────────

    def _run_all_two_tier(self, n: int, progress_callback) -> dict[str, ClusteringResult]:
        self._strategy = "two-tier"
        matrix = self._corpus.matrix
        k = min(n, MAX_CLUSTERS)

        # Fase 1: K-Means
        t0 = time.time()
        if progress_callback:
            progress_callback(f"Fase 1: agrupando {n:,} docs en {k} clusters con K-Means...")

        kmeans = MiniBatchKMeans(
            n_clusters=k, random_state=42,
            batch_size=min(1024, n),
        )
        assignments = kmeans.fit_predict(matrix)
        centroids = kmeans.cluster_centers_
        counts = Counter(assignments)
        self._cluster_assignments = assignments.tolist()
        self._max_cluster_id = max(self._cluster_assignments) if self._cluster_assignments else 0
        self._timing.append(f"K-Means ({n:,} → {k} clusters): {time.time() - t0:.1f}s")

        # Etiquetas del dendrograma: "Cluster #N (M docs)"
        self._dendrogram_labels = [
            f"#{i} ({counts.get(i, 0)} docs)" for i in range(k)
        ]

        # Fase 2: Matriz de distancias entre centroides
        t0 = time.time()
        dist = pdist(centroids, metric="euclidean")
        self._timing.append(f"Matriz de distancias ({k} centroides): {time.time() - t0:.1f}s")
        if progress_callback:
            progress_callback(f"Fase 2: distancias entre {k} centroides calculadas...")

        # Fase 3: Hierarchical sobre centroides
        self._results = {}
        for i, method in enumerate(LINKAGE_METHODS):
            name = LINKAGE_METHODS[method]
            t0 = time.time()
            if progress_callback:
                progress_callback(f"Fase 3: agrupando centroides con {name} ({i + 1}/{len(LINKAGE_METHODS)})...")

            self._results[method] = HierarchicalClustering(method).fit(
                centroids, precomputed_dist=dist,
            )
            self._timing.append(f"{name}: {time.time() - t0:.1f}s")

            # Steps cuentan la estrategia two-tier
            top_clusters = sorted(counts.items(), key=lambda x: -x[1])[:20]
            self._results[method].steps = [
                f"Estrategia two-tier para {n:,} documentos.",
                f"Fase 1 — K-Means: {n:,} docs → {k} clusters.",
                f"Fase 2 — {name}: clustering jerárquico sobre {k} centroides.",
                f"",
                f"Distribución de los {k} clusters (top 20 por tamaño):",
            ] + [
                f"  Cluster #{cid}: {cnt} documentos" for cid, cnt in top_clusters
            ]

        total = sum(float(t.split(": ")[-1].replace("s", "")) for t in self._timing)
        self._timing.append(f"Total: {total:.1f}s")
        return self._results

    # ── Acceso a documentos por cluster ───────────────────────────────

    def get_cluster_doc_indices(self, cluster_id: int) -> list[int]:
        """Devuelve los índices de los documentos que pertenecen al cluster dado."""
        if self._cluster_assignments is None:
            return []
        return [i for i, c in enumerate(self._cluster_assignments) if c == cluster_id]

    @property
    def cluster_assignments(self) -> list[int] | None:
        return self._cluster_assignments

    @property
    def cluster_counts(self) -> dict[int, int]:
        """Devuelve {cluster_id: cantidad_de_docs} para cada cluster."""
        if self._cluster_assignments is None:
            return {}
        return dict(Counter(self._cluster_assignments))

    @property
    def cluster_ids(self) -> list[int]:
        """IDs de cluster ordenados."""
        if self._cluster_assignments is None:
            return []
        return sorted(set(self._cluster_assignments))

    # ── Propiedades públicas ──────────────────────────────────────────

    def best_method(self) -> ClusteringResult:
        return max(self.run_all().values(), key=lambda r: r.cophenetic_correlation)

    def get_dendrogram_figure(self, method: str) -> Figure:
        results = self.run_all()
        if method not in results:
            raise ValueError(f"Método '{method}' no encontrado. Opciones: {list(results.keys())}")
        return build_dendrogram_figure(results[method], self._dendrogram_labels)

    @property
    def preprocessing_steps(self) -> list[str]:
        return self._corpus.steps

    @property
    def timing(self) -> list[str]:
        return self._timing

    @property
    def strategy(self) -> str:
        """'full' si se usó jerárquico directo, 'two-tier' si K-Means + jerárquico."""
        return self._strategy

    @property
    def n_clusters(self) -> int:
        """Cantidad de clusters/hojas del dendrograma."""
        return len(self._dendrogram_labels)

    @property
    def n_documents(self) -> int:
        return self._corpus.n_docs

    def get_titles_for_indices(self, indices: list[int]) -> list[str]:
        return [self._titles[i] for i in indices]

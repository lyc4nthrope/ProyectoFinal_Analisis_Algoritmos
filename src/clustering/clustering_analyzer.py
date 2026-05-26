# Importa time para medir el tiempo de ejecución de cada etapa
import time
# Importa Counter para contar documentos por cluster
from collections import Counter

# Importa Figure de matplotlib para el tipo de retorno de get_dendrogram_figure
from matplotlib.figure import Figure
# Importa fcluster para convertir la linkage matrix en asignaciones planas de cluster
from scipy.cluster.hierarchy import fcluster
# Importa pdist para calcular la matriz de distancias entre documentos
from scipy.spatial.distance import pdist
# Importa MiniBatchKMeans para la fase 1 del algoritmo two-tier (corpus grandes)
from sklearn.cluster import MiniBatchKMeans

# Importa la función que construye la matriz TF-IDF del corpus
from src.clustering.vectorizer import build_matrix, CorpusMatrix
# Importa el algoritmo de clustering jerárquico y sus tipos
from src.clustering.hierarchical import HierarchicalClustering, ClusteringResult, LINKAGE_METHODS
# Importa la función que genera la figura del dendrograma
from src.clustering.dendrogram import build_dendrogram_figure

# Umbral: sobre 5.000 docs usamos two-tier (K-Means + jerárquico sobre centroides).
# Debajo usamos jerárquico completo sobre toda la matriz.
TWO_TIER_THRESHOLD = 5_000
MAX_CLUSTERS = 500  # Número máximo de clusters en el dendrograma


class ClusteringAnalyzer:
    def __init__(self, abstracts: list[str], titles: list[str]) -> None:
        # Vectoriza el corpus: tokeniza, TF-IDF, SVD, normalización L2
        self._corpus: CorpusMatrix = build_matrix(abstracts, titles)
        self._titles: list[str] = titles
        # Cache de resultados: se calcula una vez y se reutiliza
        self._results: dict[str, ClusteringResult] | None = None
        # Registro de tiempos de ejecución de cada etapa
        self._timing: list[str] = []
        # Etiquetas que se muestran en el dendrograma
        self._dendrogram_labels: list[str] = []
        # Estrategia usada: "full" o "two-tier"
        self._strategy: str = ""
        # Asignación de cada documento a un cluster (lista de IDs)
        self._cluster_assignments: list[int] | None = None
        # ID máximo de cluster (para validaciones)
        self._max_cluster_id: int = 0

    # ── Estrategia principal ──────────────────────────────────────────

    def run_all(self, progress_callback=None) -> dict[str, ClusteringResult]:
        # Si ya se calculó, retorna el cache sin recalcular
        if self._results is not None:
            return self._results

        self._timing = []
        n = self._corpus.n_docs

        # Selecciona la estrategia según el tamaño del corpus
        if n > TWO_TIER_THRESHOLD:
            return self._run_all_two_tier(n, progress_callback)
        return self._run_all_full(n, progress_callback)

    # ── Estrategia 1: Full hierarchical (≤ 5.000 docs) ────────────────

    def _run_all_full(self, n: int, progress_callback) -> dict[str, ClusteringResult]:
        self._strategy = "full"
        # En modo full, las etiquetas del dendrograma son los títulos de los documentos
        self._dendrogram_labels = self._corpus.labels

        t0 = time.time()
        # Calcula la matriz de distancias euclidianas entre todos los documentos (pdist = triangular)
        dist = pdist(self._corpus.matrix, metric="euclidean")
        self._timing.append(f"Matriz de distancias ({n} docs): {time.time() - t0:.1f}s")

        if progress_callback:
            progress_callback("Calculando distancias entre documentos...")

        self._results = {}
        # Ejecuta los 3 métodos de enlace sobre la misma matriz de distancias
        for i, method in enumerate(LINKAGE_METHODS):
            name = LINKAGE_METHODS[method]
            t0 = time.time()
            if progress_callback:
                progress_callback(f"Agrupando con {name} ({i + 1}/{len(LINKAGE_METHODS)})...")

            # Pasa la matriz de distancias pre-calculada para evitar calcularla de nuevo
            self._results[method] = HierarchicalClustering(method).fit(
                self._corpus.matrix, precomputed_dist=dist,
            )
            self._timing.append(f"{name}: {time.time() - t0:.1f}s")

        # Genera asignaciones planas usando el mejor método (máx 500 clusters)
        k = min(n, MAX_CLUSTERS)
        best_key = max(self._results, key=lambda m: self._results[m].cophenetic_correlation)
        # fcluster convierte la linkage matrix en una lista de asignaciones de cluster por documento
        self._cluster_assignments = fcluster(
            self._results[best_key].linkage_matrix, k, criterion="maxclust",
        ).tolist()
        self._max_cluster_id = max(self._cluster_assignments) if self._cluster_assignments else 0

        # Calcula el tiempo total sumando todos los tiempos registrados
        total = sum(float(t.split(": ")[-1].replace("s", "")) for t in self._timing)
        self._timing.append(f"Total: {total:.1f}s")
        return self._results

    # ── Estrategia 2: Two-tier (> 5.000 docs) ─────────────────────────

    def _run_all_two_tier(self, n: int, progress_callback) -> dict[str, ClusteringResult]:
        self._strategy = "two-tier"
        matrix = self._corpus.matrix
        k = min(n, MAX_CLUSTERS)

        # Fase 1: K-Means — agrupa los N documentos en k clusters de forma escalable
        t0 = time.time()
        if progress_callback:
            progress_callback(f"Fase 1: agrupando {n:,} docs en {k} clusters con K-Means...")

        # MiniBatchKMeans es más rápido que KMeans para corpus muy grandes
        kmeans = MiniBatchKMeans(
            n_clusters=k, random_state=42,
            batch_size=min(1024, n),  # Procesa en lotes de máximo 1024 documentos
        )
        assignments = kmeans.fit_predict(matrix)
        centroids = kmeans.cluster_centers_   # Un centroide por cluster
        counts = Counter(assignments)          # Cuántos documentos hay en cada cluster
        self._cluster_assignments = assignments.tolist()
        self._max_cluster_id = max(self._cluster_assignments) if self._cluster_assignments else 0
        self._timing.append(f"K-Means ({n:,} → {k} clusters): {time.time() - t0:.1f}s")

        # Etiquetas del dendrograma: "Cluster #N (M docs)" en lugar de títulos individuales
        self._dendrogram_labels = [
            f"#{i} ({counts.get(i, 0)} docs)" for i in range(k)
        ]

        # Fase 2: Calcula distancias entre los k centroides (mucho más pequeño que N documentos)
        t0 = time.time()
        dist = pdist(centroids, metric="euclidean")
        self._timing.append(f"Matriz de distancias ({k} centroides): {time.time() - t0:.1f}s")
        if progress_callback:
            progress_callback(f"Fase 2: distancias entre {k} centroides calculadas...")

        # Fase 3: Clustering jerárquico sobre los k centroides (no sobre los N documentos)
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

            # Sobreescribe los steps para reflejar la estrategia two-tier en la explicación
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
        # Filtra los índices donde la asignación de cluster coincide con el ID solicitado
        return [i for i, c in enumerate(self._cluster_assignments) if c == cluster_id]

    @property
    def cluster_assignments(self) -> list[int] | None:
        # Lista de IDs de cluster para cada documento en el orden original del corpus
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
        # Retorna el método con la mayor correlación cofenética (mejor calidad de clustering)
        return max(self.run_all().values(), key=lambda r: r.cophenetic_correlation)

    def get_dendrogram_figure(self, method: str) -> Figure:
        results = self.run_all()
        if method not in results:
            raise ValueError(f"Método '{method}' no encontrado. Opciones: {list(results.keys())}")
        # Genera el dendrograma matplotlib con las etiquetas configuradas por la estrategia
        return build_dendrogram_figure(results[method], self._dendrogram_labels)

    @property
    def preprocessing_steps(self) -> list[str]:
        # Pasos del preprocesamiento del corpus para mostrar en la interfaz
        return self._corpus.steps

    @property
    def timing(self) -> list[str]:
        # Registro de tiempos de ejecución de cada etapa del clustering
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
        # Número total de documentos en el corpus
        return self._corpus.n_docs

    def get_titles_for_indices(self, indices: list[int]) -> list[str]:
        # Retorna los títulos de los documentos en las posiciones dadas
        return [self._titles[i] for i in indices]

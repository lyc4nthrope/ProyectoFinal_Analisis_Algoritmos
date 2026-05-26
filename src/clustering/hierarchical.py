# Importa dataclass y field para definir la estructura del resultado de clustering
from dataclasses import dataclass, field

# Importa numpy para el manejo de la matriz de enlace (linkage matrix)
import numpy as np
# Importa las funciones de clustering jerárquico de scipy
from scipy.cluster.hierarchy import cophenet, linkage
# Importa pdist para calcular la matriz de distancias entre documentos
from scipy.spatial.distance import pdist


# Diccionario que mapea clave técnica → nombre descriptivo de cada método de enlace
LINKAGE_METHODS: dict[str, str] = {
    "single": "Single Linkage (enlace mínimo)",
    "complete": "Complete Linkage (enlace máximo)",
    "ward": "Ward (mínima varianza)",
}

# Descripción matemática de cada método para incluir en la explicación paso a paso
_METHOD_DESCRIPTIONS: dict[str, list[str]] = {
    "single": [
        "Criterio de fusión: distancia MÍNIMA entre cualquier par de puntos de dos clusters.",
        "d(A∪B, C) = min{ d(a, c) : a ∈ A, c ∈ C }",
        "Tiende a producir clusters alargados ('efecto cadena').",
        "Sensible a valores atípicos (outliers).",
    ],
    "complete": [
        "Criterio de fusión: distancia MÁXIMA entre cualquier par de puntos de dos clusters.",
        "d(A∪B, C) = max{ d(a, c) : a ∈ A, c ∈ C }",
        "Produce clusters más compactos y esféricos que Single.",
        "Menos sensible a outliers, pero puede romper clusters grandes.",
    ],
    "ward": [
        "Criterio de fusión: minimiza el incremento de varianza intra-cluster al unir dos clusters.",
        "Δ(A, B) = (nA·nB)/(nA+nB) · ||μA − μB||²",
        "  donde nA, nB = tamaño de cada cluster, μA, μB = centroides.",
        "Produce clusters balanceados y compactos. Generalmente el mejor para texto.",
        "Requiere distancia euclidiana (compatible con vectores TF-IDF normalizados L2).",
    ],
}


# Estructura que guarda el resultado completo del clustering jerárquico para un método
@dataclass
class ClusteringResult:
    method_key: str              # Clave técnica del método (ej: "ward")
    method_name: str             # Nombre descriptivo (ej: "Ward (mínima varianza)")
    linkage_matrix: np.ndarray   # Matriz de enlace scipy: [cluster_a, cluster_b, distancia, tamaño]
    cophenetic_correlation: float # Correlación cofenética: mide la calidad del clustering [0, 1]
    steps: list[str] = field(default_factory=list)  # Explicación del algoritmo para la interfaz


class HierarchicalClustering:
    def __init__(self, method: str) -> None:
        # Valida que el método sea uno de los tres implementados
        if method not in LINKAGE_METHODS:
            raise ValueError(f"Método inválido '{method}'. Opciones: {list(LINKAGE_METHODS.keys())}")
        self._method = method
        self._method_name = LINKAGE_METHODS[method]

    def fit(self, matrix: np.ndarray, precomputed_dist: np.ndarray | None = None) -> ClusteringResult:
        if precomputed_dist is not None:
            # Si ya se calculó la matriz de distancias externamente, la reutiliza (más eficiente)
            Z = linkage(precomputed_dist, method=self._method)
            d = precomputed_dist
        else:
            # Calcula linkage y distancias desde la matriz de documentos
            Z = linkage(matrix, method=self._method, metric="euclidean")
            d = pdist(matrix, metric="euclidean")

        # Calcula la correlación cofenética: qué tan bien preserva el dendrograma las distancias originales
        c = round(float(cophenet(Z, d)[0]), 4)

        return ClusteringResult(
            method_key=self._method,
            method_name=self._method_name,
            linkage_matrix=Z,
            cophenetic_correlation=c,
            steps=self._build_steps(matrix, Z, c),
        )

    def _build_steps(self, matrix: np.ndarray, Z: np.ndarray, c: float) -> list[str]:
        n = len(matrix)
        n_merges = len(Z)  # En clustering jerárquico: n-1 fusiones para n documentos

        # Encabezado con el nombre del algoritmo y descripción de la entrada
        steps = [
            f"Algoritmo: {self._method_name}",
            f"",
            f"Entrada: matriz {n} documentos × {matrix.shape[1]} características (TF-IDF normalizado L2).",
            f"",
            "Descripción del método:",
        ]
        # Agrega la descripción matemática específica del método de enlace
        for line in _METHOD_DESCRIPTIONS[self._method]:
            steps.append(f"  {line}")

        # Describe el proceso general de clustering aglomerativo bottom-up
        steps += [
            f"",
            f"Proceso de agrupamiento jerárquico aglomerativo (bottom-up):",
            f"  1. Inicialización: cada documento es su propio cluster → {n} clusters.",
            f"  2. Iteración: se fusionan los 2 clusters más cercanos según el criterio del método.",
            f"  3. Se repite hasta tener 1 cluster. Total de fusiones: {n_merges}.",
            f"",
            f"Primeras 3 fusiones (Z[i] = [cluster_a, cluster_b, distancia, tamaño]):",
        ]
        # Muestra las primeras 3 fusiones de la matriz de enlace para ilustrar el proceso
        for i in range(min(3, n_merges)):
            a, b, d, s = Z[i]
            steps.append(f"  Fusión {i+1}: doc_{int(a)} + doc_{int(b)} → distancia={d:.4f}, cluster_size={int(s)}")

        # Explica la correlación cofenética y cómo interpretarla
        steps += [
            f"",
            f"Correlación cofenética: {round(c, 4)}",
            f"  Mide qué tan bien preserva el dendrograma las distancias originales.",
            f"  Rango [0, 1]. Valores > 0.75 indican agrupamiento coherente.",
        ]

        return steps

from dataclasses import dataclass, field

import numpy as np
from scipy.cluster.hierarchy import cophenet, linkage
from scipy.spatial.distance import pdist


LINKAGE_METHODS: dict[str, str] = {
    "single": "Single Linkage (enlace mínimo)",
    "complete": "Complete Linkage (enlace máximo)",
    "ward": "Ward (mínima varianza)",
}

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


@dataclass
class ClusteringResult:
    method_key: str
    method_name: str
    linkage_matrix: np.ndarray
    cophenetic_correlation: float
    steps: list[str] = field(default_factory=list)


class HierarchicalClustering:
    def __init__(self, method: str) -> None:
        if method not in LINKAGE_METHODS:
            raise ValueError(f"Método inválido '{method}'. Opciones: {list(LINKAGE_METHODS.keys())}")
        self._method = method
        self._method_name = LINKAGE_METHODS[method]

    def fit(self, matrix: np.ndarray, precomputed_dist: np.ndarray | None = None) -> ClusteringResult:
        if precomputed_dist is not None:
            Z = linkage(precomputed_dist, method=self._method)
            d = precomputed_dist
        else:
            Z = linkage(matrix, method=self._method, metric="euclidean")
            d = pdist(matrix, metric="euclidean")

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
        n_merges = len(Z)

        steps = [
            f"Algoritmo: {self._method_name}",
            f"",
            f"Entrada: matriz {n} documentos × {matrix.shape[1]} características (TF-IDF normalizado L2).",
            f"",
            "Descripción del método:",
        ]
        for line in _METHOD_DESCRIPTIONS[self._method]:
            steps.append(f"  {line}")

        steps += [
            f"",
            f"Proceso de agrupamiento jerárquico aglomerativo (bottom-up):",
            f"  1. Inicialización: cada documento es su propio cluster → {n} clusters.",
            f"  2. Iteración: se fusionan los 2 clusters más cercanos según el criterio del método.",
            f"  3. Se repite hasta tener 1 cluster. Total de fusiones: {n_merges}.",
            f"",
            f"Primeras 3 fusiones (Z[i] = [cluster_a, cluster_b, distancia, tamaño]):",
        ]
        for i in range(min(3, n_merges)):
            a, b, d, s = Z[i]
            steps.append(f"  Fusión {i+1}: doc_{int(a)} + doc_{int(b)} → distancia={d:.4f}, cluster_size={int(s)}")

        steps += [
            f"",
            f"Correlación cofenética: {round(c, 4)}",
            f"  Mide qué tan bien preserva el dendrograma las distancias originales.",
            f"  Rango [0, 1]. Valores > 0.75 indican agrupamiento coherente.",
        ]

        return steps

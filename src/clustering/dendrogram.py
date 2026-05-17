import sys

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram

from src.clustering.hierarchical import ClusteringResult

# scipy recorre el árbol jerárquico recursivamente. Para N documentos,
# la profundidad de recursión puede superar el límite de Python (~1000).
# Aumentamos el límite para evitar RecursionError en corpus grandes.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))

# Umbral a partir del cual truncamos el dendrograma (mostrar solo
# las últimas p fusiones en vez de todas las hojas).
TRUNCATE_AT = 500
TRUNCATE_TO = 50


def build_dendrogram_figure(result: ClusteringResult, labels: list[str]) -> Figure:
    n_leaves = len(labels)
    fig_height = max(8, min(n_leaves * 0.25, 40))  # cap a 40 pulgadas
    fig, ax = plt.subplots(figsize=(14, fig_height))

    kwargs: dict = {
        "Z": result.linkage_matrix,
        "ax": ax,
        "orientation": "right",
        "color_threshold": 0.7 * max(result.linkage_matrix[:, 2]),
    }

    if n_leaves > TRUNCATE_AT:
        # Dendrograma truncado: muestra las últimas TRUNCATE_TO fusiones
        # como clusters hoja, con el tamaño de cada cluster entre paréntesis.
        kwargs["truncate_mode"] = "lastp"
        kwargs["p"] = TRUNCATE_TO
        kwargs["leaf_font_size"] = 8
        kwargs["show_leaf_counts"] = True
    else:
        kwargs["labels"] = labels
        kwargs["leaf_font_size"] = 7

    scipy_dendrogram(**kwargs)

    trunc_msg = f" (truncado a {TRUNCATE_TO} clusters)" if n_leaves > TRUNCATE_AT else ""
    ax.set_title(
        f"Dendrograma — {result.method_name}{trunc_msg}\n"
        f"Correlación cofenética: {result.cophenetic_correlation}",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("Distancia euclidiana (vectores TF-IDF normalizados L2)", fontsize=10)
    ax.tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    return fig

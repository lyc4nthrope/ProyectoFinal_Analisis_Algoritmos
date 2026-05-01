import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram

from src.clustering.hierarchical import ClusteringResult


def build_dendrogram_figure(result: ClusteringResult, labels: list[str]) -> Figure:
    fig, ax = plt.subplots(figsize=(14, max(8, len(labels) * 0.25)))

    scipy_dendrogram(
        result.linkage_matrix,
        labels=labels,
        ax=ax,
        orientation="right",
        leaf_font_size=7,
        color_threshold=0.7 * max(result.linkage_matrix[:, 2]),
    )

    ax.set_title(
        f"Dendrograma — {result.method_name}\n"
        f"Correlación cofenética: {result.cophenetic_correlation}",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("Distancia euclidiana (vectores TF-IDF normalizados L2)", fontsize=10)
    ax.tick_params(axis="y", labelsize=7)

    plt.tight_layout()
    return fig

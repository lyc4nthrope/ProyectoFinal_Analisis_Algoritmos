# Importa sys para modificar el límite de recursión de Python
import sys

# Importa matplotlib para crear la figura del dendrograma
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
# Importa la función de scipy que dibuja el dendrograma a partir de la linkage matrix
from scipy.cluster.hierarchy import dendrogram as scipy_dendrogram

# Importa la estructura con los datos del clustering
from src.clustering.hierarchical import ClusteringResult

# scipy recorre el árbol jerárquico recursivamente. Para N documentos,
# la profundidad de recursión puede superar el límite de Python (~1000).
# Aumentamos el límite para evitar RecursionError en corpus grandes.
sys.setrecursionlimit(max(sys.getrecursionlimit(), 10_000))

# Umbral a partir del cual truncamos el dendrograma (mostrar solo
# las últimas p fusiones en vez de todas las hojas).
TRUNCATE_AT = 500   # Si hay más de 500 hojas, trunca el dendrograma
TRUNCATE_TO = 50    # En modo truncado, muestra solo las últimas 50 fusiones


def build_dendrogram_figure(result: ClusteringResult, labels: list[str]) -> Figure:
    n_leaves = len(labels)
    # Calcula la altura de la figura: 0.25 pulgadas por hoja, mínimo 8, máximo 40
    fig_height = max(8, min(n_leaves * 0.25, 40))  # cap a 40 pulgadas
    fig, ax = plt.subplots(figsize=(14, fig_height))

    # Argumentos base para el dendrograma de scipy
    kwargs: dict = {
        "Z": result.linkage_matrix,           # Matriz de enlace generada por hierarchical.py
        "ax": ax,                             # Axes de matplotlib donde dibujar
        "orientation": "right",              # Dendrograma horizontal (hojas a la derecha)
        "color_threshold": 0.7 * max(result.linkage_matrix[:, 2]),  # Umbral de coloreado
    }

    if n_leaves > TRUNCATE_AT:
        # Dendrograma truncado: muestra las últimas TRUNCATE_TO fusiones
        # como clusters hoja, con el tamaño de cada cluster entre paréntesis.
        kwargs["truncate_mode"] = "lastp"     # Modo de truncado por últimas p fusiones
        kwargs["p"] = TRUNCATE_TO             # Número de hojas a mostrar
        kwargs["leaf_font_size"] = 8          # Tamaño de fuente para las etiquetas
        kwargs["show_leaf_counts"] = True     # Muestra cuántos documentos hay en cada cluster
    else:
        # Dendrograma completo: muestra todas las etiquetas (títulos truncados)
        kwargs["labels"] = labels
        kwargs["leaf_font_size"] = 7

    # Dibuja el dendrograma con scipy usando los argumentos configurados
    scipy_dendrogram(**kwargs)

    # Prepara el mensaje de truncado si aplica
    trunc_msg = f" (truncado a {TRUNCATE_TO} clusters)" if n_leaves > TRUNCATE_AT else ""
    # Título del gráfico con el método y la correlación cofenética
    ax.set_title(
        f"Dendrograma — {result.method_name}{trunc_msg}\n"
        f"Correlación cofenética: {result.cophenetic_correlation}",
        fontsize=13,
        pad=12,
    )
    ax.set_xlabel("Distancia euclidiana (vectores TF-IDF normalizados L2)", fontsize=10)
    ax.tick_params(axis="y", labelsize=7)

    # Ajusta el layout para evitar que las etiquetas se corten
    plt.tight_layout()
    return fig

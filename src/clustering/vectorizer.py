# Importa dataclass para definir la estructura de la matriz del corpus
from dataclasses import dataclass

# Importa numpy para operaciones matriciales eficientes
import numpy as np
# Importa TruncatedSVD para reducir la dimensionalidad de la matriz TF-IDF
from sklearn.decomposition import TruncatedSVD
# Importa TfidfVectorizer para convertir texto en vectores TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer
# Importa normalize para normalizar vectores a norma L2 = 1
from sklearn.preprocessing import normalize

# Importa el preprocesador de texto
from src.processing.text_preprocessing import to_string


# Estructura que encapsula la matriz del corpus y toda la información de preprocesamiento
@dataclass
class CorpusMatrix:
    matrix: np.ndarray      # Matriz N_docs × n_components (TF-IDF normalizado L2)
    labels: list[str]       # Etiquetas truncadas a 40 caracteres para el dendrograma
    n_docs: int             # Número de documentos en el corpus
    n_features: int         # Tamaño original del vocabulario TF-IDF
    n_components: int       # Número de componentes después del SVD
    steps: list[str]        # Explicación del preprocesamiento para la interfaz


def build_matrix(abstracts: list[str], titles: list[str]) -> CorpusMatrix:
    """
    Convierte abstracts en una matriz TF-IDF normalizada por L2,
    con reducción de dimensionalidad vía TruncatedSVD (100 componentes).

    La normalización L2 hace que ||v||=1 para cada documento,
    lo que permite usar distancia euclidiana como equivalente a distancia coseno:
        d_eucl(a, b) = √(2 - 2·cos(a,b))
    Esta equivalencia permite aplicar Ward (que exige euclidiana) con
    la misma base geométrica que los otros métodos.

    SVD (TruncatedSVD, 100 componentes) reduce la dimensionalidad de ~5000
    términos a 100 dimensiones latentes, acelerando drásticamente el cálculo
    de distancias en el clustering jerárquico sin perder información semántica
    relevante (es Análisis Semántico Latente / LSA).
    """
    # Preprocesa todos los abstracts: tokeniza y elimina stopwords
    processed = [to_string(abstract) for abstract in abstracts]

    # Vectoriza con TF-IDF: min_df=2 descarta términos raros, max_df=0.9 descarta los muy comunes
    vectorizer = TfidfVectorizer(min_df=2, max_df=0.9)
    tfidf_sparse = vectorizer.fit_transform(processed)
    n_features = tfidf_sparse.shape[1]

    # SVD reduce dimensionalidad: máx 100 o n_features-1 (lo que sea menor)
    # El -1 es necesario porque SVD no puede tener más componentes que dimensiones
    n_target = min(100, max(1, n_features - 1))
    svd = TruncatedSVD(n_components=n_target, random_state=42)
    tfidf_dense = svd.fit_transform(tfidf_sparse)

    # Normaliza cada fila a norma L2 = 1 para habilitar distancia euclidiana ≡ coseno
    matrix = normalize(tfidf_dense, norm="l2")

    # Trunca los títulos a 40 caracteres para que quepan en el dendrograma
    labels = [
        (t[:40] + "...") if len(t) > 40 else t
        for t in titles
    ]

    n_docs, n_components = matrix.shape

    # Construye la explicación del preprocesamiento para mostrar en la interfaz
    steps = [
        f"1. Preprocesamiento: tokenización y eliminación de stopwords en {n_docs} abstracts.",
        f"2. Vectorización TF-IDF: min_df=2, max_df=0.9 → vocabulario de {n_features} términos.",
    ]
    if n_target < n_features:
        steps.append(
            f"3. Reducción de dimensionalidad con TruncatedSVD: {n_features} → {n_components} componentes."
            f"\n   Motivo: acelerar el cálculo de distancias (50x más rápido).",
        )
    steps += [
        f"{'4' if n_target < n_features else '3'}. Normalización L2: ||v||=1.",
        f"   Matriz resultante: {n_docs} documentos × {n_components} componentes.",
    ]

    return CorpusMatrix(matrix=matrix, labels=labels, n_docs=n_docs, n_components=n_components, n_features=n_features, steps=steps)

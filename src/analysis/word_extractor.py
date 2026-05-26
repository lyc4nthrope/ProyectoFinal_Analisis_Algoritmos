# Importa dataclass para definir estructuras de datos limpias
from dataclasses import dataclass

# Importa numpy para operaciones vectoriales eficientes sobre la matriz TF-IDF
import numpy as np
# Importa TfidfVectorizer para extraer términos representativos del corpus
from sklearn.feature_extraction.text import TfidfVectorizer

# Importa la función que convierte texto a string de tokens normalizados
from src.processing.text_preprocessing import to_string

# Número máximo de términos a extraer por defecto (límite del spec: 15)
_MAX_WORDS = 15


# Estructura que representa un término extraído con su score de relevancia
@dataclass
class ExtractedWord:
    term: str    # El término o bigrama extraído (ej: "machine learning")
    score: float # Score TF-IDF acumulado sobre todo el corpus


# Estructura completa del resultado de extracción con términos y explicación
@dataclass
class WordExtractionResult:
    words: list[ExtractedWord]  # Lista de términos ordenados por relevancia
    steps: list[str]            # Explicación paso a paso del proceso TF-IDF


def extract_associated_words(abstracts: list[str], max_words: int = _MAX_WORDS) -> WordExtractionResult:
    """
    Extrae los términos más representativos del corpus usando TF-IDF.

    TF(t, d)    = frecuencias del término t en el documento d
    IDF(t)      = log( (1 + N) / (1 + df(t)) ) + 1
    TF-IDF(t,d) = TF(t,d) × IDF(t)

    Score final por término = suma de TF-IDF sobre todos los documentos.
    Los top-{max_words} representan los conceptos más relevantes y específicos del corpus.
    """
    # Preprocesa todos los abstracts (tokeniza + elimina stopwords)
    processed = [to_string(abstract) for abstract in abstracts]

    # Configura el vectorizador TF-IDF con n-gramas de 1 y 2 palabras (unigramas y bigramas)
    # min_df=2: descarta términos que aparecen en menos de 2 documentos (muy raros)
    # max_df=0.85: descarta términos que aparecen en más del 85% de documentos (demasiado comunes)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.85)
    tfidf_matrix = vectorizer.fit_transform(processed)

    # Obtiene el vocabulario (lista de todos los términos/bigramas aprendidos)
    vocab = vectorizer.get_feature_names_out()
    # Suma las puntuaciones TF-IDF de cada término a través de todos los documentos
    term_scores = np.asarray(tfidf_matrix.sum(axis=0)).flatten()

    # Selecciona los índices de los top-max_words términos con mayor score acumulado
    top_indices = term_scores.argsort()[::-1][:max_words]
    extracted = [
        ExtractedWord(term=vocab[i], score=round(float(term_scores[i]), 4))
        for i in top_indices
    ]

    n_docs = len(abstracts)
    vocab_size = len(vocab)

    # Construye la explicación matemática del proceso para mostrar en la interfaz
    steps = [
        f"1. Preprocesamiento: tokenización y eliminación de stopwords en {n_docs} abstracts.",
        f"2. Vectorización TF-IDF con n-gramas (1,2): vocabulario de {vocab_size} términos/bigramas.",
        f"   min_df=2 (aparece en al menos 2 documentos), max_df=0.85 (en máximo 85% de documentos).",
        f"3. Matriz TF-IDF resultante: {n_docs} documentos × {vocab_size} términos.",
        f"   TF(t,d) = frecuencia del término t en documento d",
        f"   IDF(t)  = log((1+N)/(1+df(t))) + 1  donde N={n_docs}, df=documentos que contienen t",
        f"4. Score por término = Σ TF-IDF(t,d) sobre todos los documentos d.",
        f"   Penaliza términos muy comunes (IDF bajo) y premia los específicos del corpus.",
        f"5. Top-{max_words} términos por score total:",
    ]
    # Agrega cada término extraído con su posición y score a la explicación
    for i, w in enumerate(extracted, 1):
        steps.append(f"   {i:2}. {w.term:<35} score={w.score}")

    return WordExtractionResult(words=extracted, steps=steps)

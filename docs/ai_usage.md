# Uso de Inteligencia Artificial en el Proyecto

## Contexto

El requerimiento R2 del proyecto exige implementar **cuatro algoritmos clásicos** y **dos algoritmos basados en inteligencia artificial** para calcular similitud entre abstracts de artículos científicos. Este documento justifica la selección de los dos algoritmos con IA, describe su funcionamiento técnico, explica su integración en el sistema y registra las decisiones de diseño tomadas durante la implementación.

---

## Algoritmos con IA implementados

### 1. LSI — Latent Semantic Indexing (Indexación Semántica Latente)

**Archivo:** `src/similarity/lsi_similarity.py`

#### Qué es

LSI es una técnica de recuperación de información basada en álgebra lineal. Parte de una matriz término-documento construida con TF-IDF y aplica Descomposición en Valores Singulares (SVD) para reducir la dimensionalidad al espacio semántico latente. El nombre "latente" hace referencia a que el modelo aprende relaciones semánticas implícitas entre términos que no aparecen juntos textualmente pero sí en contextos similares.

#### Fundamento matemático

Dada la matriz TF-IDF `X` de dimensión `(n_documentos × n_términos)`:

```
X ≈ U · Σ · Vᵀ
```

Donde:
- `U`: matriz de documentos en el espacio latente (`n_documentos × k`)
- `Σ`: diagonal de valores singulares (importancia de cada dimensión latente)
- `Vᵀ`: matriz de términos en el espacio latente (`k × n_términos`)

Con `k = 100` componentes latentes (parámetro configurable), cada documento queda representado como un vector en `ℝ¹⁰⁰`. La similitud entre dos documentos se calcula como la similitud coseno entre sus vectores proyectados.

#### Por qué es IA

LSI aprende una representación del lenguaje a partir de los datos. A diferencia de Jaccard o Levenshtein, que operan sobre la forma literal de las palabras, LSI captura que "machine learning" y "deep learning" son semánticamente próximos dentro del corpus, incluso si no comparten tokens exactos. Esto lo convierte en un modelo estadístico de lenguaje no supervisado: no requiere etiquetas pero sí entrenamiento sobre el corpus.

#### Complejidad

- `fit()`: O(n·d·k) donde `n` = documentos, `d` = dimensión TF-IDF, `k` = componentes SVD
- `compute_pair()`: O(k) — producto punto de dos vectores en el espacio latente

#### Integración

```python
# src/similarity/lsi_similarity.py
class LSISimilarity(BaseSimilarity):
    def fit(self, corpus: list[str]) -> None:
        # TfidfVectorizer -> TruncatedSVD (100 componentes)
        self._vectors = self._pipeline.fit_transform(corpus)

    def compute_pair(self, idx_a: int, idx_b: int) -> float:
        # similitud coseno entre vectores latentes
        return float(cosine_similarity(
            self._vectors[idx_a].reshape(1, -1),
            self._vectors[idx_b].reshape(1, -1)
        )[0, 0])
```

---

### 2. Sentence Embeddings (Embeddings de oraciones)

**Archivo:** `src/similarity/sentence_embedding_similarity.py`

#### Qué es

Los Sentence Embeddings son representaciones vectoriales densas generadas por modelos de lenguaje basados en Transformers. El modelo utilizado es `all-MiniLM-L6-v2` de la biblioteca `sentence-transformers`. Este modelo fue preentrenado con BERT y afinado sobre pares de oraciones para producir embeddings donde la similitud coseno refleja la similitud semántica.

#### Fundamento técnico

El modelo `all-MiniLM-L6-v2` es una versión comprimida de BERT con 6 capas Transformer, 384 dimensiones de salida y aproximadamente 22 millones de parámetros. Dado un texto de entrada:

1. El tokenizador divide el texto en subpalabras (WordPiece).
2. Los tokens se pasan por 6 capas de atención multi-cabeza.
3. El embedding final se obtiene aplicando mean-pooling sobre los estados ocultos de la última capa.
4. El vector resultante tiene dimensión `ℝ³⁸⁴`.

La similitud entre dos abstracts se calcula como:

```
similitud(a, b) = cos(embed(a), embed(b)) = (embed(a) · embed(b)) / (||embed(a)|| · ||embed(b)||)
```

#### Por qué es IA

Este algoritmo usa un modelo de red neuronal profunda preentrenado. A diferencia de LSI, no requiere datos del corpus para funcionar: el conocimiento semántico ya está codificado en los pesos del modelo tras el preentrenamiento en corpus masivos. Es el único algoritmo del proyecto que depende de una red neuronal con aprendizaje supervisado previo.

#### Decisión de diseño: modo offline

En entornos sin acceso a internet (incluyendo el servidor de despliegue durante el arranque inicial), el modelo puede no estar disponible en caché local. Para garantizar que la aplicación funcione sin fallos:

```python
# Importación condicional — permite arrancar sin la librería instalada
try:
    from sentence_transformers import SentenceTransformer
    _HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    _HAS_SENTENCE_TRANSFORMERS = False

def _load_model(self) -> "SentenceTransformer":
    if not _HAS_SENTENCE_TRANSFORMERS:
        raise RuntimeError("sentence-transformers no disponible")
    # local_files_only=True: no intenta descargar desde internet
    self._model = SentenceTransformer(self._model_name, local_files_only=True)
    return self._model
```

Si el modelo no está en caché local, `SentenceEmbeddingSimilarity` lanza un error controlado que la vista (`app/views/similarity.py`) captura y presenta al usuario con un mensaje explicativo, sin interrumpir la aplicación.

#### Complejidad

- `fit()`: O(n) — codificación por lotes (batch encoding) de todos los abstracts
- `compute_pair()`: O(d) donde `d = 384` — producto punto en el espacio de embeddings

La optimización clave respecto a una implementación naïve es que `fit()` codifica todos los textos en un solo paso batch, almacena los vectores en un diccionario y `compute_pair()` solo recupera y compara. Sin esto, cada llamada a `compute_pair()` recodificaría el texto desde cero, resultando en complejidad O(n) por par.

---

## Comparación entre algoritmos clásicos y con IA

| Algoritmo | Tipo | Representación | Semántica | Complejidad fit | Complejidad par |
|-----------|------|----------------|-----------|-----------------|-----------------|
| Levenshtein | Clásico | Caracteres | No | O(1) | O(m·n) |
| Jaccard | Clásico | Tokens | No | O(n·d) | O(d) |
| Cosine TF-IDF | Clásico | Bolsa de palabras | Parcial | O(n·d) | O(d) |
| BM25 | Clásico | Bolsa de palabras | Parcial | O(n·d) | O(d) |
| LSI (SVD) | IA | Espacio latente | Sí | O(n·d·k) | O(k) |
| Sentence Embeddings | IA (DL) | Red neuronal | Sí (profunda) | O(n) batch | O(384) |

Los algoritmos con IA son superiores para encontrar similitudes semánticas que los algoritmos clásicos no pueden detectar. Por ejemplo, dos abstracts que traten el mismo tema usando vocabulario diferente obtendrán alta similitud con LSI y Sentence Embeddings, pero baja similitud con Levenshtein o Jaccard.

---

## Implementación en la interfaz

La página `Similitud` (`app/views/similarity.py`) expone todos los algoritmos al usuario mediante un selector. El usuario puede:

1. Seleccionar un abstract de referencia.
2. Elegir uno o más algoritmos.
3. Ver el top-k de artículos más similares con sus puntuaciones.
4. Ver la matriz de similitud completa entre todos los abstracts.

La fachada `SimilarityAnalyzer` (`src/similarity/similarity_analyzer.py`) orquesta todos los algoritmos bajo una interfaz uniforme, permitiendo que la vista no conozca los detalles de implementación de cada uno.

---

## Justificación académica

El uso de dos algoritmos basados en IA en este proyecto responde directamente al requerimiento R2 del enunciado. La selección de LSI y Sentence Embeddings fue intencional:

- **LSI** representa el primer escalón histórico de los modelos de lenguaje basados en álgebra lineal, ampliamente usado en sistemas de recuperación de información desde los años 90.
- **Sentence Embeddings** representa el estado del arte actual, donde modelos Transformer preentrenados producen representaciones semánticas que superan consistentemente a los enfoques clásicos en benchmarks de similitud de texto.

Juntos, ilustran la evolución de la representación semántica en NLP: desde reducción de dimensionalidad estadística hasta redes neuronales profundas con atención.

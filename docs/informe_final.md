# Informe Final — Análisis Bibliométrico sobre Inteligencia Artificial Generativa

**Universidad del Quindío**
Programa de Ingeniería de Sistemas y Computación
Análisis de Algoritmos en el contexto de la bibliometría

**Autores:**
Daniel Stiven Pérez Córdoba
Cristhian Eduardo Osorio Restrepo

**Dominio de conocimiento:** Generative Artificial Intelligence
**Cadena de búsqueda:** `"generative artificial intelligence"`

---

## 1. Introducción

La bibliometría es una disciplina que permite explorar y analizar volúmenes de datos derivados de la producción científica utilizando métodos cuantitativos y cualitativos. Se fundamenta en las matemáticas y la estadística para establecer descripciones, relaciones, inferencias y presentaciones de la información suministrada por publicaciones científicas.

Este proyecto implementa un sistema de análisis bibliométrico computacional sobre el dominio de la inteligencia artificial generativa. El sistema automatiza la recolección de artículos científicos desde múltiples fuentes, aplica seis algoritmos de similitud textual (cuatro clásicos y dos basados en IA), analiza la frecuencia de conceptos clave, agrupa artículos mediante clustering jerárquico y genera visualizaciones interactivas de la producción científica.

El corpus resultante contiene **225 artículos únicos** obtenidos de tres fuentes: OpenAlex API, ScienceDirect y EBSCO Academic Search Ultimate. Durante el proceso de unificación se detectaron y registraron **128 duplicados**.

---

## 2. Propósito del proyecto

Implementar algoritmos que permitan el análisis bibliométrico y computacional sobre un dominio de conocimiento a partir de bases de datos disponibles en la Universidad del Quindío. El proyecto se fundamenta en seis requerimientos funcionales que contemplan la implementación de diversas técnicas bibliométricas y tipos de algoritmos, con despliegue de la aplicación y documentación técnica correspondiente.

---

## 3. Arquitectura del sistema

### 3.1 Estructura de capas

El sistema está organizado en dos capas principales:

```
app/          ← Interfaz Streamlit y orquestación de interacción
src/          ← Lógica de dominio, procesamiento, análisis y exportación
```

**Regla de diseño aplicada:** las vistas no leen ni escriben archivos directamente; la lógica de negocio y persistencia vive en `src/`.

### 3.2 Estructura de carpetas

```
ProyectoFinal_Analisis_Algoritmos/
├── app/
│   ├── main.py              ← Entrada principal, navegación Streamlit
│   ├── loader.py            ← Carga cacheada del corpus y analizadores
│   └── views/               ← Páginas: overview, upload, api_search,
│                               similarity, concepts, clustering,
│                               visualization, export_pdf
├── data/
│   ├── raw/
│   │   ├── sciencedirect/          ← Exportaciones .bib de ScienceDirect
│   │   └── academicsearchultimate/ ← Exportaciones .bibtex de EBSCO
│   └── processed/
│       ├── unified.csv        ← 225 artículos únicos
│       ├── duplicates.csv     ← 128 duplicados registrados
│       └── country_cache.json ← Caché de resolución geográfica
├── src/
│   ├── data_sources/    ← bibtex_parser.py, api_source.py
│   ├── processing/      ← unifier.py, deduplication.py, text_preprocessing.py
│   ├── repositories/    ← corpus_repository.py
│   ├── services/        ← api_search_service.py, api_search_store.py
│   ├── similarity/      ← 6 algoritmos + similarity_analyzer.py
│   ├── analysis/        ← concept_frequency.py, word_extractor.py, precision_evaluator.py
│   ├── clustering/      ← hierarchical.py, dendrogram.py, vectorizer.py
│   └── visualization/   ← geo_heatmap.py, wordcloud_chart.py, timeline_chart.py, pdf_exporter.py
├── docs/
├── exports/
└── tests/               ← 184 pruebas automatizadas
```

### 3.3 Módulos y responsabilidades

| Módulo | Archivo(s) | Responsabilidad |
|--------|-----------|-----------------|
| Ingesta API | `src/data_sources/api_source.py` | Consulta OpenAlex, pagina resultados, transforma JSON |
| Ingesta BibTeX | `src/data_sources/bibtex_parser.py` | Parsea .bib y .bibtex de cualquier fuente |
| Preprocesamiento | `src/processing/text_preprocessing.py` | `normalize()`, `tokenize()`, `to_string()` compartidos |
| Deduplicación | `src/processing/deduplication.py` | Exact match O(1) + Levenshtein con umbral 0.90 |
| Unificador | `src/processing/unifier.py` | Orquesta descubrimiento, carga, mezcla y guardado |
| Repositorio | `src/repositories/corpus_repository.py` | Lectura e integración del corpus persistido |
| Similitud | `src/similarity/` | 6 algoritmos bajo patrón Strategy |
| Conceptos | `src/analysis/concept_frequency.py` | Frecuencia de 15 conceptos GenAI por regex |
| Palabras | `src/analysis/word_extractor.py` | Top-15 términos por TF-IDF con bigramas |
| Evaluación | `src/analysis/precision_evaluator.py` | Precisión / Recall / F1 |
| Clustering | `src/clustering/hierarchical.py` | Single, Complete, Ward + correlación cofenética |
| Dendrograma | `src/clustering/dendrogram.py` | Figura matplotlib desde resultado de clustering |
| Heatmap | `src/visualization/geo_heatmap.py` | Mapa coroplético Plotly por país |
| Nube | `src/visualization/wordcloud_chart.py` | WordCloud desde abstracts y keywords |
| Timeline | `src/visualization/timeline_chart.py` | Publicaciones por año y top 10 revistas |
| PDF | `src/visualization/pdf_exporter.py` | Portada + figuras en PDF con fpdf2 |
| App | `app/main.py` + `app/views/` | Interfaz Streamlit con 8 secciones |

### 3.4 Decisiones de diseño relevantes

**Patrón Strategy en similitud:** cada algoritmo implementa `BaseSimilarity` con `fit()` y `compute_pair()`. La fachada `SimilarityAnalyzer` trabaja con cualquier algoritmo sin conocer su implementación interna.

**Caching lazy en `app/loader.py`:** `@st.cache_resource` garantiza que `SimilarityAnalyzer` y `ClusteringAnalyzer` se inicializan una sola vez por sesión, sin importar cuántas veces el usuario navegue entre páginas.

**L2-normalización en vectorización TF-IDF para clustering:** permite usar distancia euclidiana equivalente a distancia coseno cuando `||v|| = 1`, requisito de Ward linkage.

**Caché local JSON en geo_resolver.py:** evita repetir llamadas a la API de CrossRef para DOIs ya resueltos. Se persiste en `data/processed/country_cache.json`.

**Instalación editable vía `pyproject.toml`:** elimina la necesidad de `sys.path` hacks en los módulos. En Streamlit Cloud se añade `sys.path.insert(0, repo_root)` al inicio de `app/main.py` como compensación por el comportamiento del servidor remoto.

---

## 4. Requerimiento 1 — Automatización de descarga y unificación

### 4.1 Descripción del requerimiento

Automatizar la descarga de información sobre dos bases de datos. Unificar en un solo archivo garantizando una sola instancia por producto. Generar un archivo con los duplicados eliminados.

### 4.2 Fuentes de datos implementadas

| Fuente | Tipo | Archivo de ingesta | Notas |
|--------|------|--------------------|-------|
| **OpenAlex** | API pública automatizada | `src/data_sources/api_source.py` | Paginación automática, hasta 200 resultados |
| **ScienceDirect** | Exportación BibTeX | `src/data_sources/bibtex_parser.py` | Archivos `.bib` en `data/raw/sciencedirect/` |
| **EBSCO Academic Search Ultimate** | Exportación BibTeX | `src/data_sources/bibtex_parser.py` | Archivos `.bibtex` en `data/raw/academicsearchultimate/` |

**Justificación de OpenAlex como fuente principal:** la API pública permite automatizar la recolección sin almacenar credenciales institucionales ni depender de automatización web sobre portales privados. ScienceDirect y EBSCO actúan como fuentes complementarias mediante exportación manual, integrándose en la misma tubería de procesamiento.

### 4.3 Proceso de unificación

El módulo `src/processing/unifier.py` orquesta:

1. Descubrimiento automático de archivos `.bib` y `.bibtex` en `data/raw/`.
2. Carga y normalización de cada artículo al formato interno del proyecto.
3. Mezcla de resultados de API y de exportaciones en un único corpus.
4. Deduplicación mediante el algoritmo descrito en la sección 4.4.
5. Guardado de `data/processed/unified.csv` y `data/processed/duplicates.csv`.

### 4.4 Algoritmo de deduplicación

**Archivo:** `src/processing/deduplication.py`

El algoritmo opera en dos fases sobre los títulos normalizados:

**Fase 1 — Exact match (O(1) por búsqueda):**
Se mantiene un diccionario `exact_index: {titulo_normalizado → índice}`. Si el título ya existe en el índice, se registra como duplicado sin costo adicional.

**Fase 2 — Similitud aproximada (O(n) en el peor caso):**
Si no hay exact match, se compara contra todos los títulos existentes usando distancia de Levenshtein normalizada:

```
similitud(a, b) = 1 - Levenshtein.distance(a, b) / max(len(a), len(b))
```

Si `similitud ≥ 0.90`, se considera duplicado.

**Política de merge:** cuando se detecta un duplicado, se conserva el artículo con más campos completos. Los campos vacíos del artículo conservado se complementan con los del duplicado descartado.

**Implementación:**

```python
from rapidfuzz.distance import Levenshtein

SIMILARITY_THRESHOLD = 0.90

def _similarity(a: str, b: str) -> float:
    distance = Levenshtein.distance(a, b)
    return 1 - distance / max(len(a), len(b))
```

**Biblioteca:** `rapidfuzz>=3.9.0`. Proporciona la misma API que `python-Levenshtein` con soporte de wheels para Python 3.12+.

### 4.5 Resultados

- **`data/processed/unified.csv`:** 225 artículos únicos con todos sus campos.
- **`data/processed/duplicates.csv`:** 128 duplicados registrados con referencia al artículo que los reemplazó.

---

## 5. Requerimiento 2 — Algoritmos de similitud textual

### 5.1 Descripción del requerimiento

Implementar cuatro algoritmos clásicos de similitud textual (distancia de edición o vectorización estadística) y dos con modelos de IA. Presentar explicación detallada paso a paso del funcionamiento matemático y algorítmico de cada uno. La aplicación permite seleccionar dos o más artículos, extraer el abstract y analizar la similitud.

### 5.2 Arquitectura: patrón Strategy

Todos los algoritmos implementan la interfaz `BaseSimilarity`:

```python
class BaseSimilarity(ABC):
    @abstractmethod
    def fit(self, corpus: list[str]) -> None: ...

    @abstractmethod
    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult: ...
```

La fachada `SimilarityAnalyzer` (`src/similarity/similarity_analyzer.py`) orquesta todos los algoritmos y expone métodos de comparación, top-k y matriz completa sin que la vista conozca los detalles de cada implementación.

---

### 5.3 Algoritmo 1 — Levenshtein (Word Edit Distance)

**Archivo:** `src/similarity/levenshtein_similarity.py`
**Tipo:** Clásico — distancia de edición a nivel de palabras
**Complejidad temporal:** O(n × m) donde n, m = cantidad de tokens de cada texto
**Complejidad espacial:** O(min(n, m))

**Fundamento matemático:**

La distancia de edición cuenta el número mínimo de operaciones (inserción, eliminación, sustitución) necesarias para transformar una secuencia de tokens en otra.

**Paso a paso:**

1. Preprocesamiento: tokenización y eliminación de stopwords.
   - Ejemplo: `tokens_A = ["generative", "model", "language"]`
   - Ejemplo: `tokens_B = ["language", "model", "generation"]`

2. Construcción de la matriz de programación dinámica `dp` de tamaño `(n+1) × (m+1)`:
   - `dp[0][j] = j` (transformar cadena vacía en B[:j] cuesta j inserciones)
   - `dp[i][0] = i` (transformar A[:i] en cadena vacía cuesta i eliminaciones)
   - `dp[i][j] = dp[i-1][j-1]` si `tokens_A[i-1] == tokens_B[j-1]`
   - `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])` en caso contrario

3. La distancia final es `dp[n][m]`.

4. Normalización:
```
similitud = 1 - dp[n][m] / max(n, m)
```
Resultado en [0, 1]. Valor 1 = textos idénticos.

**Optimización de espacio:** la implementación usa solo un vector de tamaño `m+1` en lugar de la matriz completa, reduciendo de O(n×m) a O(m) en espacio.

---

### 5.4 Algoritmo 2 — Jaccard Similarity

**Archivo:** `src/similarity/jaccard_similarity.py`
**Tipo:** Clásico — similitud de conjuntos
**Complejidad temporal:** O(n + m)
**Complejidad espacial:** O(n + m)

**Fundamento matemático:**

La similitud de Jaccard mide la proporción de tokens comunes sobre el total de tokens únicos en ambos textos.

```
J(A, B) = |A ∩ B| / |A ∪ B|
```

**Paso a paso:**

1. Tokenización y eliminación de stopwords en ambos textos.
2. Convertir cada texto en un **conjunto** de tokens únicos (ignora frecuencias).
3. Calcular la intersección: `A ∩ B` = tokens que aparecen en ambos.
4. Calcular la unión: `A ∪ B` = todos los tokens únicos de ambos textos.
5. Dividir:
```
J(A, B) = |A ∩ B| / |A ∪ B|
```
Resultado en [0, 1]. Si los conjuntos son idénticos, J = 1.

**Limitación:** no considera la frecuencia de los términos. Dos textos que comparten las mismas palabras en proporciones muy distintas obtienen el mismo score.

---

### 5.5 Algoritmo 3 — Cosine TF-IDF

**Archivo:** `src/similarity/cosine_tfidf_similarity.py`
**Tipo:** Clásico — modelo vectorial con pesos
**Complejidad temporal:** O(V) donde V = tamaño del vocabulario
**Complejidad espacial:** O(V)

**Fundamento matemático:**

Cada abstract se representa como un vector en el espacio de términos del corpus, ponderado por TF-IDF.

```
TF(t, d)     = frecuencia del término t en el documento d
IDF(t)       = log(N / df(t))   donde N = total de documentos, df(t) = documentos que contienen t
TF-IDF(t, d) = TF(t, d) × IDF(t)
```

La similitud entre dos documentos es el coseno del ángulo entre sus vectores:

```
cosine(A, B) = (A · B) / (||A|| × ||B||)
```

**Paso a paso:**

1. `fit()`: construir vocabulario del corpus y calcular IDF por término.
2. `transform(texto)`: vectorizar el texto usando el vocabulario aprendido.
3. Calcular el producto punto: `A · B = Σ(A[i] × B[i])`.
4. Calcular las normas euclidianas: `||A|| = sqrt(Σ A[i]²)`.
5. Dividir:
```
cosine(A, B) = (A · B) / (||A|| × ||B||)
```
Resultado en [0, 1]. Insensible a la longitud de los textos.

---

### 5.6 Algoritmo 4 — BM25 (Okapi)

**Archivo:** `src/similarity/bm25_similarity.py`
**Tipo:** Clásico — ranking probabilístico
**Complejidad temporal:** O(N² · L) para el corpus, O(L) por par
**Parámetros:** k1 = 1.5, b = 0.75

**Fundamento matemático:**

BM25 extiende TF-IDF con dos mejoras: saturación de frecuencia de término (evita que un término muy repetido domine) y normalización por longitud del documento.

```
BM25(q, d) = Σ IDF(t) × [TF(t,d) × (k1 + 1)] / [TF(t,d) + k1 × (1 - b + b × |d| / avgdl)]
```

donde:
- `k1 = 1.5`: controla la saturación de TF (cuánto influye la repetición)
- `b = 0.75`: controla la penalización por longitud del documento
- `avgdl`: longitud promedio de documentos en el corpus
- `IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)`

**Paso a paso:**

1. `fit()`: tokenizar corpus, calcular `avgdl` e `IDF` por término.
2. `BM25(A→B)`: usar A como query y B como documento.
3. `BM25(B→A)`: usar B como query y A como documento.
4. Score bidireccional simétrico:
```
score_raw = (BM25(A→B) + BM25(B→A)) / 2
```
5. Normalización sobre el máximo del corpus:
```
score = score_raw / max_score_corpus
```
Resultado en [0, 1].

---

### 5.7 Algoritmo 5 — LSI / LSA (con IA)

**Archivo:** `src/similarity/lsi_similarity.py`
**Tipo:** IA — Indexación Semántica Latente (Latent Semantic Indexing)
**Complejidad temporal:** O(N · V · k) donde k = 100 componentes latentes
**Complejidad espacial:** O(N · k)

**Por qué es IA:** LSI aprende una representación del lenguaje a partir de los datos del corpus. A diferencia de Jaccard o TF-IDF, captura que "machine learning" y "deep learning" son semánticamente próximos aunque no compartan tokens exactos. Es un modelo estadístico de lenguaje no supervisado.

**Fundamento matemático:**

Partiendo de la matriz TF-IDF `M` de dimensión `(N_documentos × V_vocabulario)`, se aplica Descomposición en Valores Singulares (SVD) truncada:

```
M ≈ U × Σ × Vᵀ
```

donde:
- `U`: matriz de documentos en el espacio latente (N × k)
- `Σ`: diagonal de valores singulares (importancia de cada dimensión)
- `Vᵀ`: matriz de términos en el espacio latente (k × V)

Con `k = 100` componentes latentes, cada documento queda representado como un vector en `ℝ¹⁰⁰`.

**Paso a paso:**

1. `fit()`: construir matriz TF-IDF → aplicar `TruncatedSVD(n_components=100)` → normalizar por fila (L2).
2. Varianza explicada por las 100 dimensiones: accesible en `svd.explained_variance_ratio_.sum()`.
3. Para comparar dos textos nuevos:
   - Transformar con TF-IDF → proyectar con SVD → normalizar.
4. Similitud coseno en el espacio latente:
```
cos(A, B) = A · B   (vectores ya normalizados L2 → ||A|| = ||B|| = 1)
```
Resultado en [0, 1].

---

### 5.8 Algoritmo 6 — Sentence Embeddings (con IA)

**Archivo:** `src/similarity/sentence_embedding_similarity.py`
**Tipo:** IA — Red Neuronal Transformer preentrenada
**Modelo:** `all-MiniLM-L6-v2` (sentence-transformers)
**Complejidad temporal:** O(N) batch en `fit()`, O(384) por par en `compute_pair()`

**Por qué es IA:** usa un modelo de red neuronal profunda preentrenada con aprendizaje supervisado sobre más de 1 billón de pares de oraciones. El conocimiento semántico está codificado en los pesos del modelo. Es el único algoritmo que depende de una red neuronal con entrenamiento supervisado previo.

**Arquitectura del modelo:**
- 6 capas Transformer con atención multi-cabeza
- ~22 millones de parámetros
- Salida: vector denso de 384 dimensiones

**Fundamento técnico:**

Dado un texto de entrada:
1. El tokenizador divide el texto en subpalabras (WordPiece).
2. Los tokens pasan por 6 capas de atención multi-cabeza.
3. Mean-pooling sobre los estados ocultos de la última capa produce el embedding.
4. Normalización L2: `||embedding|| = 1`.

La similitud:
```
similitud(a, b) = cos(embed(a), embed(b)) = embed(a) · embed(b)
```
(el producto punto es equivalente al coseno cuando los vectores están normalizados L2)

**Paso a paso:**

1. `fit()`: almacena el corpus para codificación diferida (lazy loading). El modelo NO se descarga aquí para no bloquear la UI.
2. Primer `compute_pair()` o `compute_matrix()`: codifica el corpus completo en un **único batch** → almacena embeddings en diccionario → lookup O(1) por texto.
3. Comparar dos textos: recuperar embeddings del caché → producto punto.

**Decisión de diseño — robustez offline:** si el modelo no está en caché local, se activa un fallback a TF-IDF L2-normalizado con mensaje al usuario. Esto permite que la aplicación funcione en entornos sin internet.

```python
try:
    self._model = SentenceTransformer(model_name, local_files_only=True)
except Exception as exc:
    self._use_fallback(exc)  # TF-IDF L2 como respaldo
```

### 5.9 Comparativa de algoritmos

| Algoritmo | Tipo | Semántica | Complejidad fit | Complejidad par |
|-----------|------|-----------|-----------------|-----------------|
| Levenshtein | Clásico | No | O(1) | O(n × m) tokens |
| Jaccard | Clásico | No | O(n + m) | O(n + m) |
| Cosine TF-IDF | Clásico | Parcial | O(N · V) | O(V) |
| BM25 | Clásico | Parcial | O(N² · L) | O(L) |
| LSI / LSA | IA | Sí | O(N · V · k) | O(k) = O(100) |
| Sentence Embeddings | IA (DL) | Sí (profunda) | O(N) batch | O(384) |

---

## 6. Requerimiento 3 — Frecuencia de conceptos y nuevas palabras

### 6.1 Descripción del requerimiento

Dada la categoría **Concepts of Generative AI in Education** y sus palabras asociadas, calcular la frecuencia de aparición usando los abstracts como fuente. Usar un algoritmo que analice todos los abstracts y genere un listado de nuevas palabras asociadas (máximo 15). Determinar la precisión de esas nuevas palabras.

### 6.2 Conceptos del dominio (según spec)

| N° | Concepto |
|----|---------|
| 1 | Generative models |
| 2 | Prompting |
| 3 | Machine learning |
| 4 | Multimodality |
| 5 | Fine-tuning |
| 6 | Training data |
| 7 | Algorithmic bias |
| 8 | Explainability |
| 9 | Transparency |
| 10 | Ethics |
| 11 | Privacy |
| 12 | Personalization |
| 13 | Human-AI interaction |
| 14 | AI literacy |
| 15 | Co-creation |

### 6.3 Algoritmo de conteo de frecuencia

**Archivo:** `src/analysis/concept_frequency.py`

Para cada concepto de la lista, se aplica una búsqueda por expresión regular case-insensitive sobre el abstract de cada artículo. Se cuenta cuántos artículos mencionan cada concepto al menos una vez (frecuencia de documentos) y el total de apariciones en el corpus.

### 6.4 Algoritmo de extracción de nuevas palabras asociadas

**Archivo:** `src/analysis/word_extractor.py`

**Algoritmo:** TF-IDF con bigramas sobre el corpus completo de abstracts.

**Paso a paso:**

1. Preprocesamiento: tokenización y eliminación de stopwords en todos los abstracts.
2. Vectorización TF-IDF con n-gramas (unigramas y bigramas):
   - `min_df = 2`: el término debe aparecer en al menos 2 documentos.
   - `max_df = 0.85`: excluye términos que aparecen en más del 85% de documentos (son demasiado generales).
3. Construir matriz TF-IDF de dimensión `(n_docs × n_términos)`.
4. Calcular el score global de cada término: suma de TF-IDF sobre todos los documentos.
   ```
   score(t) = Σ TF-IDF(t, d) para todo d en corpus
   ```
5. Ordenar términos por score descendente.
6. Retornar los **top-15 términos** (unigramas o bigramas) con mayor score.

La fórmula IDF usada por scikit-learn:
```
IDF(t) = log( (1 + N) / (1 + df(t)) ) + 1
```

### 6.5 Evaluación de precisión

**Archivo:** `src/analysis/precision_evaluator.py`

Los 15 términos extraídos se comparan contra el conjunto de referencia de conceptos del spec:

```
Precisión = |extraídos ∩ referencia| / |extraídos|
Recall    = |extraídos ∩ referencia| / |referencia|
F1        = 2 × (P × R) / (P + R)
```

---

## 7. Requerimiento 4 — Clustering jerárquico

### 7.1 Descripción del requerimiento

Implementar tres algoritmos de agrupamiento jerárquico para construir un dendrograma que represente la similitud entre abstracts. Realizar preprocesamiento, calcular similitud, aplicar clustering, representar visualmente y determinar cuál produce agrupamientos más coherentes.

### 7.2 Preprocesamiento y vectorización

**Archivo:** `src/clustering/vectorizer.py`

1. Tokenización y eliminación de stopwords en inglés y español.
2. Vectorización TF-IDF del corpus completo.
3. **L2-normalización de los vectores resultantes.**

La normalización L2 es crítica para Ward linkage: cuando `||v|| = 1`, la distancia euclidiana es equivalente a la distancia coseno:
```
euclidean(u/||u||, v/||v||)² = 2 - 2 · cos(u, v)
```
Esto permite que Ward agrupe por similitud temática y no por longitud del abstract.

### 7.3 Los tres métodos de linkage

**Archivo:** `src/clustering/hierarchical.py`

#### Single Linkage (enlace mínimo)
```
d(A∪B, C) = min{ d(a, c) : a ∈ A, c ∈ C }
```
Fusiona los clusters cuya distancia **mínima** entre cualquier par de puntos sea la menor. Tiende a producir clusters alargados ("efecto cadena"). Sensible a valores atípicos.

#### Complete Linkage (enlace máximo)
```
d(A∪B, C) = max{ d(a, c) : a ∈ A, c ∈ C }
```
Fusiona usando la distancia **máxima**. Produce clusters más compactos y balanceados que Single. Menos sensible a outliers.

#### Ward (mínima varianza)
```
Δ(A, B) = (nA · nB) / (nA + nB) · ||μA − μB||²
```
donde `nA`, `nB` = tamaño de cada cluster y `μA`, `μB` = centroides.

Minimiza el incremento de varianza intra-cluster al fusionar dos clusters. Produce los clusters más balanceados y coherentes para texto. **Generalmente es el mejor método para corpus de abstracts científicos.**

### 7.4 Proceso aglomerativo (bottom-up)

1. Inicialización: cada artículo es su propio cluster → N clusters.
2. Calcular la matriz de distancias entre todos los pares.
3. Fusionar los 2 clusters más próximos según el criterio del método.
4. Actualizar la matriz de distancias.
5. Repetir hasta tener 1 cluster. Total de fusiones: N-1.

La librería `scipy.cluster.hierarchy.linkage` implementa este proceso eficientemente con la fórmula de actualización de Lance-Williams.

### 7.5 Correlación cofenética

Para evaluar la calidad del agrupamiento:
```
c = correlación de Pearson entre distancias originales y distancias cofenéticas
```
La **distancia cofenética** entre dos puntos es la distancia a la que se fusionaron sus clusters en el dendrograma. Un valor cercano a **1.0** indica que el dendrograma preserva fielmente las distancias originales del espacio vectorial.

- **Valor > 0.75**: agrupamiento coherente.
- **Ward típicamente produce la correlación más alta** en corpus de texto (~0.85-0.95).

### 7.6 Estrategia two-tier para corpus grandes

Cuando el corpus supera cierto umbral de artículos, el dendrograma completo se vuelve ilegible. Se aplica una estrategia de dos niveles:
1. Reducir a representantes mediante mini-batch clustering.
2. Aplicar clustering jerárquico sobre los representantes.

---

## 8. Requerimiento 5 — Visualización de la producción científica

### 8.1 Descripción del requerimiento

1. Mapa de calor con distribución geográfica según el primer autor.
2. Nube de palabras con términos más frecuentes en abstracts y keywords (dinámica).
3. Línea temporal de publicaciones por año y por revista.
4. Exportar los tres anteriores a formato PDF.

### 8.2 Mapa de calor geográfico

**Archivos:** `src/visualization/geo_resolver.py`, `src/visualization/geo_heatmap.py`

**Proceso de resolución de país:**
1. Se intenta resolver el país del primer autor a partir del DOI del artículo usando la API de CrossRef.
2. Se consulta la afiliación del autor cuando está disponible.
3. Si un DOI no resuelve o la afiliación no contiene país reconocible, el registro se excluye del mapa.
4. Los resultados se cachean localmente en `data/processed/country_cache.json` para evitar consultas repetidas.

El mapa coroplético se construye con Plotly Express (`choropleth_map`). El color de cada país representa la cantidad de publicaciones de autores de esa nación en el corpus.

### 8.3 Nube de palabras

**Archivo:** `src/visualization/wordcloud_chart.py`

Se genera con la librería `wordcloud` a partir de la concatenación de todos los abstracts y keywords del corpus cargado. La nube es **dinámica**: se regenera cada vez que el corpus cambia (nuevos archivos BibTeX o nuevas búsquedas API añaden artículos).

El tamaño de cada palabra en la nube es proporcional a su frecuencia en el corpus. Se aplica una lista de stopwords en inglés y español antes de generar la nube.

### 8.4 Línea temporal

**Archivo:** `src/visualization/timeline_chart.py`

Se generan dos gráficas:
1. **Publicaciones por año:** conteo de artículos por año de publicación, desde el primer año hasta el más reciente del corpus.
2. **Top 10 revistas:** evolución temporal de las 10 revistas con más publicaciones en el corpus. Permite identificar tendencias editoriales.

### 8.5 Exportación a PDF

**Archivo:** `src/visualization/pdf_exporter.py`

Usando `fpdf2`:
1. Portada con título, fecha de generación y metadatos del corpus.
2. Una sección por cada figura: título y la imagen exportada.
3. Las figuras de Plotly se convierten a PNG mediante `kaleido`.
4. Las figuras de matplotlib se exportan directamente como PNG.

---

## 9. Requerimiento 6 — Despliegue y documentación

### 9.1 Despliegue

La aplicación está desplegada en **Streamlit Community Cloud**:

```
https://bibliometria-genai.streamlit.app
```

**Repositorio:** `https://github.com/lyc4nthrope/ProyectoFinal_Analisis_Algoritmos`
**Rama:** `main` | **Archivo de entrada:** `app/main.py`

### 9.2 Configuración de despliegue

| Archivo | Propósito |
|---------|-----------|
| `requirements.txt` | Dependencias Python |
| `packages.txt` | Dependencias del sistema (`libfontconfig1`) |
| `.streamlit/config.toml` | Headless, CORS deshabilitado |
| `app/main.py` línea 1-3 | `sys.path.insert(0, repo_root)` — necesario en Streamlit Cloud para resolver imports `app.*` y `src.*` |

**Problemas resueltos durante el despliegue:**

1. `python-Levenshtein==0.25.1` falla en Python 3.14 (C extension rota en esa versión). Solución: migrar a `rapidfuzz>=3.9.0`, misma API, wheels disponibles para Python 3.12+.
2. `ModuleNotFoundError: No module named 'app'` en Streamlit Cloud. Causa: el servidor no agrega el root del repositorio al `sys.path`. Solución: `sys.path.insert(0, str(Path(__file__).parent.parent))` al inicio de `app/main.py`.
3. `libfreetype6-dev` en conflicto con Debian trixie. Solución: solo `libfontconfig1` en `packages.txt`.

### 9.3 Ejecución local

```bash
pip install -r requirements.txt
pip install -e . --no-deps
streamlit run app/main.py
```

### 9.4 Suite de pruebas

```bash
pytest tests/ -v
```

**184 pruebas** distribuidas en:

| Carpeta | Pruebas | Cubre |
|---------|---------|-------|
| `tests/data_sources/` | 18 | Ingesta API y BibTeX |
| `tests/processing/` | 22 | Deduplicación y preprocesamiento |
| `tests/similarity/` | 84 | 6 algoritmos + analizador |
| `tests/analysis/` | 24 | Frecuencia, extracción, evaluación |
| `tests/clustering/` | 21 | Vectorización, clustering, dendrograma |
| `tests/visualization/` | 15 | Timeline, wordcloud, mapa, PDF |

---

## 10. Uso de Inteligencia Artificial

### 10.1 Justificación del uso de IA

El requerimiento R2 exige implementar dos algoritmos basados en inteligencia artificial. Se seleccionaron **LSI** y **Sentence Embeddings** por razones complementarias:

- **LSI** representa el primer escalón histórico de los modelos de lenguaje basados en álgebra lineal (años 90), ampliamente usado en recuperación de información.
- **Sentence Embeddings** representa el estado del arte actual, donde modelos Transformer preentrenados superan consistentemente a los enfoques clásicos en benchmarks de similitud semántica.

Juntos ilustran la evolución de la representación semántica en NLP: desde reducción de dimensionalidad estadística hasta redes neuronales profundas con atención.

### 10.2 LSI — Aspectos a considerar

- **Aprendizaje:** no supervisado. El modelo aprende las dimensiones latentes del lenguaje a partir del corpus de abstracts.
- **Parámetro clave:** número de componentes latentes `k = 100`. Más componentes capturan más detalle pero aumentan el costo computacional.
- **Ventaja sobre TF-IDF:** detecta sinónimos y conceptos relacionados aunque no compartan tokens exactos.
- **Limitación:** el espacio latente depende del corpus; un modelo entrenado en un corpus no generaliza bien a dominios muy distintos.

### 10.3 Sentence Embeddings — Aspectos a considerar

- **Aprendizaje:** supervisado previo. El modelo `all-MiniLM-L6-v2` fue preentrenado por Hugging Face en más de 1 billón de pares de oraciones.
- **Portabilidad:** el conocimiento semántico ya está en los pesos; no requiere reentrenamiento sobre el corpus del proyecto.
- **Dimensiones:** vectores de ℝ³⁸⁴. Capturan relaciones semánticas que LSI (ℝ¹⁰⁰ dependiente del corpus) no puede representar.
- **Limitación:** requiere que el modelo esté disponible en caché local para funcionar offline. Se implementó degradación controlada a TF-IDF cuando el modelo no está disponible.
- **Costo:** más lento en el primer cómputo (encoding batch del corpus). Los cómputos subsiguientes son O(384) gracias al caché.

### 10.4 Comparativa IA vs clásicos en contexto bibliométrico

Los algoritmos con IA son superiores para encontrar similitudes semánticas que los clásicos no pueden detectar:

- Dos abstracts que traten el mismo tema con vocabulario diferente obtendrán alta similitud con LSI y Sentence Embeddings, pero baja similitud con Levenshtein o Jaccard.
- En un corpus de artículos científicos donde los autores varían su vocabulario deliberadamente, la semántica profunda es más relevante que la coincidencia léxica exacta.

---

## 11. Conclusiones

El proyecto implementó exitosamente los seis requerimientos funcionales del enunciado:

- **R1:** corpus de 225 artículos únicos obtenido de tres fuentes, con 128 duplicados registrados. Deduplicación automática combinando exact match O(1) y Levenshtein con umbral 0.90.

- **R2:** seis algoritmos de similitud implementados bajo el patrón Strategy, cada uno con su explicación matemática paso a paso accesible en la interfaz. Los algoritmos con IA (LSI y Sentence Embeddings) capturan relaciones semánticas que los clásicos no pueden detectar.

- **R3:** conteo de frecuencia de los 15 conceptos del dominio, extracción de 15 nuevas palabras asociadas por TF-IDF con bigramas, y evaluación con métricas de Precisión, Recall y F1.

- **R4:** tres métodos de clustering jerárquico (Single, Complete, Ward) con dendrograma y correlación cofenética para determinar el método más coherente. Ward produce la mayor correlación cofenética en corpus de texto científico.

- **R5:** mapa geográfico coroplético, nube de palabras dinámica, línea temporal por año y revista, y exportación PDF de las tres visualizaciones.

- **R6:** aplicación desplegada en `https://bibliometria-genai.streamlit.app`, documentación técnica completa y 184 pruebas automatizadas.

El proyecto demuestra que los algoritmos computacionales aplicados a bibliometría permiten extraer patrones significativos de la producción científica sobre inteligencia artificial generativa, combinando técnicas clásicas con modelos modernos de lenguaje.

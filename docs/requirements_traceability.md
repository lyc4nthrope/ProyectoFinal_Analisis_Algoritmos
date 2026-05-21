# Trazabilidad de Requerimientos R1-R6

Referencia: [Proyecto Análisis de Algoritmos.pdf](</home/lycan/Downloads/context ProyectoAnalisis/Proyecto Análisis de Algoritmos.pdf>)

---

## R1. Automatización de descarga y unificación

### Estado

Cumplimiento funcional con decisión de diseño documentada.

### Qué exige el spec

- Obtener información de **al menos dos bases de datos** científicas.
- Unificar en un solo corpus eliminando duplicados.
- Generar `unified.csv` con los artículos únicos.
- Generar un registro de los duplicados encontrados.

### Implementado

| Componente | Archivo | Descripción |
|-----------|---------|-------------|
| Cliente OpenAlex | `src/data_sources/api_source.py` | Paginación automática, hasta 200 resultados por consulta |
| Parser BibTeX | `src/data_sources/bibtex_parser.py` | Lee `.bib` y `.bibtex` desde `data/raw/` |
| Preprocesamiento | `src/processing/text_preprocessing.py` | `normalize()`, `tokenize()`, `to_string()` compartidos |
| Deduplicación | `src/processing/deduplication.py` | Exact match O(1) + Levenshtein con umbral 0.90 |
| Unificador | `src/processing/unifier.py` | Orquesta descubrimiento de archivos, carga, mezcla y guardado |
| Repositorio | `src/repositories/corpus_repository.py` | Lectura, integración y limpieza del corpus persistido |

### Fuentes de datos utilizadas

- **OpenAlex** (fuente automatizada principal): API pública, sin credenciales, paginación, resultado en JSON normalizado.
- **ScienceDirect** (vía exportación BibTeX): archivos `.bib` depositados en `data/raw/sciencedirect/`.
- **EBSCO Academic Search Ultimate** (vía exportación BibTeX): archivos `.bibtex` en `data/raw/academicsearchultimate/`.

### Algoritmo de deduplicación

El módulo `src/processing/deduplication.py` implementa una estrategia en dos fases:

1. **Exact match** (`O(1)`): índice de hash sobre títulos normalizados. Si el título ya existe, se registra como duplicado sin costo adicional.
2. **Similitud aproximada** (`O(n)` en el peor caso): si no hay exact match, se compara contra todos los títulos existentes usando distancia de Levenshtein mediante `rapidfuzz`. Si la similitud es ≥ 0.90, se considera duplicado.

```
similitud(a, b) = 1 - Levenshtein.distance(a, b) / max(len(a), len(b))
```

Cuando se detecta un duplicado, se conserva el artículo con más campos completos y el otro se envía a `duplicates.csv`.

### Resultados con el corpus actual

- `data/processed/unified.csv`: **225 artículos únicos**
- `data/processed/duplicates.csv`: **128 duplicados registrados**

### Cobertura de pruebas

- `tests/processing/test_deduplication.py`: exact match, similitud aproximada, merge de campos, umbral límite.
- `tests/processing/test_text_preprocessing.py`: normalización, tokenización.
- `tests/data_sources/test_bibtex_parser.py`: parseo BibTeX múltiples formatos.
- `tests/data_sources/test_api_source.py`: paginación, transformación JSON.

---

## R2. Cuatro algoritmos clásicos y dos con IA

### Estado

Cumplimiento funcional.

### Qué exige el spec

- Implementar **cuatro algoritmos clásicos** de similitud textual.
- Implementar **dos algoritmos basados en IA**.
- Permitir comparar abstracts entre sí y mostrar la puntuación de similitud.
- Explicar el funcionamiento matemático de cada método.

### Implementado

| Algoritmo | Tipo | Archivo | Descripción técnica |
|-----------|------|---------|---------------------|
| Levenshtein | Clásico | `src/similarity/levenshtein_similarity.py` | Distancia de edición entre strings normalizados |
| Jaccard | Clásico | `src/similarity/jaccard_similarity.py` | \|A ∩ B\| / \|A ∪ B\| sobre conjuntos de tokens |
| Cosine TF-IDF | Clásico | `src/similarity/cosine_tfidf_similarity.py` | Similitud coseno en espacio vectorial TF-IDF |
| BM25 | Clásico | `src/similarity/bm25_similarity.py` | Ranking probabilístico con saturación de términos |
| LSI | IA | `src/similarity/lsi_similarity.py` | TF-IDF + SVD truncado (100 dimensiones latentes) |
| Sentence Embeddings | IA | `src/similarity/sentence_embedding_similarity.py` | Transformer `all-MiniLM-L6-v2`, embeddings ℝ³⁸⁴ |

### Patrón de diseño aplicado

Todos los algoritmos implementan la interfaz `BaseSimilarity` (`src/similarity/base_similarity.py`):

```python
class BaseSimilarity(ABC):
    @abstractmethod
    def fit(self, corpus: list[str]) -> None: ...

    @abstractmethod
    def compute_pair(self, idx_a: int, idx_b: int) -> float: ...
```

Esto es el **patrón Strategy**: la fachada `SimilarityAnalyzer` trabaja con cualquier algoritmo sin conocer su implementación.

### Complejidades

| Algoritmo | fit | compute_pair |
|-----------|-----|--------------|
| Levenshtein | O(n) | O(m·n) donde m,n = len de los strings |
| Jaccard | O(n·d) | O(d) |
| Cosine TF-IDF | O(n·d) | O(d) |
| BM25 | O(n·d) | O(d) |
| LSI | O(n·d·k), k=100 | O(k) |
| Sentence Embeddings | O(n) batch | O(384) |

### Detalle de cada algoritmo

**Levenshtein**: número mínimo de inserciones, eliminaciones y sustituciones para transformar un string en otro. Normalizado por `max(len(a), len(b))`.

**Jaccard**: proporción de tokens comunes sobre la unión de tokens. Insensible al orden y a la frecuencia.

**Cosine TF-IDF**: cada abstract se vectoriza como `TF(t,d) × IDF(t)`. La similitud es el ángulo entre vectores. Captura frecuencia e importancia relativa de términos.

**BM25**: variante de TF-IDF con saturación de frecuencia de término (evita que un término muy repetido domine el score) y normalización por longitud del documento. Parámetros `k1=1.5`, `b=0.75`.

**LSI**: aplica SVD truncada sobre la matriz TF-IDF. Las `k=100` dimensiones latentes capturan relaciones semánticas implícitas. Dos textos con vocabulario diferente pero semántica similar obtienen alta similitud.

**Sentence Embeddings**: modelo Transformer con 6 capas de atención multi-cabeza. Mean-pooling sobre los estados ocultos de la última capa produce vectores de ℝ³⁸⁴. Degradación controlada a TF-IDF si el modelo no está disponible offline.

### Cobertura de pruebas

- `tests/similarity/test_levenshtein_similarity.py`
- `tests/similarity/test_jaccard_similarity.py`
- `tests/similarity/test_cosine_tfidf_similarity.py`
- `tests/similarity/test_bm25_similarity.py`
- `tests/similarity/test_lsi_similarity.py`
- `tests/similarity/test_sentence_embedding_similarity.py`
- `tests/similarity/test_similarity_analyzer.py`

---

## R3. Frecuencia de conceptos y palabras asociadas

### Estado

Cumplimiento funcional.

### Qué exige el spec

- Calcular frecuencia de términos de la categoría **Concepts of Generative AI in Education**.
- Generar un listado de **nuevas palabras asociadas** (máximo 15 términos).
- Evaluar la precisión, recall y F1 de las palabras generadas.

### Implementado

| Componente | Archivo | Descripción |
|-----------|---------|-------------|
| Frecuencia de conceptos | `src/analysis/concept_frequency.py` | Conteo por regex sobre abstracts normalizados |
| Extracción de palabras | `src/analysis/word_extractor.py` | Top-15 por TF-IDF con bigramas, filtrado de stopwords |
| Evaluación | `src/analysis/precision_evaluator.py` | Precisión, Recall y F1 sobre la lista extraída |
| Analizador integrado | `src/analysis/concept_analyzer.py` | Fachada que une los tres módulos |
| Constantes de conceptos | `src/analysis/concepts.py` | Lista canónica de 15 términos del spec |

### Conceptos del dominio (según spec)

```
generative models, prompting, machine learning, multimodality, fine-tuning,
training data, algorithmic bias, explainability, transparency, ethics,
privacy, personalization, human-AI interaction, AI literacy, co-creation
```

### Algoritmo de extracción de palabras asociadas

1. Se construye una matriz TF-IDF sobre todos los abstracts con unigramas y bigramas (`ngram_range=(1,2)`).
2. Se eliminan stopwords en inglés y español.
3. Se suman los scores TF-IDF por término a través del corpus para obtener un score global.
4. Se toman los 15 términos con mayor score agregado.

### Evaluación de precisión

La evaluación compara los 15 términos extraídos contra el conjunto de referencia de conceptos del spec:

```
Precisión = |extraídos ∩ referencia| / |extraídos|
Recall    = |extraídos ∩ referencia| / |referencia|
F1        = 2 × (P × R) / (P + R)
```

### Cobertura de pruebas

- `tests/analysis/test_concept_frequency.py`
- `tests/analysis/test_word_extractor.py`
- `tests/analysis/test_precision_evaluator.py`

---

## R4. Clustering jerárquico

### Estado

Cumplimiento funcional.

### Qué exige el spec

- Implementar **tres algoritmos de clustering jerárquico**.
- Construir un dendrograma.
- Analizar cuál algoritmo produce agrupamientos más coherentes.

### Implementado

| Componente | Archivo | Descripción |
|-----------|---------|-------------|
| Vectorizador | `src/clustering/vectorizer.py` | TF-IDF con L2-normalización para Ward linkage |
| Clustering | `src/clustering/hierarchical.py` | Single, Complete, Ward + correlación cofenética |
| Dendrograma | `src/clustering/dendrogram.py` | Figura matplotlib a partir del resultado |
| Analizador | `src/clustering/clustering_analyzer.py` | Fachada que integra vectorización, clustering y dendrograma |

### Métodos de linkage implementados

| Método | Criterio de fusión | Comportamiento |
|--------|-------------------|----------------|
| **Single** | Distancia mínima entre clusters | Tiende a crear cadenas largas |
| **Complete** | Distancia máxima entre clusters | Clusters compactos y balanceados |
| **Ward** | Minimiza la varianza intra-cluster | Más robusto, clusters de tamaño similar |

### Correlación cofenética

Para evaluar la calidad del agrupamiento se calcula la correlación cofenética entre la matriz de distancias original y la matriz cofenética derivada del árbol jerárquico. Un valor cercano a 1.0 indica que el dendrograma preserva fielmente las distancias originales.

Valores típicos en el corpus actual:
- Ward: correlación más alta (~0.85-0.95)
- Complete: correlación media (~0.75-0.85)
- Single: correlación variable

### Decisión técnica: L2-normalización

TF-IDF sin normalizar produce vectores con normas distintas. Ward linkage opera sobre distancias euclidianas, que para vectores L2-normalizados son equivalentes a la distancia coseno:

```
euclidean(u/||u||, v/||v||)² = 2 - 2·cos(u,v)
```

Esto garantiza que Ward agrupe por similitud temática y no por longitud de abstract.

### Estrategia two-tier para corpus grandes

Cuando el corpus supera 500 artículos, el dendrograma completo se vuelve ilegible. Se aplica una estrategia de dos niveles:

1. Mini-batch clustering para reducir a ~50 representantes.
2. Clustering jerárquico sobre los representantes.

### Cobertura de pruebas

- `tests/clustering/test_hierarchical.py`
- `tests/clustering/test_dendrogram.py`
- `tests/clustering/test_clustering_analyzer.py`

---

## R5. Visualización de la producción científica

### Estado

Cumplimiento funcional con dependencia externa documentada.

### Qué exige el spec

- Mapa de calor con distribución geográfica por primer autor.
- Nube de palabras con términos frecuentes.
- Línea temporal de publicaciones por año y por revista.
- Exportación a PDF.

### Implementado

| Componente | Archivo | Descripción |
|-----------|---------|-------------|
| Resolución geográfica | `src/visualization/geo_resolver.py` | CrossRef API + caché JSON local |
| Mapa de calor | `src/visualization/geo_heatmap.py` | Mapa coroplético Plotly por país |
| Nube de palabras | `src/visualization/wordcloud_chart.py` | WordCloud desde abstracts y keywords |
| Línea temporal | `src/visualization/timeline_chart.py` | Publicaciones por año y top 10 revistas |
| Exportador PDF | `src/visualization/pdf_exporter.py` | Portada + figuras Plotly/Matplotlib en PDF |

### Decisión técnica: caché de resolución geográfica

La resolución de país a partir de DOI depende de CrossRef. Para evitar consultas repetidas:

- La caché se guarda en `data/processed/country_cache.json`.
- Si el DOI ya fue resuelto, se usa el valor en caché sin consultar la API.
- Si CrossRef falla o el DOI es nulo, el artículo queda sin país asignado.

### Exportación PDF

El exportador usa `fpdf2` para construir el PDF:

1. Portada con título y fecha de generación.
2. Sección por cada figura: título, imagen PNG generada por `kaleido` (Plotly) o `matplotlib`.

### Riesgos documentados

- El mapa geográfico puede degradarse por disponibilidad de CrossRef o por artículos sin DOI.
- La exportación de figuras Plotly requiere `kaleido` instalado.

### Cobertura de pruebas

- `tests/visualization/test_timeline_chart.py`
- `tests/visualization/test_wordcloud_chart.py`
- `tests/visualization/test_geo_heatmap.py`
- `tests/visualization/test_pdf_exporter.py`

---

## R6. Despliegue y documentación

### Estado

**Cumplimiento completo.**

### Qué exige el spec

- Aplicación desplegada y accesible.
- Documentación técnica de arquitectura y algoritmos.
- Pruebas automatizadas.

### Implementado

| Componente | Descripción |
|-----------|-------------|
| **Despliegue** | Streamlit Community Cloud — `bibliometria-genai.streamlit.app` |
| **README.md** | Descripción, instalación, datos de entrada, arquitectura, módulos |
| **docs/architecture.md** | Arquitectura detallada, separación de capas, decisiones recientes |
| **docs/requirements_traceability.md** | Este documento — trazabilidad técnica R1-R6 |
| **docs/ai_usage.md** | Justificación de uso de IA: LSI y Sentence Embeddings |
| **Pruebas** | 184 pruebas con `pytest` — cobertura de todos los módulos |

### URL de despliegue

```
https://bibliometria-genai.streamlit.app
```

Repositorio: `https://github.com/lyc4nthrope/ProyectoFinal_Analisis_Algoritmos`  
Rama principal: `main`  
Archivo de entrada: `app/main.py`

### Configuración de despliegue

| Archivo | Propósito |
|---------|-----------|
| `requirements.txt` | Dependencias de Python con versiones mínimas |
| `packages.txt` | Dependencias del sistema operativo (`libfontconfig1`) |
| `.streamlit/config.toml` | Configuración headless, CORS, estadísticas deshabilitadas |
| `app/main.py` | `sys.path.insert(0, repo_root)` al inicio — necesario en Streamlit Cloud para resolver imports `app.*` y `src.*` |

### Ejecución local

```bash
pip install -r requirements.txt
pip install -e . --no-deps
streamlit run app/main.py
```

### Suite de pruebas

```bash
pytest tests/ -v
```

184 pruebas distribuidas en:

- `tests/data_sources/` — ingesta API y BibTeX
- `tests/processing/` — deduplicación y preprocesamiento
- `tests/similarity/` — 6 algoritmos de similitud
- `tests/analysis/` — frecuencia, extracción, evaluación
- `tests/clustering/` — vectorización, clustering, dendrograma
- `tests/visualization/` — timeline, wordcloud, mapa, PDF

---

## Riesgos abiertos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| OpenAlex API no disponible | Baja | Alto | Los CSVs pre-seeded están en git; la app funciona sin API |
| CrossRef API no disponible | Media | Bajo | El mapa queda vacío; el resto de la app no se ve afectado |
| Sentence Embeddings sin caché local | Media | Bajo | Degradación controlada a TF-IDF con mensaje al usuario |
| `kaleido` falla en exportar Plotly | Baja | Medio | Las figuras matplotlib se exportan correctamente; Plotly puede fallar silenciosamente |

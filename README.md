# Bibliometría GenAI

**Universidad del Quindío — Análisis de Algoritmos**
Daniel Stiven Pérez Córdoba · Cristhian Eduardo Osorio Restrepo

**Dominio:** Generative Artificial Intelligence
**App desplegada:** https://bibliometria-genai.streamlit.app
**Documento técnico:** [docs/informe_final.md](docs/informe_final.md)

---

## Qué hace el proyecto

Sistema de análisis bibliométrico computacional sobre publicaciones científicas de inteligencia artificial generativa. Automatiza la recolección, limpia duplicados, compara artículos por similitud, analiza conceptos clave, agrupa por temática y genera visualizaciones.

---

## Guía rápida de sustentación — qué se hizo por requerimiento

### R1 — Automatización de descarga y unificación

**Qué pedía:** dos bases de datos, unificar en un archivo, registrar duplicados, proceso automático.

**Qué se hizo:**
- **3 fuentes:** OpenAlex (API automática), ScienceDirect y EBSCO (exportación BibTeX).
- **Corpus resultante:** `data/processed/unified.csv` — 225 artículos únicos.
- **Duplicados:** `data/processed/duplicates.csv` — 128 registros.
- **Deduplicación en dos fases:** exact match O(1) con diccionario hash + Levenshtein normalizado con umbral 0.90. Si `similitud ≥ 0.90` → duplicado. Se conserva el artículo con más campos completos.
- **Archivos clave:** `src/data_sources/api_source.py`, `src/data_sources/bibtex_parser.py`, `src/processing/deduplication.py`, `src/processing/unifier.py`.

---

### R2 — Algoritmos de similitud textual

**Qué pedía:** 4 clásicos + 2 con IA, explicación matemática paso a paso.

**Qué se hizo — 6 algoritmos bajo patrón Strategy:**

| Algoritmo | Tipo | Idea central |
|-----------|------|-------------|
| Levenshtein | Clásico | Distancia de edición a nivel de palabras, DP O(n×m), normalizado por max(n,m) |
| Jaccard | Clásico | `\|A∩B\| / \|A∪B\|` sobre conjuntos de tokens |
| Cosine TF-IDF | Clásico | `(A·B) / (‖A‖×‖B‖)` en espacio vectorial TF-IDF |
| BM25 | Clásico | TF-IDF con saturación de frecuencia, k1=1.5, b=0.75 |
| LSI / LSA | **IA** | TF-IDF + SVD truncado (100 dim latentes), captura semántica |
| Sentence Embeddings | **IA** | Transformer `all-MiniLM-L6-v2`, vectores ℝ³⁸⁴, fallback offline a TF-IDF |

**Cada algoritmo muestra sus pasos en la interfaz.** Ver implementaciones en `src/similarity/`.

---

### R3 — Frecuencia de conceptos y nuevas palabras

**Qué pedía:** frecuencia de 15 conceptos GenAI, generar 15 nuevas palabras asociadas, medir precisión.

**Qué se hizo:**
- **Conteo:** regex case-insensitive sobre abstracts para los 15 conceptos del spec (generative models, prompting, machine learning, multimodality, fine-tuning, training data, algorithmic bias, explainability, transparency, ethics, privacy, personalization, human-AI interaction, AI literacy, co-creation).
- **Extracción de nuevas palabras:** TF-IDF con bigramas (min_df=2, max_df=0.85), score global = Σ TF-IDF(t,d) por término, top-15 resultantes.
- **Evaluación:** Precisión = `|extraídos ∩ referencia| / |extraídos|`, Recall = `|extraídos ∩ referencia| / |referencia|`, F1.
- **Archivos clave:** `src/analysis/concept_frequency.py`, `src/analysis/word_extractor.py`, `src/analysis/precision_evaluator.py`.

---

### R4 — Clustering jerárquico

**Qué pedía:** 3 algoritmos jerárquicos, dendrograma, determinar cuál es más coherente.

**Qué se hizo:**
- **Vectorización:** TF-IDF con L2-normalización (permite que distancia euclidiana = coseno).
- **3 métodos:**
  - **Single linkage:** distancia mínima entre clusters. Efecto cadena.
  - **Complete linkage:** distancia máxima. Clusters más compactos.
  - **Ward:** minimiza varianza intra-cluster `Δ(A,B) = (nA·nB)/(nA+nB) · ‖μA−μB‖²`. Mejor para texto.
- **Correlación cofenética:** mide qué tan bien el dendrograma preserva las distancias originales. Valor > 0.75 = coherente. Ward suele dar el valor más alto.
- **Archivos clave:** `src/clustering/hierarchical.py`, `src/clustering/dendrogram.py`, `src/clustering/vectorizer.py`.

---

### R5 — Visualización de la producción científica

**Qué pedía:** mapa de calor geográfico, nube de palabras dinámica, línea temporal, exportar PDF.

**Qué se hizo:**
- **Mapa:** país del primer autor resuelto vía DOI → CrossRef API → caché JSON local. Coroplético con Plotly.
- **Nube de palabras:** generada con `wordcloud` desde abstracts + keywords. Dinámica: se regenera con cada cambio del corpus.
- **Línea temporal:** publicaciones por año + top 10 revistas por año.
- **Exportación PDF:** `fpdf2` + `kaleido` (Plotly → PNG). Portada + secciones por figura.
- **Archivos clave:** `src/visualization/`.

---

### R6 — Despliegue y documentación

**Qué pedía:** app desplegada, documentación técnica por requerimiento.

**Qué se hizo:**
- **URL:** https://bibliometria-genai.streamlit.app
- **Documentación técnica:** `docs/informe_final.md` — arquitectura, implementación detallada R1-R6, uso de IA, conclusiones.
- **Pruebas:** 184 tests con pytest (datos_sources, processing, similarity, analysis, clustering, visualization).
- **Archivos de despliegue:** `requirements.txt`, `packages.txt`, `.streamlit/config.toml`.

---

## Estructura del repositorio

```
app/             ← Interfaz Streamlit (main.py + 8 vistas)
src/
  data_sources/  ← OpenAlex API + parser BibTeX
  processing/    ← deduplicación, normalización, unificación
  similarity/    ← 6 algoritmos de similitud
  analysis/      ← frecuencia de conceptos, extracción de palabras, evaluación
  clustering/    ← clustering jerárquico + dendrograma
  visualization/ ← mapa, nube, timeline, PDF
data/processed/  ← unified.csv (225), duplicates.csv (128)
docs/            ← informe_final.md
tests/           ← 184 pruebas automatizadas
```

---

## Instalación local

```bash
pip install -r requirements.txt
pip install -e . --no-deps
streamlit run app/main.py
```

La app queda en `http://localhost:8501`.

### Datos de entrada

- **API automática:** buscar desde la sección `Búsqueda API` en la app.
- **BibTeX complementario:**
  - `data/raw/sciencedirect/` ← archivos `.bib` de ScienceDirect
  - `data/raw/academicsearchultimate/` ← archivos `.bibtex` de EBSCO

Si `data/processed/unified.csv` no existe al arrancar, el sistema lo genera automáticamente.

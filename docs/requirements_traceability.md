# Trazabilidad de Requerimientos R1-R6

Referencia: [Proyecto Análisis de Algoritmos.pdf](</home/lycan/Downloads/context ProyectoAnalisis/Proyecto Análisis de Algoritmos.pdf>)

## R1. Automatización de descarga y unificación

### Estado actual

Cumplimiento funcional con decisión de diseño.

### Implementado

- búsqueda automatizada de artículos mediante OpenAlex API;
- transformación automática del JSON de OpenAlex al formato interno del proyecto;
- parseo de archivos BibTeX desde dos carpetas de entrada;
- unificación en `data/processed/unified.csv`;
- registro de duplicados en `data/processed/duplicates.csv`;
- integración de resultados API y de exportaciones BibTeX en un mismo corpus.

### Justificación técnica

La automatización principal del proyecto se resolvió mediante OpenAlex, una fuente
académica pública consultable por API, lo que evita depender de credenciales
institucionales o flujos frágiles de scraping sobre plataformas privadas.

Además, el sistema conserva compatibilidad con archivos `.bib` y `.bibtex`
exportados desde bases como ScienceDirect y EBSCO Academic Search Ultimate.
Esto permite complementar el corpus con las bases recomendadas por el curso sin
exponer credenciales en el código ni acoplar la solución a mecanismos de acceso
propietarios de la universidad.

En esta arquitectura:

- OpenAlex actúa como fuente automatizada principal.
- Las bases institucionales actúan como fuentes complementarias mediante exportación.

### Archivos clave

- `src/data_sources/api_source.py`
- `src/data_sources/bibtex_parser.py`
- `src/processing/unifier.py`
- `src/processing/deduplication.py`

## R2. Cuatro algoritmos clásicos y dos con IA

### Estado actual

Cumplimiento funcional.

### Implementado

- Levenshtein
- Jaccard
- Cosine TF-IDF
- BM25
- LSI
- Sentence Embeddings con respaldo offline

### Archivos clave

- `src/similarity/`
- `app/views/similarity.py`

## R3. Frecuencia de conceptos y palabras asociadas

### Estado actual

Cumplimiento funcional.

### Implementado

- frecuencia de términos del dominio;
- extracción de palabras asociadas;
- evaluación de precisión, recall y F1.

### Archivos clave

- `src/analysis/`
- `app/views/concepts.py`

## R4. Clustering jerárquico

### Estado actual

Cumplimiento funcional.

### Implementado

- métodos `single`, `complete` y `ward`;
- cálculo de correlación cofenética;
- dendrograma;
- estrategia `two-tier` para corpus grandes.

### Archivos clave

- `src/clustering/`
- `app/views/clustering.py`

## R5. Visualización de producción científica

### Estado actual

Cumplimiento funcional con dependencia externa.

### Implementado

- línea temporal por año;
- línea temporal top 10 por revista;
- nube de palabras;
- mapa geográfico por primer autor;
- exportación PDF.

### Riesgos

- el mapa depende de CrossRef y puede degradarse por red o completitud de DOI;
- la exportación de figuras Plotly depende de `kaleido`.

### Archivos clave

- `src/visualization/`
- `app/views/visualization.py`
- `app/views/export_pdf.py`

## R6. Despliegue y documentación

### Estado actual

Cumplimiento parcial.

### Implementado

- aplicación ejecutable con Streamlit;
- `README.md`;
- pruebas automatizadas con `pytest`.

### Brecha

Faltaba documentación técnica en `docs/`; este directorio ya tiene una base, pero
todavía conviene ampliarlo con decisiones de diseño por algoritmo y evidencias de despliegue.

## Riesgos abiertos prioritarios

1. La automatización de R1 depende de OpenAlex como fuente pública principal y no de acceso directo a portales institucionales.
2. Dependencia de servicios externos para OpenAlex y CrossRef.
3. Falta de una política única de logging y observabilidad.

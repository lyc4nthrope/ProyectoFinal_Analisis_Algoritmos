# Arquitectura Técnica

## Resumen

El proyecto está organizado en dos capas principales:

- `app/`: interfaz Streamlit y orquestación de interacción.
- `src/`: lógica de dominio, acceso a datos, procesamiento, análisis y exportación.

La regla aplicada en este refactor es:

- las vistas no deben leer o escribir archivos directamente salvo para descarga final al usuario;
- la lógica de negocio y persistencia debe vivir en `src/`.

## Estructura actual

```text
app/
  main.py
  loader.py
  views/

src/
  analysis/
  clustering/
  data_sources/
  processing/
  repositories/
  services/
  similarity/
  visualization/
```

## Responsabilidades por módulo

### `app/`

- `main.py`: navegación y configuración general de Streamlit.
- `loader.py`: carga cacheada del corpus y de analizadores para la sesión.
- `views/`: presentación y captura de acciones del usuario.

### `src/data_sources/`

- `bibtex_parser.py`: parseo de exportaciones BibTeX.
- `api_source.py`: cliente de OpenAlex con paginación y reintentos.

OpenAlex es la fuente automatizada principal del proyecto. La decisión de usar
esta API pública permite automatizar la recolección sin almacenar credenciales
institucionales ni depender de automatización web sobre portales privados.
Las exportaciones BibTeX desde ScienceDirect o EBSCO se mantienen como una vía
complementaria compatible con la misma tubería de procesamiento.

### `src/processing/`

- `unifier.py`: descubrimiento de archivos, carga, mezcla y deduplicación.
- `deduplication.py`: eliminación de duplicados.
- `text_preprocessing.py`: normalización y tokenización compartidas.

### `src/repositories/`

- `corpus_repository.py`: lectura, integración y limpieza del corpus persistido.

### `src/services/`

- `api_search_service.py`: reglas de paginación de búsqueda API.
- `api_search_store.py`: persistencia temporal de resultados de búsqueda API en JSONL.

### `src/similarity/`

- implementación de 6 algoritmos.
- `similarity_analyzer.py`: fachada para comparación, top-k y matrices.

### `src/clustering/`

- vectorización, clustering jerárquico, dendrogramas y análisis integrador.

### `src/analysis/`

- frecuencia de conceptos, extracción de términos y evaluación.

### `src/visualization/`

- generación de figuras, resolución geográfica y exportación a PDF.

## Decisiones recientes

### 1. Separación de persistencia desde la UI

Antes:

- `app/views/api_search.py` escribía JSONL, leía slices y fusionaba `unified.csv`.
- `app/views/overview.py` borraba `unified.csv` directamente.

Ahora:

- `src/services/api_search_store.py` administra JSONL temporal.
- `src/repositories/corpus_repository.py` administra el corpus persistido.

### 2. Robustez offline en similitud con IA

`sentence_embedding_similarity.py` ahora intenta cargar el modelo de forma local.
Si no existe caché local del modelo, hace degradación controlada a un respaldo TF-IDF
para que la aplicación y las pruebas no dependan de internet.

### 3. Eliminación de acceso a atributos privados desde vistas

Las vistas ya no deben depender de `_algorithms`, `_titles` o `_corpus`.
Se expusieron interfaces públicas mínimas en los analizadores.

## Deuda técnica restante

- `app/views/visualization.py` y `app/views/export_pdf.py` todavía contienen orquestación algo densa que puede extraerse a servicios.
- `src/processing/unifier.py` sigue dependiendo de archivos BibTeX ya exportados manualmente.
- falta una estrategia de logging estructurado; hoy predominan mensajes simples y errores directos a UI.

## Entorno recomendado

Para el equipo se recomienda fijar Python 3.11 y usar:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .[dev]
streamlit run app/main.py
```

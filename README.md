# Proyecto Final - Analisis de Algoritmos

## Descripcion general del proyecto

En este proyecto se busca desarrollar una aplicacion orientada al analisis bibliometrico de publicaciones cientificas relacionadas con el tema **"generative artificial intelligence"**. La idea principal es tomar informacion proveniente de bases de datos academicas, organizarla, limpiarla y despues aplicar distintos algoritmos para analizar el contenido de los articulos, especialmente sus **abstracts**, palabras clave, autores, revistas y anos de publicacion.

Este proyecto no se trata solo de construir una aplicacion que muestre datos, sino de entender como los **algoritmos** pueden ayudar a estudiar la produccion cientifica en un dominio especifico del conocimiento. En este caso, el dominio escogido es la inteligencia artificial generativa, un tema actual y con mucha produccion academica.

## De que trata el proyecto

Este proyecto trata sobre aplicar conceptos de **analisis de algoritmos**, **mineria de texto**, **procesamiento de lenguaje natural** y **visualizacion de datos** en el contexto de la bibliometria. La bibliometria es el area que permite estudiar publicaciones cientificas mediante tecnicas cuantitativas y cualitativas. Gracias a ella es posible identificar patrones, tendencias, relaciones entre autores, temas frecuentes, evolucion temporal de publicaciones y similitud entre documentos.

Lo que se espera construir es una herramienta capaz de:

- Obtener informacion de al menos dos bases de datos cientificas.
- Unificar los registros en un solo conjunto de datos.
- Detectar y eliminar duplicados.
- Comparar articulos mediante algoritmos de similitud textual.
- Analizar la frecuencia de conceptos importantes dentro de los abstracts.
- Agrupar articulos segun su semejanza tematica.
- Generar visualizaciones que permitan interpretar mejor la produccion cientifica.

En otras palabras, el proyecto busca transformar un conjunto grande de articulos cientificos en informacion organizada, analizable y visualmente comprensible.

## Para que sirve

El proyecto sirve para comprender mejor como se esta investigando el tema de la inteligencia artificial generativa dentro de la literatura cientifica. No se trata unicamente de recopilar articulos, sino de responder preguntas importantes como:

- Que articulos se parecen mas entre si.
- Que conceptos aparecen con mayor frecuencia.
- Que palabras nuevas pueden surgir como relevantes dentro del conjunto de abstracts.
- Como se agrupan los documentos segun su contenido.
- De que paises provienen los autores.
- Como evoluciona la produccion cientifica con el paso del tiempo.

Por eso, el valor del proyecto esta en combinar una vision academica con una implementacion tecnica que permita analizar informacion real.

## Objetivo principal

El objetivo con este proyecto es implementar una aplicacion que permita realizar un **analisis bibliometrico y computacional** sobre publicaciones cientificas relacionadas con inteligencia artificial generativa, apoyandome en distintos algoritmos de comparacion, agrupamiento y analisis textual.

Tambien que el proyecto no quede solo en el nivel teorico, sino que pueda ser desplegado y documentado correctamente, de manera que cualquier persona pueda entender su arquitectura, su funcionamiento y las decisiones tecnicas tomadas durante el desarrollo.

## Requerimientos del proyecto explicados

### 1. Automatizacion de la descarga y unificacion de datos

El primer requerimiento consiste en automatizar la obtencion de informacion desde dos bases de datos cientificas. Despues de descargar los resultados, unificar toda la informacion en un solo archivo, evitando que un mismo producto aparezca repetido.

Esto significa que si un articulo se encuentra en ambas fuentes, el sistema debe identificarlo, consolidar su informacion y dejar una sola instancia valida. Ademas, tambien hay que generar otro archivo donde queden registrados los productos duplicados que fueron eliminados.

Este punto es importante porque antes de analizar cualquier informacion se necesita tener un conjunto de datos limpio, consistente y bien estructurado.

### 2. Implementacion de algoritmos de similitud textual

En este requerimiento se debe implementar **cuatro algoritmos clasicos de similitud textual** y **dos algoritmos basados en inteligencia artificial**. La aplicacion debe permitir seleccionar dos o mas articulos, extraer sus abstracts y comparar que tan similares son entre si.

Aqui no basta con obtener un resultado numerico. Tambien debo explicar de manera detallada el funcionamiento matematico y algoritmico de cada metodo, mostrando paso a paso como se calcula la similitud.

Este requerimiento es importante porque permite estudiar diferentes formas de comparar textos y analizar cual enfoque resulta mas util dentro del contexto bibliometrico.

### 3. Analisis de frecuencia de conceptos y nuevas palabras asociadas

En este punto hay que trabajar con una categoria especifica: **Concepts of Generative AI in Education**, junto con una lista de palabras asociadas como:

- Generative models
- Prompting
- Machine learning
- Multimodality
- Fine-tuning
- Training data
- Algorithmic bias
- Explainability
- Transparency
- Ethics
- Privacy
- Personalization
- Human-AI interaction
- AI literacy
- Co-creation

Lo que hay que hacer es calcular cuantas veces aparecen esas palabras dentro de los abstracts de los articulos. Luego, debo aplicar un algoritmo que analice todos los abstracts y genere un listado de nuevas palabras asociadas, con un maximo de 15 terminos. Finalmente, determinar que tan precisas son esas nuevas palabras generadas.

Este requerimiento combina conteo de frecuencia, extraccion de terminos relevantes y evaluacion de resultados.

### 4. Agrupamiento jerarquico de abstracts

Aqui se debe implementar **tres algoritmos de clustering jerarquico** para construir un dendrograma que represente la similitud entre abstracts cientificos. Para lograrlo, primero hay que hacer un preprocesamiento del texto, luego calcular una medida de similitud o distancia, despues aplicar los algoritmos de agrupamiento y finalmente representar visualmente los grupos obtenidos.

Ademas, se debe analizar cual de los algoritmos produce agrupamientos mas coherentes. Este punto es clave porque no solo implica programar, sino tambien interpretar la calidad de los resultados.

### 5. Visualizacion de la produccion cientifica

Este requerimiento busca presentar la informacion de forma visual. Debo desarrollar:

- Un mapa de calor con la distribucion geografica segun el primer autor del articulo.
- Una nube de palabras con los terminos mas frecuentes en abstracts y keywords.
- Una linea temporal de publicaciones por ano y por revista.
- La exportacion de estas visualizaciones a formato PDF.

Esta parte del proyecto es importante porque convierte los datos procesados en resultados faciles de interpretar y comunicar.

### 6. Despliegue y documentacion

Finalmente, el proyecto debe quedar desplegado y respaldado con documentacion tecnica. Esto significa que no solo debo hacer que la aplicacion funcione, sino tambien explicar claramente su arquitectura, los componentes que la integran, los algoritmos usados y la forma en que se resolvio cada requerimiento.

Esta parte es fundamental porque demuestra que el proyecto fue desarrollado con una estructura clara y con criterio de ingenieria.


## Lenguaje usado: Python

Python es util para este proyecto por varias razones:

- Tiene librerias muy buenas para manejo de datos, como `pandas`.
- Permite trabajar con procesamiento de texto usando herramientas como `nltk`, `spacy` y `scikit-learn`.
- Facilita la implementacion de algoritmos de similitud y clustering.
- Tiene soporte para modelos de inteligencia artificial y embeddings con librerias como `transformers` o `sentence-transformers`.
- Permite crear graficos, mapas y reportes con librerias como `matplotlib`, `seaborn`, `plotly`, `folium` y `wordcloud`.
- Tambien permite crear una aplicacion web de manera relativamente sencilla con `Streamlit`, `Flask` o `FastAPI`.

En general, Python nos da un entorno muy completo para resolver tanto la parte algoritmica como la parte visual del proyecto.

## Enfoque de desarrollo en Python

La estructura es en modulos:

- `data_sources/`: para la descarga o importacion de informacion desde bases de datos.
- `processing/`: para limpieza, normalizacion y eliminacion de duplicados.
- `similarity/`: para implementar algoritmos clasicos y algoritmos con IA.
- `analysis/`: para frecuencia de terminos y palabras asociadas.
- `clustering/`: para agrupamiento jerarquico y construccion de dendrogramas.
- `visualization/`: para mapas, nube de palabras, linea temporal y exportacion.
- `app/`: para la interfaz de usuario.
- `docs/`: para la documentacion tecnica y academica.

## Estructura de carpetas del proyecto

Se debe organizar el repositorio con una estructura inicial que permita separar responsabilidades desde el comienzo:

```text
ProyectoFinal_Analisis_Algoritmos/
├── app/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
├── exports/
├── src/
│   ├── analysis/
│   ├── clustering/
│   ├── data_sources/
│   ├── processing/
│   ├── similarity/
│   └── visualization/
└── tests/
```

Significado de las carpetas, es decir, la estructura del proyecto:

- `app/`: aqui puedo desarrollar la interfaz o punto de entrada de la aplicacion.
- `data/raw/`: aqui puedo guardar los archivos originales descargados desde las bases de datos.
- `data/processed/`: aqui puedo almacenar los datos ya limpios, unificados y sin duplicados.
- `docs/`: aqui puedo guardar la documentacion tecnica, arquitectura, explicaciones de algoritmos y evidencias.
- `exports/`: aqui puedo generar los PDF y otros resultados exportados por la aplicacion.
- `src/data_sources/`: aqui puedo implementar la automatizacion de descarga o importacion de datos.
- `src/processing/`: aqui puedo trabajar limpieza, normalizacion y deduplicacion.
- `src/similarity/`: aqui puedo implementar los algoritmos clasicos y los algoritmos con IA para similitud textual.
- `src/analysis/`: aqui puedo desarrollar el analisis de frecuencia y la extraccion de palabras asociadas.
- `src/clustering/`: aqui puedo implementar el agrupamiento jerarquico y los dendrogramas.
- `src/visualization/`: aqui puedo construir mapas, nubes de palabras y lineas temporales.
- `tests/`: aqui puedo organizar las pruebas del proyecto.

## Como funciona la estructura de carpetas

La estructura de carpetas del proyecto va a funcionar separando cada parte segun su responsabilidad. Considerando que esta organizacion es importante porque evita mezclar datos, codigo fuente, documentacion, resultados exportados y pruebas en un mismo lugar. De esta forma, el proyecto se vuelve mas claro, mas facil de mantener y tambien mas facil de trabajar en equipo.

En este caso, la estructura quedo organizada con **6 carpetas principales**:

- `app/`
- `data/`
- `docs/`
- `exports/`
- `src/`
- `tests/`

Si ademas cuento las subcarpetas internas que ya hacen parte de la base del proyecto, entonces en total salen **14 carpetas**:

- `app/`
- `data/`
- `data/raw/`
- `data/processed/`
- `docs/`
- `exports/`
- `src/`
- `src/data_sources/`
- `src/processing/`
- `src/similarity/`
- `src/analysis/`
- `src/clustering/`
- `src/visualization/`
- `tests/`

## Para que sirve cada carpeta

El uso de cada carpeta de la siguiente manera:

- `app/`: aqui iria la aplicacion principal o la interfaz desde donde se ejecuta el sistema.
- `data/`: aqui se concentra toda la informacion usada por el proyecto.
- `data/raw/`: aqui se guardan los datos originales descargados desde las bases de datos, sin modificar.
- `data/processed/`: aqui se almacenan los datos ya limpios, unificados y listos para el analisis.
- `docs/`: aqui se organiza la documentacion tecnica, academica y arquitectonica del proyecto.
- `exports/`: aqui se guardan los resultados generados por la aplicacion, como PDF, reportes o salidas visuales.
- `src/`: aqui vive el codigo fuente principal del sistema.
- `src/data_sources/`: aqui se implementa la carga o automatizacion de obtencion de datos.
- `src/processing/`: aqui se trabaja la limpieza, normalizacion y eliminacion de duplicados.
- `src/similarity/`: aqui se implementan los algoritmos de similitud textual.
- `src/analysis/`: aqui se desarrolla el analisis de frecuencia y deteccion de palabras asociadas.
- `src/clustering/`: aqui se implementa el agrupamiento jerarquico y los dendrogramas.
- `src/visualization/`: aqui se construyen los componentes visuales del proyecto.
- `tests/`: aqui se ubican las pruebas para validar el comportamiento del sistema.

## Ramas propuestas para el equipo

Teniendo en cuenta que en el proyecto estamos **Cristhian Eduardo Osorio Restrepo y Daniel Stiven Perez Cordoba**, la base de ramas queda planteada de esta forma:

- `main`
- `develop`
- `feature/cristhian`
- `feature/daniel`
- `release/preproduccion`
- `hotfix/produccion`

Considerando que esta organizacion es util porque permite que cada integrante avance en su propia rama de trabajo y despues integre cambios en `develop`. Una vez el proyecto este mas estable, los cambios pueden pasar a `release/preproduccion` para validacion, y cuando todo este aprobado, se publica en `main`. Si aparece un error critico, se corrige directamente desde `hotfix/produccion`.

## Flujo de trabajo que seguire

La idea de trabajo seria la siguiente:

1. Cada integrante desarrolla sus tareas en su propia rama `feature`.
2. Cuando una parte este lista, se integra en `develop`.
3. Cuando se quiera preparar una entrega, se pasa a `release/preproduccion`.
4. Si la validacion es correcta, se publica en `main`.
5. Si surge un problema urgente en produccion, se usa `hotfix/produccion`.

Este flujo ayuda a trabajar de manera mas organizada y reduce el riesgo de dañar la version estable del proyecto.

## Conclusion

En conclusion, este proyecto busca aplicar algoritmos al analisis de publicaciones cientificas sobre inteligencia artificial generativa, integrando recoleccion de datos, limpieza, comparacion textual, agrupamiento, visualizacion y documentacion. Es un proyecto academico bastante completo, porque combina teoria, implementacion y capacidad de analisis.

---

## Instalacion y ejecucion

### Requisitos previos

- Python 3.11 o superior
- pip

### Pasos

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Instalar el proyecto en modo editable (resuelve imports entre modulos)
pip install -e . --no-deps

# 3. Instalar Chrome para exportacion de graficas a PNG (solo una vez)
#    Cuando el comando pregunte, responder 'y'
plotly_get_chrome

# 4. Ejecutar la aplicacion
streamlit run app/main.py
```

La aplicacion queda disponible en `http://localhost:8501`.

### Datos de entrada

La aplicación admite dos formas de ingesta:

- **Automática vía API**: búsqueda en OpenAlex desde la sección `Búsqueda API`.
- **Complementaria vía exportación**: archivos BibTeX descargados desde bases como ScienceDirect o EBSCO.

Los archivos BibTeX de las bases de datos deben ubicarse en:

```
data/raw/sciencedirect/         <- archivos .bib de ScienceDirect
data/raw/academicsearchultimate/ <- archivos .bibtex de EBSCO Academic Search Ultimate
```

Si `data/processed/unified.csv` no existe al arrancar la app, el sistema lo genera automaticamente.

---

## Arquitectura tecnica

### Flujo de datos

```
OpenAlex API / BibTeX exportado
          -> src/data_sources/ + src/processing/
          -> data/processed/unified.csv
          -> src/similarity/ / src/analysis/ / src/clustering/ / src/visualization/
          -> app/main.py
```

### Descripcion de modulos

| Modulo | Archivo(s) | Responsabilidad |
|--------|-----------|-----------------|
| **R1 — Ingesta API** | `src/data_sources/api_source.py` | Consulta OpenAlex, pagina resultados y transforma JSON al formato interno |
| **R1 — Ingesta BibTeX** | `src/data_sources/bibtex_parser.py` | Parsea archivos BibTeX de cualquier fuente |
| **R1 — Deduplicacion** | `src/processing/deduplication.py` | Exact match O(1) + Levenshtein con umbral 0.90 |
| **R1 — Unificador** | `src/processing/unifier.py` | Orquesta descubrimiento, carga y guardado del corpus |
| **R1 — Preprocesamiento** | `src/processing/text_preprocessing.py` | `normalize()`, `tokenize()`, `to_string()` compartidos |
| **R2 — Similitud** | `src/similarity/` | 6 algoritmos: Levenshtein, Jaccard, Cosine TF-IDF, BM25, LSI, Sentence Embeddings |
| **R3 — Conceptos** | `src/analysis/concept_frequency.py` | Frecuencia de 15 conceptos GenAI via regex |
| **R3 — Palabras** | `src/analysis/word_extractor.py` | Top-15 terminos por TF-IDF con bigramas |
| **R3 — Evaluacion** | `src/analysis/precision_evaluator.py` | Precision / Recall / F1 sobre terminos extraidos |
| **R4 — Clustering** | `src/clustering/hierarchical.py` | Single, Complete y Ward linkage con correlacion cofenotica |
| **R4 — Dendrograma** | `src/clustering/dendrogram.py` | Figura matplotlib a partir del resultado de clustering |
| **R5 — Heatmap** | `src/visualization/geo_heatmap.py` | Mapa coropletico Plotly; paises resueltos via CrossRef |
| **R5 — Wordcloud** | `src/visualization/wordcloud_chart.py` | Nube de palabras desde abstracts y keywords |
| **R5 — Timeline** | `src/visualization/timeline_chart.py` | Publicaciones por anio y por revista (top 10) |
| **R5 — PDF** | `src/visualization/pdf_exporter.py` | Exporta figuras Plotly/Matplotlib a un PDF con portada |
| **R6 — App** | `app/main.py` + `app/views/` | Interfaz Streamlit con 6 secciones y caching de analyzers |

### Decisiones de diseno relevantes

- **Patron Strategy** en `src/similarity/`: cada algoritmo implementa `BaseSimilarity` con `fit()` y `compute_pair()`.
- **Caching lazy** en `app/loader.py`: `@st.cache_resource` garantiza que `SimilarityAnalyzer` y `ClusteringAnalyzer` se inicializan una sola vez por sesion, independientemente de cuantas veces el usuario navegue entre paginas.
- **L2-normalizacion** en vectorizacion TF-IDF para clustering: permite usar distancia euclidiana que equivale a distancia coseno cuando `||v||=1`, requisito de Ward linkage.
- **Cache local JSON** en `src/visualization/geo_resolver.py`: evita repetir llamadas a la API de CrossRef para DOIs ya resueltos.
- **Instalacion editable** via `pyproject.toml`: elimina la necesidad de `sys.path` hacks en cualquier modulo.

### Bases de datos utilizadas

| Fuentes                        |

| ScienceDirect                  |
| EBSCO Academic Search Ultimate |

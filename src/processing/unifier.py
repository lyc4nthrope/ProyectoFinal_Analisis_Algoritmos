# Importa Callable para tipar funciones callback que se pasan como argumento
from collections.abc import Callable
# Importa Path para manejo de rutas del sistema de archivos
from pathlib import Path

# Importa pandas para crear y guardar DataFrames en CSV
import pandas as pd
# Importa requests para capturar errores de red al consultar la API
import requests

# Importa rutas de configuración del proyecto
from src.config import RAW_DIR, PROCESSED_DIR, SUPPORTED_EXTENSIONS
# Importa el parser de la API de OpenAlex
from src.data_sources import ApiParser
# Importa el parser de archivos BibTeX
from src.data_sources.bibtex_parser import BibtexFileParser
# Importa la función de deduplicación de artículos
from src.processing.deduplication import deduplicate


def discover_files(raw_dir: Path) -> list[tuple[str, Path]]:
    # Lista para acumular los archivos encontrados
    found = []
    # Recorre cada subcarpeta de data/raw/ en orden alfabético (cada una es una fuente)
    for source_dir in sorted(raw_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        # Dentro de cada fuente, busca archivos con extensión BibTeX soportada
        for file_path in sorted(source_dir.iterdir()):
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                # Guarda el nombre de la fuente y la ruta del archivo
                found.append((source_dir.name, file_path))
    return found


def load_articles(files: list[tuple[str, Path]]) -> list[dict]:
    # Acumula todos los artículos de todas las fuentes
    all_articles = []
    for source_name, file_path in files:
        # Crea un parser BibTeX con el nombre de la fuente para etiquetar los artículos
        parser = BibtexFileParser(source_name=source_name)
        articles = parser.parse(str(file_path))
        print(f"  {source_name}: {len(articles)} artículos leídos de {file_path.name}")
        all_articles.extend(articles)
    return all_articles


def save_results(unique: list[dict], duplicates: list[dict], processed_dir: Path) -> None:
    # Crea el directorio de salida si no existe
    processed_dir.mkdir(parents=True, exist_ok=True)
    # Guarda los artículos únicos en unified.csv con comillas en todos los campos (quoting=1)
    pd.DataFrame(unique).to_csv(processed_dir / "unified.csv", index=False, encoding="utf-8", quoting=1)
    # Guarda los duplicados detectados en duplicates.csv
    pd.DataFrame(duplicates).to_csv(processed_dir / "duplicates.csv", index=False, encoding="utf-8", quoting=1)


def run(api_query: str | None = None, on_api_error: Callable | None = None) -> None:
    # Descubre todos los archivos BibTeX en data/raw/
    files = discover_files(RAW_DIR)
    if not files:
        print("No se encontraron archivos .bib o .bibtex en data/raw/")
        return

    # Carga todos los artículos de los archivos encontrados
    articles = load_articles(files)
    print(f"\nTotal antes de deduplicación: {len(articles)}")

    # Consulta la API de OpenAlex (si hay query) y fusiona los resultados
    articles = fetch_and_merge_api(articles, api_query, on_error=on_api_error)

    # Elimina duplicados y obtiene las dos listas: únicos y duplicados
    unique, duplicates = deduplicate(articles)
    print(f"Artículos únicos:    {len(unique)}")
    print(f"Duplicados:          {len(duplicates)}")

    # Guarda los resultados en los archivos CSV de salida
    save_results(unique, duplicates, PROCESSED_DIR)
    print(f"\nArchivos generados en: {PROCESSED_DIR}")


def fetch_and_merge_api(
    articles: list[dict],
    query: str | None = None,
    max_results: int = 25,
    on_error: Callable | None = None,
    direct_results: list[dict] | None = None,
) -> list[dict]:
    # Si se proporcionan resultados directos (ya buscados), simplemente los agrega
    if direct_results is not None:
        articles.extend(direct_results)
        return articles

    # Si no hay query o está vacío, devuelve los artículos sin modificar
    if not query or not query.strip():
        return articles

    # Crea el parser de la API y busca artículos en OpenAlex
    parser = ApiParser()
    try:
        api_results = parser.search(query, max_results)
        articles.extend(api_results)
    except (ConnectionError, requests.HTTPError) as e:
        # Si hay error de red, notifica al callback (si existe) pero no interrumpe
        if on_error:
            on_error(f"No se pudieron obtener resultados de OpenAlex: {e}")
    return articles


# Permite ejecutar el pipeline directamente desde la línea de comandos
if __name__ == "__main__":
    run()

from collections.abc import Callable
from pathlib import Path

import pandas as pd
import requests

from src.config import RAW_DIR, PROCESSED_DIR, SUPPORTED_EXTENSIONS
from src.data_sources import ApiParser
from src.data_sources.bibtex_parser import BibtexFileParser
from src.processing.deduplication import deduplicate


def discover_files(raw_dir: Path) -> list[tuple[str, Path]]:
    found = []
    for source_dir in sorted(raw_dir.iterdir()):
        if not source_dir.is_dir():
            continue
        for file_path in sorted(source_dir.iterdir()):
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                found.append((source_dir.name, file_path))
    return found


def load_articles(files: list[tuple[str, Path]]) -> list[dict]:
    all_articles = []
    for source_name, file_path in files:
        parser = BibtexFileParser(source_name=source_name)
        articles = parser.parse(str(file_path))
        print(f"  {source_name}: {len(articles)} artículos leídos de {file_path.name}")
        all_articles.extend(articles)
    return all_articles


def save_results(unique: list[dict], duplicates: list[dict], processed_dir: Path) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(unique).to_csv(processed_dir / "unified.csv", index=False, encoding="utf-8", quoting=1)
    pd.DataFrame(duplicates).to_csv(processed_dir / "duplicates.csv", index=False, encoding="utf-8", quoting=1)


def run(api_query: str | None = None, on_api_error: Callable | None = None) -> None:
    files = discover_files(RAW_DIR)
    if not files:
        print("No se encontraron archivos .bib o .bibtex en data/raw/")
        return

    articles = load_articles(files)
    print(f"\nTotal antes de deduplicación: {len(articles)}")

    articles = fetch_and_merge_api(articles, api_query, on_error=on_api_error)

    unique, duplicates = deduplicate(articles)
    print(f"Artículos únicos:    {len(unique)}")
    print(f"Duplicados:          {len(duplicates)}")

    save_results(unique, duplicates, PROCESSED_DIR)
    print(f"\nArchivos generados en: {PROCESSED_DIR}")


def fetch_and_merge_api(
    articles: list[dict],
    query: str | None = None,
    max_results: int = 25,
    on_error: Callable | None = None,
    direct_results: list[dict] | None = None,
) -> list[dict]:
    if direct_results is not None:
        articles.extend(direct_results)
        return articles

    if not query or not query.strip():
        return articles

    parser = ApiParser()
    try:
        api_results = parser.search(query, max_results)
        articles.extend(api_results)
    except (ConnectionError, requests.HTTPError) as e:
        if on_error:
            on_error(f"No se pudieron obtener resultados de OpenAlex: {e}")
    return articles


if __name__ == "__main__":
    run()

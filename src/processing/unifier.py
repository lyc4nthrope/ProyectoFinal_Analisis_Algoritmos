from pathlib import Path

import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR, SUPPORTED_EXTENSIONS
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
    pd.DataFrame(unique).to_csv(processed_dir / "unified.csv", index=False, encoding="utf-8")
    pd.DataFrame(duplicates).to_csv(processed_dir / "duplicates.csv", index=False, encoding="utf-8")


def run() -> None:
    files = discover_files(RAW_DIR)
    if not files:
        print("No se encontraron archivos .bib o .bibtex en data/raw/")
        return

    articles = load_articles(files)
    print(f"\nTotal antes de deduplicación: {len(articles)}")

    unique, duplicates = deduplicate(articles)
    print(f"Artículos únicos:    {len(unique)}")
    print(f"Duplicados:          {len(duplicates)}")

    save_results(unique, duplicates, PROCESSED_DIR)
    print(f"\nArchivos generados en: {PROCESSED_DIR}")


if __name__ == "__main__":
    run()

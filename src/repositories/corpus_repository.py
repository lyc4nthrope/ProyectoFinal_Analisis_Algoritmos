from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DIR

CORPUS_PATH = PROCESSED_DIR / "unified.csv"
DUPLICATES_PATH = PROCESSED_DIR / "duplicates.csv"


def load_corpus_df(path: Path = CORPUS_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, on_bad_lines="skip").fillna("")


def load_duplicates_df(path: Path = DUPLICATES_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, on_bad_lines="skip").fillna("")


def integrate_articles(
    articles: list[dict],
    path: Path = CORPUS_PATH,
) -> tuple[int, int]:
    """Merge new articles into the corpus and deduplicate by DOI/title."""
    incoming = pd.DataFrame(articles)
    if incoming.empty:
        return 0, len(load_corpus_df(path))

    existing = load_corpus_df(path)
    corpus = pd.concat([existing, incoming], ignore_index=True).fillna("")
    corpus, new_dups = _deduplicate_rows(corpus)

    path.parent.mkdir(parents=True, exist_ok=True)
    corpus.to_csv(path, index=False, quoting=1)

    if not new_dups.empty:
        dups_path = path.parent / "duplicates.csv"
        existing_dups = load_duplicates_df(dups_path)
        all_dups = pd.concat([existing_dups, new_dups], ignore_index=True)
        all_dups.to_csv(dups_path, index=False, quoting=1)

    return len(incoming), len(corpus)


def clear_corpus(path: Path = CORPUS_PATH) -> bool:
    if not path.exists():
        return False
    path.unlink()
    dups_path = path.parent / "duplicates.csv"
    if dups_path.exists():
        dups_path.unlink()
    return True


def _deduplicate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = df.copy()

    if "doi" not in work.columns:
        work["doi"] = ""
    if "title" not in work.columns:
        work["title"] = ""

    work["_doi_key"] = work["doi"].astype(str).str.strip().str.lower()
    work["_title_key"] = (
        work["title"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )
    work["_dedup_key"] = work["_doi_key"]
    missing_doi = work["_dedup_key"] == ""
    work.loc[missing_doi, "_dedup_key"] = work.loc[missing_doi, "_title_key"]

    deduped = work.drop_duplicates(subset="_dedup_key", keep="first")
    duplicates = work.loc[work.index.difference(deduped.index)]

    clean_cols = ["_doi_key", "_title_key", "_dedup_key"]
    return (
        deduped.drop(columns=clean_cols),
        duplicates.drop(columns=clean_cols),
    )

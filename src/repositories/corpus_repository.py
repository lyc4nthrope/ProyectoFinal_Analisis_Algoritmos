from __future__ import annotations

# Importa Path para manejo de rutas del sistema de archivos
from pathlib import Path

# Importa pandas para leer y escribir los archivos CSV del corpus
import pandas as pd

# Importa las rutas configuradas para el corpus y los duplicados
from src.config import PROCESSED_DIR

# Ruta del archivo principal del corpus (artículos únicos deduplicados)
CORPUS_PATH = PROCESSED_DIR / "unified.csv"
# Ruta del archivo que guarda los artículos detectados como duplicados
DUPLICATES_PATH = PROCESSED_DIR / "duplicates.csv"


def load_corpus_df(path: Path = CORPUS_PATH) -> pd.DataFrame:
    # Si el archivo no existe, retorna un DataFrame vacío (corpus aún no generado)
    if not path.exists():
        return pd.DataFrame()
    # Lee el CSV ignorando líneas mal formateadas; rellena NaN con "" para evitar errores
    return pd.read_csv(path, on_bad_lines="skip").fillna("")


def load_duplicates_df(path: Path = DUPLICATES_PATH) -> pd.DataFrame:
    # Si no hay archivo de duplicados, retorna DataFrame vacío
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, on_bad_lines="skip").fillna("")


def integrate_articles(
    articles: list[dict],
    path: Path = CORPUS_PATH,
) -> tuple[int, int]:
    """Merge new articles into the corpus and deduplicate by DOI/title."""
    # Convierte la lista de artículos nuevos a DataFrame
    incoming = pd.DataFrame(articles)
    if incoming.empty:
        # Si no hay artículos nuevos, retorna (0 insertados, total actual)
        return 0, len(load_corpus_df(path))

    # Carga el corpus existente (puede estar vacío si es la primera vez)
    existing = load_corpus_df(path)
    # Concatena los artículos existentes con los nuevos
    corpus = pd.concat([existing, incoming], ignore_index=True).fillna("")
    # Deduplica el corpus combinado usando DOI y título como claves
    corpus, new_dups = _deduplicate_rows(corpus)

    # Crea el directorio si no existe antes de guardar
    path.parent.mkdir(parents=True, exist_ok=True)
    corpus.to_csv(path, index=False, quoting=1)

    # Si hay duplicados nuevos, los agrega al archivo de duplicados existente
    if not new_dups.empty:
        existing_dups = load_duplicates_df()
        all_dups = pd.concat([existing_dups, new_dups], ignore_index=True)
        all_dups.to_csv(DUPLICATES_PATH, index=False, quoting=1)

    # Retorna cuántos artículos se insertaron y cuál es el total del corpus
    return len(incoming), len(corpus)


def clear_corpus(path: Path = CORPUS_PATH) -> bool:
    # Si no hay corpus, no hay nada que borrar
    if not path.exists():
        return False
    # Elimina el archivo principal del corpus
    path.unlink()
    # Elimina también el archivo de duplicados si existe
    if DUPLICATES_PATH.exists():
        DUPLICATES_PATH.unlink()
    return True


def _deduplicate_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    work = df.copy()

    # Asegura que las columnas doi y title existan aunque el DataFrame no las tenga
    if "doi" not in work.columns:
        work["doi"] = ""
    if "title" not in work.columns:
        work["title"] = ""

    # Normaliza el DOI para comparación: elimina espacios y pasa a minúsculas
    work["_doi_key"] = work["doi"].astype(str).str.strip().str.lower()
    # Normaliza el título: elimina espacios extra y pasa a minúsculas
    work["_title_key"] = (
        work["title"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )
    # La clave de deduplicación es el DOI si existe, o el título si el DOI está vacío
    work["_dedup_key"] = work["_doi_key"]
    missing_doi = work["_dedup_key"] == ""
    work.loc[missing_doi, "_dedup_key"] = work.loc[missing_doi, "_title_key"]

    # Mantiene solo la primera aparición de cada clave (elimina duplicados)
    deduped = work.drop_duplicates(subset="_dedup_key", keep="first")
    # Los duplicados son las filas que no están en el DataFrame deduplicado
    duplicates = work.loc[work.index.difference(deduped.index)]

    # Elimina las columnas auxiliares de deduplicación antes de retornar
    clean_cols = ["_doi_key", "_title_key", "_dedup_key"]
    return (
        deduped.drop(columns=clean_cols),
        duplicates.drop(columns=clean_cols),
    )

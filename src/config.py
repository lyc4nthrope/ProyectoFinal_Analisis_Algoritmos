from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

SUPPORTED_EXTENSIONS = {".bib", ".bibtex"}

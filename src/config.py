# Importa Path de pathlib para manejar rutas del sistema de archivos de forma portable
from pathlib import Path

# Calcula la raíz del proyecto subiendo dos niveles desde este archivo (src/config.py → raíz)
PROJECT_ROOT = Path(__file__).parent.parent

# Define la carpeta donde se guardan los archivos BibTeX originales sin procesar
RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Define la carpeta donde se guardan los archivos CSV procesados (unified.csv, duplicates.csv)
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Extensiones de archivo BibTeX que el sistema reconoce y puede procesar
SUPPORTED_EXTENSIONS = {".bib", ".bibtex"}

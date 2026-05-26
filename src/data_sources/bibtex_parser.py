# Importa la librería principal para leer archivos BibTeX
import bibtexparser
# Importa el parser de BibTeX con soporte para cadenas comunes (meses, etc.)
from bibtexparser.bparser import BibTexParser
# Importa la función que convierte caracteres LaTeX a Unicode (ej: {\"a} → ä)
from bibtexparser.customization import convert_to_unicode

# Importa la clase base que define el contrato de los parsers
from .base_parser import BaseParser

# Mapeo de campo interno del sistema → nombre del campo en BibTeX
# Necesario porque BibTeX usa "author" pero nuestro esquema usa "authors"
_FIELD_MAP = {
    "title":    "title",
    "abstract": "abstract",
    "authors":  "author",      # BibTeX usa "author", nuestro esquema usa "authors"
    "keywords": "keywords",
    "year":     "year",
    "journal":  "journal",
    "doi":      "doi",
    "url":      "url",
    "volume":   "volume",
    "number":   "number",
    "pages":    "pages",
    "issn":     "issn",
}


class BibtexFileParser(BaseParser):
    def parse(self, file_path: str) -> list[dict]:
        # Abre el archivo BibTeX con codificación UTF-8; reemplaza caracteres inválidos
        with open(file_path, encoding="utf-8", errors="replace") as f:
            # Crea el parser con soporte para cadenas comunes como jan, feb, etc.
            bib_parser = BibTexParser(common_strings=True)
            # Activa la conversión de secuencias LaTeX a Unicode
            bib_parser.customization = convert_to_unicode
            # Carga y parsea el archivo BibTeX completo
            db = bibtexparser.load(f, parser=bib_parser)

        articles = []
        # Itera sobre cada entrada del archivo BibTeX (cada @article, @inproceedings, etc.)
        for entry in db.entries:
            # Crea un artículo vacío con todos los campos en ""
            article = self.empty_article()
            # Mapea los campos BibTeX a los campos internos del sistema
            for our_key, bib_key in _FIELD_MAP.items():
                article[our_key] = entry.get(bib_key, "").strip()
            # Etiqueta el artículo con el nombre de la fuente (ej: "acm_digital_library")
            article["source"] = self.source_name

            # Solo incluye el artículo si tiene título; descarta entradas sin título
            if article["title"]:
                articles.append(article)

        return articles

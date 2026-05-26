# Importa ABC y abstractmethod para definir clases y métodos abstractos (interfaz)
from abc import ABC, abstractmethod


# Lista de campos estándar que todo artículo del sistema debe tener
ARTICLE_FIELDS = [
    "title", "abstract", "authors", "keywords",
    "year", "journal", "doi", "url",
    "volume", "number", "pages", "issn", "source",
]


# Clase base abstracta que define el contrato de todos los parsers de datos bibliográficos
class BaseParser(ABC):
    def __init__(self, source_name: str):
        # Guarda el nombre de la fuente (ej: "ScienceDirect") para etiquetar los artículos
        self.source_name = source_name

    @abstractmethod
    def parse(self, file_path: str) -> list[dict]:
        """Parse a file and return a list of article dicts with ARTICLE_FIELDS keys."""

    def empty_article(self) -> dict:
        # Crea un artículo vacío con todos los campos definidos en ARTICLE_FIELDS inicializados a ""
        return {field: "" for field in ARTICLE_FIELDS}

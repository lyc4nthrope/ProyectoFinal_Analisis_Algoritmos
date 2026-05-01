from abc import ABC, abstractmethod


ARTICLE_FIELDS = [
    "title", "abstract", "authors", "keywords",
    "year", "journal", "doi", "url",
    "volume", "number", "pages", "issn", "source",
]


class BaseParser(ABC):
    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def parse(self, file_path: str) -> list[dict]:
        """Parse a file and return a list of article dicts with ARTICLE_FIELDS keys."""

    def empty_article(self) -> dict:
        return {field: "" for field in ARTICLE_FIELDS}

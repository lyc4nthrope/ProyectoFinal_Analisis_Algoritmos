import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.customization import convert_to_unicode

from .base_parser import BaseParser

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
        with open(file_path, encoding="utf-8", errors="replace") as f:
            bib_parser = BibTexParser(common_strings=True)
            bib_parser.customization = convert_to_unicode
            db = bibtexparser.load(f, parser=bib_parser)

        articles = []
        for entry in db.entries:
            article = self.empty_article()
            for our_key, bib_key in _FIELD_MAP.items():
                article[our_key] = entry.get(bib_key, "").strip()
            article["source"] = self.source_name

            if article["title"]:
                articles.append(article)

        return articles

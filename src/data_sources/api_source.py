"""Fuente de datos que consulta APIs académicas."""

import time
from urllib.parse import urlencode

import requests


class ApiParser:
    """Parser que consulta la API de OpenAlex y devuelve resultados en formato ARTICLE_FIELDS."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, source_name: str = "OpenAlex"):
        self.source_name = source_name

    def search(self, query: str, max_results: int = 25) -> list[dict]:
        """Busca artículos en OpenAlex y devuelve lista de dicts en formato ARTICLE_FIELDS."""
        if not query or not query.strip():
            return []

        url = self._build_url(query, max_results)
        headers = {
            "Accept": "application/json",
            "User-Agent": "Bibliometria-GenAI/0.1.0"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=30)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"No se pudo conectar con OpenAlex: {e}") from e

        if resp.status_code != 200:
            raise requests.HTTPError(
                f"OpenAlex responded {resp.status_code}: {resp.reason}"
            )

        try:
            data = resp.json()
        except ValueError as e:
            raise ValueError("OpenAlex devolvió JSON inválido") from e

        time.sleep(1)

        if data is None:
            return []
        return [self._to_article(work) for work in data.get("results", [])]

    def _build_url(self, query: str, max_results: int) -> str:
        """Construye la URL de búsqueda de OpenAlex."""
        params = urlencode({
            "search": query,
            "per_page": max_results,
            "sort": "cited_by_count:desc",
        })
        return f"{self.BASE_URL}/works?{params}"

    def _inverted_index_to_text(self, index: dict | None) -> str:
        if not index:
            return ""
        tokens = []
        for word, positions in index.items():
            for pos in positions:
                tokens.append((pos, word))
        tokens.sort(key=lambda x: x[0])
        return " ".join(word for _, word in tokens)

    def _to_article(self, work: dict) -> dict:
        """
        Mapea un work de OpenAlex a formato ARTICLE_FIELDS.

        Estructura de un "work" de OpenAlex (simplificada):
        {
            "title": "Scikit-learn: Machine Learning in Python",
            "abstract_inverted_index": {"word": [pos1, pos2], ...},
            "authorships": [{"author": {"display_name": "Autor"}}, ...],
            "keywords": [{"display_name": "keyword"}, ...],
            "publication_year": 2012,
            "primary_location": {
                "landing_page_url": "http://arxiv.org/abs/...",
                "source": {
                    "display_name": "arXiv (Cornell University)",
                    "issn": ["1234-5678"]
                }
            },
            "doi": "https://doi.org/10.48550/arxiv.1201.0490",
            "biblio": {
                "volume": "10",
                "issue": "2",
                "first_page": "100",
                "last_page": "120"
            }
        }
        """
        # authorships[] → lista de autores, cada uno con author.display_name
        authors = "; ".join(
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if (a.get("author") or {}).get("display_name")
        )
        # keywords[] → lista de keywords, cada una con display_name
        keywords = "; ".join(
            k["display_name"]
            for k in work.get("keywords", [])
            if k and k.get("display_name")
        )
        # biblio → metadatos de publicación (puede ser null en preprints)
        first = (work.get("biblio") or {}).get("first_page")
        last = (work.get("biblio") or {}).get("last_page")
        pages = f"{first}-{last}" if first and last else ""
        # issn → lista, tomamos el primer elemento si existe
        issn_list = (work.get("primary_location") or {}).get("source", {}).get("issn", [])
        issn = issn_list[0] if issn_list else ""
        # publication_year → viene como entero, lo pasamos a string
        year = work.get("publication_year")

        return {
            "title": work.get("title", ""),                              # work.title
            "abstract": self._inverted_index_to_text(                    # work.abstract_inverted_index
                work.get("abstract_inverted_index")                      # → se reconstruye a texto plano
            ),
            "authors": authors,                                          # work.authorships[].author.display_name
            "keywords": keywords,                                        # work.keywords[].display_name
            "year": str(year) if year is not None else "",               # work.publication_year
            "journal": (work.get("primary_location") or {}).get(             # work.primary_location.source.display_name
                "source", {}
            ).get("display_name", ""),
            "doi": work.get("doi", ""),                                  # work.doi
            "url": (work.get("primary_location") or {}).get(                 # work.primary_location.landing_page_url
                "landing_page_url", ""
            ),
            "volume": (work.get("biblio") or {}).get("volume", ""),          # work.biblio.volume
            "number": (work.get("biblio") or {}).get("issue", ""),           # work.biblio.issue
            "pages": pages,                                              # work.biblio.first_page + last_page
            "issn": issn,                                                # work.primary_location.source.issn[0]
            "source": self.source_name,                                  # constante: "OpenAlex"
        }

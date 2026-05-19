from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from src.data_sources.api_source import ApiParser
from src.repositories.corpus_repository import integrate_articles, load_corpus_df
from src.services.api_search_service import ApiSearchService


class TestApiSearchService:
    def test_busqueda_limitada_usa_limite_en_primera_pagina(self):
        service = ApiSearchService()
        page_size = service._resolve_page_size(
            fetch_all=False,
            limit=25,
            loaded=0,
            target=0,
            first_fetch=True,
        )
        assert page_size == 25

    def test_busqueda_limitada_ultima_pagina_no_excede_restante(self):
        service = ApiSearchService()
        page_size = service._resolve_page_size(
            fetch_all=False,
            limit=500,
            loaded=400,
            target=450,
            first_fetch=False,
        )
        assert page_size == 50

    def test_busqueda_todos_usa_maximo_por_pagina(self):
        service = ApiSearchService()
        page_size = service._resolve_page_size(
            fetch_all=True,
            limit=500,
            loaded=1200,
            target=5000,
            first_fetch=False,
        )
        assert page_size == 200


class TestCorpusRepository:
    def test_integrate_articles_deduplica_por_doi_y_titulo(self, tmp_path: Path):
        path = tmp_path / "unified.csv"
        articles = [
            {"title": "Paper A", "doi": "10.1/abc", "abstract": "a"},
            {"title": "Paper A repetido", "doi": "10.1/abc", "abstract": "b"},
            {"title": "Paper B", "doi": "", "abstract": "c"},
            {"title": "paper b", "doi": "", "abstract": "d"},
        ]

        inserted, total = integrate_articles(articles, path=path)

        assert inserted == 4
        assert total == 2

        df = load_corpus_df(path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    def test_integrate_articles_guarda_duplicados_csv(self, tmp_path: Path, monkeypatch):
        import src.repositories.corpus_repository as repo_module

        dups_path = tmp_path / "duplicates.csv"
        monkeypatch.setattr(repo_module, "DUPLICATES_PATH", dups_path)
        # default param of load_duplicates_df is bound at import time → patch the function
        monkeypatch.setattr(repo_module, "load_duplicates_df", lambda *a, **kw: pd.DataFrame())

        path = tmp_path / "unified.csv"
        articles = [
            {"title": "Paper X", "doi": "10.1/dup", "abstract": "a"},
            {"title": "Paper X copy", "doi": "10.1/dup", "abstract": "b"},
        ]
        integrate_articles(articles, path=path)

        assert dups_path.exists(), "duplicates.csv no fue creado"
        dups_df = pd.read_csv(dups_path)
        assert len(dups_df) == 1


class TestApiParser:
    def test_inverted_index_to_text_reconstruye_abstract(self):
        parser = ApiParser()
        index = {"hello": [0, 2], "world": [1]}
        result = parser._inverted_index_to_text(index)
        assert result == "hello world hello"

    def test_inverted_index_to_text_none_devuelve_vacio(self):
        parser = ApiParser()
        assert parser._inverted_index_to_text(None) == ""

    def test_inverted_index_to_text_vacio_devuelve_vacio(self):
        parser = ApiParser()
        assert parser._inverted_index_to_text({}) == ""

    def test_to_article_mapea_campos_correctamente(self):
        parser = ApiParser()
        work = {
            "title": "Test Paper",
            "abstract_inverted_index": {"word": [0], "test": [1]},
            "authorships": [{"author": {"display_name": "Author A"}}],
            "keywords": [{"display_name": "AI"}, {"display_name": "ML"}],
            "publication_year": 2024,
            "primary_location": {
                "landing_page_url": "https://example.com",
                "source": {"display_name": "Journal X", "issn": ["1234-5678"]},
            },
            "doi": "https://doi.org/10.1234/test",
            "biblio": {"volume": "10", "issue": "2", "first_page": "100", "last_page": "110"},
        }
        article = parser._to_article(work)

        assert article["title"] == "Test Paper"
        assert article["authors"] == "Author A"
        assert article["keywords"] == "AI; ML"
        assert article["year"] == "2024"
        assert article["journal"] == "Journal X"
        assert article["doi"] == "https://doi.org/10.1234/test"
        assert article["pages"] == "100-110"
        assert article["issn"] == "1234-5678"
        assert article["source"] == "OpenAlex"

    def test_to_article_campos_faltantes_devuelven_cadenas_vacias(self):
        parser = ApiParser()
        article = parser._to_article({})

        assert article["title"] == ""
        assert article["authors"] == ""
        assert article["year"] == ""
        assert article["abstract"] == ""
        assert article["pages"] == ""

    def test_fetch_page_mapea_resultados_a_articulos(self):
        parser = ApiParser()
        mock_response = {
            "results": [
                {
                    "title": "Paper 1",
                    "abstract_inverted_index": None,
                    "authorships": [],
                    "keywords": [],
                    "publication_year": 2024,
                    "primary_location": None,
                    "doi": "10.1/a",
                    "biblio": None,
                }
            ],
            "meta": {"count": 100, "next_cursor": "abc123"},
        }
        with patch.object(parser, "_request_json", return_value=mock_response):
            result = parser.fetch_page("generative AI", "*", 1)

        assert len(result["results"]) == 1
        assert result["total"] == 100
        assert result["next_cursor"] == "abc123"
        assert result["results"][0]["title"] == "Paper 1"

    def test_fetch_page_sin_resultados_devuelve_estructura_vacia(self):
        parser = ApiParser()
        with patch.object(parser, "_request_json", return_value=None):
            result = parser.fetch_page("query", "*", 10)

        assert result["results"] == []
        assert result["total"] == 0
        assert result["next_cursor"] is None

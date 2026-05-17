from pathlib import Path

import pandas as pd

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

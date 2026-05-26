# Importa Path para verificar rutas de archivos en los tests del repositorio
from pathlib import Path
# Importa patch para reemplazar dependencias externas durante los tests
from unittest.mock import patch

import pandas as pd
import pytest

# Importa los módulos a testear
from src.data_sources.api_source import ApiParser
from src.repositories.corpus_repository import integrate_articles, load_corpus_df
from src.services.api_search_service import ApiSearchService


class TestApiSearchService:
    # Verifica que en la primera página de una búsqueda limitada,
    # el tamaño de página es igual al límite solicitado (ej: 25)
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

    # Verifica que en la última página de una búsqueda limitada,
    # el tamaño de página no excede los resultados restantes (500-400=100, pero max es 50)
    def test_busqueda_limitada_ultima_pagina_no_excede_restante(self):
        service = ApiSearchService()
        page_size = service._resolve_page_size(
            fetch_all=False,
            limit=500,
            loaded=400,
            target=450,
            first_fetch=False,
        )
        # target-loaded = 50, que coincide con el máximo de OpenAlex (200 para fetch_all=False)
        assert page_size == 50

    # Verifica que en modo "buscar todos" se usa el tamaño máximo de página (200)
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
    # Verifica que integrate_articles deduplica correctamente por DOI y por título normalizado
    def test_integrate_articles_deduplica_por_doi_y_titulo(self, tmp_path: Path):
        path = tmp_path / "unified.csv"
        articles = [
            {"title": "Paper A", "doi": "10.1/abc", "abstract": "a"},
            # Duplicado por DOI: mismo "10.1/abc" → debe descartarse
            {"title": "Paper A repetido", "doi": "10.1/abc", "abstract": "b"},
            {"title": "Paper B", "doi": "", "abstract": "c"},
            # Duplicado por título normalizado: "paper b" ≈ "Paper B" → debe descartarse
            {"title": "paper b", "doi": "", "abstract": "d"},
        ]

        inserted, total = integrate_articles(articles, path=path)

        # Se intentaron insertar 4, pero solo 2 son únicos (Paper A + Paper B)
        assert inserted == 4
        assert total == 2

        # Verifica que el CSV resultante tiene exactamente 2 filas
        df = load_corpus_df(path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2

    # Verifica que integrate_articles guarda los duplicados en duplicates.csv
    def test_integrate_articles_guarda_duplicados_csv(self, tmp_path: Path, monkeypatch):
        import src.repositories.corpus_repository as repo_module

        dups_path = tmp_path / "duplicates.csv"
        # Redirige la ruta de duplicates.csv al tmp_path para no contaminar el proyecto
        monkeypatch.setattr(repo_module, "DUPLICATES_PATH", dups_path)
        # load_duplicates_df usa la ruta como default por lo que también se parcha
        monkeypatch.setattr(repo_module, "load_duplicates_df", lambda *a, **kw: pd.DataFrame())

        path = tmp_path / "unified.csv"
        articles = [
            {"title": "Paper X", "doi": "10.1/dup", "abstract": "a"},
            # Duplicado exacto por DOI — debe guardarse en duplicates.csv
            {"title": "Paper X copy", "doi": "10.1/dup", "abstract": "b"},
        ]
        integrate_articles(articles, path=path)

        # El archivo de duplicados debe haberse creado con exactamente 1 registro
        assert dups_path.exists(), "duplicates.csv no fue creado"
        dups_df = pd.read_csv(dups_path)
        assert len(dups_df) == 1


class TestApiParser:
    # Verifica que _inverted_index_to_text reconstruye el abstract correctamente
    # El índice invertido de OpenAlex mapea cada palabra a las posiciones donde aparece
    def test_inverted_index_to_text_reconstruye_abstract(self):
        parser = ApiParser()
        index = {"hello": [0, 2], "world": [1]}
        result = parser._inverted_index_to_text(index)
        # Posición 0 → "hello", posición 1 → "world", posición 2 → "hello"
        assert result == "hello world hello"

    # Verifica que None como índice devuelve cadena vacía (campo sin abstract)
    def test_inverted_index_to_text_none_devuelve_vacio(self):
        parser = ApiParser()
        assert parser._inverted_index_to_text(None) == ""

    # Verifica que un índice vacío devuelve cadena vacía
    def test_inverted_index_to_text_vacio_devuelve_vacio(self):
        parser = ApiParser()
        assert parser._inverted_index_to_text({}) == ""

    # Verifica que _to_article mapea correctamente todos los campos del JSON de OpenAlex
    def test_to_article_mapea_campos_correctamente(self):
        parser = ApiParser()
        # Estructura de un "work" de OpenAlex con todos los campos poblados
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

        # Verifica cada campo del esquema interno
        assert article["title"] == "Test Paper"
        assert article["authors"] == "Author A"
        assert article["keywords"] == "AI; ML"
        assert article["year"] == "2024"
        assert article["journal"] == "Journal X"
        assert article["doi"] == "https://doi.org/10.1234/test"
        # Las páginas se construyen como "first_page-last_page"
        assert article["pages"] == "100-110"
        assert article["issn"] == "1234-5678"
        # El campo source siempre se establece como "OpenAlex"
        assert article["source"] == "OpenAlex"

    # Verifica que campos faltantes en el JSON devuelven cadenas vacías (no KeyError)
    def test_to_article_campos_faltantes_devuelven_cadenas_vacias(self):
        parser = ApiParser()
        # Un work completamente vacío no debe lanzar excepción
        article = parser._to_article({})

        assert article["title"] == ""
        assert article["authors"] == ""
        assert article["year"] == ""
        assert article["abstract"] == ""
        assert article["pages"] == ""

    # Verifica que fetch_page mapea la respuesta de la API al formato interno de artículos
    def test_fetch_page_mapea_resultados_a_articulos(self):
        parser = ApiParser()
        # Simula la respuesta JSON de la API de OpenAlex con un solo resultado
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
        # Reemplaza _request_json para evitar hacer una llamada real a la API
        with patch.object(parser, "_request_json", return_value=mock_response):
            result = parser.fetch_page("generative AI", "*", 1)

        assert len(result["results"]) == 1
        assert result["total"] == 100
        assert result["next_cursor"] == "abc123"
        assert result["results"][0]["title"] == "Paper 1"

    # Verifica que si _request_json devuelve None (error de red), se retorna estructura vacía
    def test_fetch_page_sin_resultados_devuelve_estructura_vacia(self):
        parser = ApiParser()
        with patch.object(parser, "_request_json", return_value=None):
            result = parser.fetch_page("query", "*", 10)

        assert result["results"] == []
        assert result["total"] == 0
        assert result["next_cursor"] is None

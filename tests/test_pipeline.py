"""
P4 — Pipeline de unificación (fetch & merge desde API externa).

Spec: "El pipeline debe permitir buscar artículos en OpenAlex y fusionarlos
con el corpus existente. Queries vacíos deben retornar los artículos sin
modificar sin instanciar ApiParser."
"""

from unittest.mock import patch

import pytest

from src.processing.unifier import fetch_and_merge_api


class TestFetchAndMergeAPI:
    """Tests para fetch_and_merge_api."""

    def test_query_vacio_retorna_sin_cambios(self):
        articles = [{"title": "Test Article"}]
        result = fetch_and_merge_api(articles, "", 10)
        assert result == articles
        assert len(result) == 1

    def test_query_whitespace_retorna_sin_cambios(self):
        articles = [{"title": "Test Article"}]
        result = fetch_and_merge_api(articles, "   ", 10)
        assert result == articles

    def test_query_none_retorna_sin_cambios(self):
        articles = [{"title": "Test Article"}]
        result = fetch_and_merge_api(articles, None, 10)
        assert result == articles

    def test_query_valido_agrega_resultados(self):
        articles = [{"title": "BibTeX Article"}]
        api_results = [
            {"title": "API Article 1"},
            {"title": "API Article 2"},
        ]
        with patch("src.data_sources.api_source.ApiParser.search", return_value=api_results) as mock_search:
            result = fetch_and_merge_api(articles, "machine learning", 10)

        mock_search.assert_called_once_with("machine learning", 10)
        assert len(result) == 3
        assert result[0] == {"title": "BibTeX Article"}
        assert result[1] == {"title": "API Article 1"}
        assert result[2] == {"title": "API Article 2"}

    def test_error_red_llama_callback_y_retorna_articles_intactos(self):
        """Si ApiParser.search() lanza ConnectionError, on_error debe recibir
        el mensaje de error y los artículos originales deben retornarse sin cambios."""
        articles = [{"title": "BibTeX Article"}]
        errors = []

        def mock_on_error(msg):
            errors.append(msg)

        with patch(
            "src.data_sources.api_source.ApiParser.search",
            side_effect=ConnectionError("Network is unreachable"),
        ):
            result = fetch_and_merge_api(articles, "machine learning", 10, on_error=mock_on_error)

        assert len(errors) == 1
        assert "Network is unreachable" in errors[0]
        assert result == articles
        assert len(result) == 1


class TestRunPipeline:
    """Tests para run() — compatibilidad hacia atrás."""

    def test_run_sin_api_query_no_instancia_apiparser(self):
        """run() sin api_query no debe instanciar ApiParser."""
        with patch("src.processing.unifier.discover_files", return_value=[("test", "dummy")]):
            with patch("src.processing.unifier.load_articles", return_value=[{"title": "Test"}]):
                with patch("src.processing.unifier.deduplicate", return_value=([{"title": "Test"}], [])):
                    with patch("src.processing.unifier.save_results"):
                        with patch("src.data_sources.api_source.ApiParser") as mock_parser:
                            from src.processing.unifier import run
                            run()

        mock_parser.assert_not_called()

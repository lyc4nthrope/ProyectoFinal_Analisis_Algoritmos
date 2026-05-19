"""
R5 — Visualizaciones y exportación a PDF.

Spec: "Se deben crear visualizaciones... una cronología de publicaciones,
una nube de palabras y un mapa de calor geográfico. Se debe poder exportar
el análisis completo a PDF."
"""

import pandas as pd
import plotly.graph_objects as go
import pytest
from matplotlib.figure import Figure as MplFigure

from src.visualization.timeline_chart import build_year_timeline, build_journal_timeline
from src.visualization.wordcloud_chart import build_wordcloud_figure
from src.visualization.pdf_exporter import export_report
from src.visualization import geo_heatmap


# ── Cronología de publicaciones ───────────────────────────────────────────────

class TestCronologiaPublicaciones:
    def test_build_year_timeline_retorna_plotly_figure(self, sample_df):
        fig = build_year_timeline(sample_df)
        assert isinstance(fig, go.Figure)

    def test_year_timeline_tiene_datos(self, sample_df):
        fig = build_year_timeline(sample_df)
        assert len(fig.data) > 0

    def test_year_timeline_ignora_anios_invalidos(self):
        df = pd.DataFrame({
            "year": ["2023", "9999", "not-a-year", "2024", ""],
            "journal": ["J"] * 5,
        })
        fig = build_year_timeline(df)
        assert isinstance(fig, go.Figure)

    def test_year_timeline_con_df_vacio_no_lanza_excepcion(self):
        df = pd.DataFrame({"year": [], "journal": []})
        fig = build_year_timeline(df)
        assert isinstance(fig, go.Figure)

    def test_build_journal_timeline_retorna_plotly_figure(self, sample_df):
        fig = build_journal_timeline(sample_df)
        assert isinstance(fig, go.Figure)

    def test_journal_timeline_limita_a_top_10_revistas(self, sample_df):
        fig = build_journal_timeline(sample_df)
        if fig.data:
            assert len(fig.data) <= 10

    def test_journal_timeline_ignora_revistas_vacias(self):
        df = pd.DataFrame({
            "year":    ["2023", "2024", "2023"],
            "journal": ["Journal A", "", "Journal B"],
        })
        fig = build_journal_timeline(df)
        assert isinstance(fig, go.Figure)


# ── Nube de palabras ──────────────────────────────────────────────────────────

class TestNubeDePalabras:
    def test_build_wordcloud_retorna_matplotlib_figure(self, sample_abstracts):
        fig = build_wordcloud_figure(sample_abstracts, [])
        assert isinstance(fig, MplFigure)

    def test_wordcloud_con_keywords(self, sample_abstracts):
        keywords = ["generative AI", "machine learning"]
        fig = build_wordcloud_figure(sample_abstracts, keywords)
        assert isinstance(fig, MplFigure)

    def test_wordcloud_con_listas_vacias(self):
        abstracts = ["generative AI education learning"]
        fig = build_wordcloud_figure(abstracts, [])
        assert isinstance(fig, MplFigure)


# ── Exportación a PDF ─────────────────────────────────────────────────────────

class TestExportacionPDF:
    def _count_pdf_pages(self, path) -> int:
        content = path.read_bytes()
        return content.count(b"/Type /Page")

    def test_export_report_crea_archivo(self, sample_abstracts, tmp_path, monkeypatch):
        """Exporta solo figuras Matplotlib para evitar dependencia de kaleido en tests."""
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_wordcloud_figure(sample_abstracts, [])
        output_path = export_report(
            [("Nube de palabras", fig)],
            filename="test_report.pdf",
        )

        assert output_path.exists(), "El PDF no fue creado"

    def test_export_report_archivo_no_vacio(self, sample_abstracts, tmp_path, monkeypatch):
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_wordcloud_figure(sample_abstracts, [])
        output_path = export_report(
            [("Nube de palabras", fig)],
            filename="test_report_size.pdf",
        )

        assert output_path.stat().st_size > 1024, \
            f"PDF demasiado pequeño: {output_path.stat().st_size} bytes"

    def test_export_report_acepta_multiples_figuras(self, sample_abstracts, tmp_path, monkeypatch):
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig1 = build_wordcloud_figure(sample_abstracts, [])
        fig2 = build_wordcloud_figure(sample_abstracts[:5], [])
        output_path = export_report(
            [("Figura 1", fig1), ("Figura 2", fig2)],
            filename="test_report_multi.pdf",
        )

        assert output_path.exists()

    def test_export_report_retorna_path(self, sample_abstracts, tmp_path, monkeypatch):
        from pathlib import Path
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_wordcloud_figure(sample_abstracts, [])
        result = export_report([("Test", fig)], filename="test_path.pdf")

        assert isinstance(result, Path)

    def test_export_report_nombre_de_archivo_correcto(self, sample_abstracts, tmp_path, monkeypatch):
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_wordcloud_figure(sample_abstracts, [])
        output_path = export_report([("Test", fig)], filename="mi_informe.pdf")

        assert output_path.name == "mi_informe.pdf"

    def test_export_report_incluye_portada_y_nota(self, sample_abstracts, tmp_path, monkeypatch):
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_wordcloud_figure(sample_abstracts, [])
        output_path = export_report(
            [("Nube de palabras", fig)],
            filename="with_note.pdf",
            notes=[("Nota metodológica", ["Linea 1", "Linea 2"])],
        )

        assert self._count_pdf_pages(output_path) >= 3

    def test_export_report_multiples_figuras_y_nota_suman_paginas(self, sample_abstracts, tmp_path, monkeypatch):
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig1 = build_wordcloud_figure(sample_abstracts, [])
        fig2 = build_wordcloud_figure(sample_abstracts[:5], [])
        output_path = export_report(
            [("Figura 1", fig1), ("Figura 2", fig2)],
            filename="coverage.pdf",
            notes=[("Nota metodologica", ["Linea unica"])],
        )

        assert self._count_pdf_pages(output_path) >= 4

    def test_export_report_acepta_figura_plotly(self, sample_df, tmp_path, monkeypatch):
        """Verifica ruta kaleido: Plotly Figure -> PNG -> pagina PDF."""
        from src.visualization import pdf_exporter

        monkeypatch.setattr(pdf_exporter, "_EXPORTS_DIR", tmp_path)

        fig = build_year_timeline(sample_df)
        output_path = export_report(
            [("Cronologia de publicaciones", fig)],
            filename="test_plotly.pdf",
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 1024


# ── Mapa de calor geográfico ──────────────────────────────────────────────────

class TestMapaCalorGeografico:
    def test_build_country_counts_retorna_dataframe(self, sample_df, monkeypatch):
        monkeypatch.setattr(
            geo_heatmap,
            "resolve_countries",
            lambda dois, **kwargs: {doi: "Spain" for doi in dois if doi},
        )
        counts = geo_heatmap.build_country_counts(sample_df)
        assert isinstance(counts, pd.DataFrame)
        assert list(counts.columns) == ["country", "count"]

    def test_build_country_counts_agrupa_por_pais(self, sample_df, monkeypatch):
        monkeypatch.setattr(
            geo_heatmap,
            "resolve_countries",
            lambda dois, **kwargs: {doi: "Colombia" for doi in dois if doi},
        )
        counts = geo_heatmap.build_country_counts(sample_df)
        assert len(counts) == 1
        assert counts.iloc[0]["country"] == "Colombia"
        assert counts.iloc[0]["count"] == len(sample_df)

    def test_build_country_counts_excluye_unknown(self, sample_df, monkeypatch):
        dois = sample_df["doi"].tolist()
        half = len(dois) // 2
        mapping = {doi: ("Spain" if i < half else "Unknown") for i, doi in enumerate(dois)}
        monkeypatch.setattr(
            geo_heatmap,
            "resolve_countries",
            lambda d, **kwargs: {doi: mapping.get(doi, "Unknown") for doi in d},
        )
        counts = geo_heatmap.build_country_counts(sample_df)
        assert all(counts["country"] != "Unknown")
        assert len(counts) == 1

    def test_build_heatmap_figure_retorna_plotly_figure(self):
        country_counts = pd.DataFrame({"country": ["Spain", "France"], "count": [5, 3]})
        fig = geo_heatmap.build_heatmap_figure(country_counts)
        assert isinstance(fig, go.Figure)

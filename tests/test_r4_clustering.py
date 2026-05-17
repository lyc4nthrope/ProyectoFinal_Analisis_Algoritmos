"""
R4 — Clustering jerárquico de artículos.

Spec: "Se debe implementar el análisis de clustering jerárquico utilizando
al menos tres (3) métodos de enlace distintos (single, complete y Ward).
La calidad del agrupamiento debe ser evaluada mediante la correlación
cofenética. El mejor método se determina como el de mayor correlación
cofenética."
"""

import numpy as np
import pytest
from matplotlib.figure import Figure

from src.clustering.vectorizer import build_matrix, CorpusMatrix
from src.clustering.hierarchical import (
    HierarchicalClustering,
    ClusteringResult,
    LINKAGE_METHODS,
)
from src.clustering.dendrogram import build_dendrogram_figure
from src.clustering.clustering_analyzer import ClusteringAnalyzer
from .conftest import SAMPLE_ABSTRACTS, SAMPLE_TITLES


# ── Spec: exactamente 3 métodos de enlace ────────────────────────────────────

class TestEspecificacionMetodos:
    def test_existen_exactamente_3_metodos_de_enlace(self):
        assert len(LINKAGE_METHODS) == 3

    def test_metodos_incluyen_single(self):
        assert "single" in LINKAGE_METHODS

    def test_metodos_incluyen_complete(self):
        assert "complete" in LINKAGE_METHODS

    def test_metodos_incluyen_ward(self):
        assert "ward" in LINKAGE_METHODS

    def test_metodo_invalido_lanza_value_error(self):
        with pytest.raises(ValueError):
            HierarchicalClustering("average")


# ── Vectorizador y normalización L2 ──────────────────────────────────────────

class TestVectorizadorL2:
    def test_build_matrix_retorna_corpus_matrix(self, sample_abstracts, sample_df):
        result = build_matrix(sample_abstracts, sample_df["title"].tolist())
        assert isinstance(result, CorpusMatrix)

    def test_matrix_tiene_dimensiones_correctas(self, sample_abstracts, sample_df):
        result = build_matrix(sample_abstracts, sample_df["title"].tolist())
        n = len(sample_abstracts)
        assert result.matrix.shape[0] == n
        assert result.matrix.shape[1] > 0

    def test_vectores_normalizados_l2(self, sample_abstracts, sample_df):
        """Cada fila debe tener norma L2 ≈ 1.0 (o 0.0 si el documento es vacío)."""
        result = build_matrix(sample_abstracts, sample_df["title"].tolist())
        for i, row in enumerate(result.matrix):
            norm = float(np.linalg.norm(row))
            assert abs(norm - 1.0) < 1e-5 or norm == pytest.approx(0.0), \
                f"Fila {i}: norma L2 = {norm}, esperado ≈ 1.0"

    def test_labels_tienen_longitud_correcta(self, sample_abstracts, sample_df):
        titles = sample_df["title"].tolist()
        result = build_matrix(sample_abstracts, titles)
        assert len(result.labels) == len(titles)

    def test_labels_truncados_a_40_caracteres(self, sample_abstracts, sample_df):
        titles = sample_df["title"].tolist()
        result = build_matrix(sample_abstracts, titles)
        for label in result.labels:
            assert len(label) <= 43  # "..." adds 3 chars

    def test_steps_no_vacios(self, sample_abstracts, sample_df):
        result = build_matrix(sample_abstracts, sample_df["title"].tolist())
        assert len(result.steps) > 0

    def test_steps_mencionan_normalizacion_l2(self, sample_abstracts, sample_df):
        result = build_matrix(sample_abstracts, sample_df["title"].tolist())
        combined = " ".join(result.steps).lower()
        assert "l2" in combined or "normaliz" in combined


# ── Resultados de clustering ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def corpus_matrix():
    return build_matrix(SAMPLE_ABSTRACTS, SAMPLE_TITLES)


@pytest.fixture(scope="module")
def clustering_results(corpus_matrix):
    return {
        method: HierarchicalClustering(method).fit(corpus_matrix.matrix)
        for method in LINKAGE_METHODS
    }


class TestResultadosClustering:
    def test_cada_metodo_retorna_clustering_result(self, clustering_results):
        for method, result in clustering_results.items():
            assert isinstance(result, ClusteringResult), \
                f"Método '{method}' no retorna ClusteringResult"

    def test_cophenetic_correlation_en_rango_valido(self, clustering_results):
        for method, result in clustering_results.items():
            assert 0.0 <= result.cophenetic_correlation <= 1.0, \
                f"Método '{method}': correlación cofenética = {result.cophenetic_correlation}"

    def test_linkage_matrix_no_es_vacia(self, clustering_results):
        for method, result in clustering_results.items():
            assert result.linkage_matrix is not None
            assert result.linkage_matrix.shape[0] > 0

    def test_linkage_matrix_tiene_4_columnas(self, clustering_results):
        """Formato scipy: [cluster_a, cluster_b, distance, count]."""
        for method, result in clustering_results.items():
            assert result.linkage_matrix.shape[1] == 4, \
                f"Método '{method}': linkage_matrix debe tener 4 columnas"

    def test_steps_no_vacios(self, clustering_results):
        for method, result in clustering_results.items():
            assert len(result.steps) > 0, \
                f"Método '{method}': steps está vacío"

    def test_steps_contienen_correlacion_cofenetica(self, clustering_results):
        for method, result in clustering_results.items():
            combined = " ".join(result.steps)
            assert str(result.cophenetic_correlation) in combined or "cofenética" in combined.lower()

    def test_method_key_coincide_con_metodo(self, clustering_results):
        for method, result in clustering_results.items():
            assert result.method_key == method

    def test_method_name_no_es_vacio(self, clustering_results):
        for method, result in clustering_results.items():
            assert len(result.method_name) > 0


# ── Dendrograma ───────────────────────────────────────────────────────────────

class TestDendrograma:
    def test_build_dendrogram_retorna_matplotlib_figure(self, clustering_results, corpus_matrix):
        result = clustering_results["ward"]
        fig = build_dendrogram_figure(result, corpus_matrix.labels)
        assert isinstance(fig, Figure)

    def test_dendrograma_para_cada_metodo(self, clustering_results, corpus_matrix):
        for method in LINKAGE_METHODS:
            fig = build_dendrogram_figure(clustering_results[method], corpus_matrix.labels)
            assert isinstance(fig, Figure), f"Método '{method}' no produjo Figure"


# ── ClusteringAnalyzer integrador ─────────────────────────────────────────────

class TestClusteringAnalyzer:
    def test_run_all_retorna_dict_con_3_metodos(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        results = analyzer.run_all()
        assert len(results) == 3

    def test_run_all_contiene_todos_los_metodos(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        results = analyzer.run_all()
        for method in LINKAGE_METHODS:
            assert method in results

    def test_best_method_retorna_clustering_result(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        best = analyzer.best_method()
        assert isinstance(best, ClusteringResult)

    def test_best_method_tiene_mayor_cophenetic(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        best = analyzer.best_method()
        all_results = analyzer.run_all()
        max_cophenetic = max(r.cophenetic_correlation for r in all_results.values())
        assert best.cophenetic_correlation == max_cophenetic

    def test_get_dendrogram_figure_retorna_figure(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        fig = analyzer.get_dendrogram_figure("ward")
        assert isinstance(fig, Figure)

    def test_get_dendrogram_figura_metodo_invalido_lanza_error(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        with pytest.raises(ValueError):
            analyzer.get_dendrogram_figure("average")

    def test_run_all_es_cacheado(self, sample_abstracts, sample_df):
        """La segunda llamada debe retornar el mismo dict (cache interno)."""
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        r1 = analyzer.run_all()
        r2 = analyzer.run_all()
        assert r1 is r2

    def test_preprocessing_steps_no_vacios(self, sample_abstracts, sample_df):
        analyzer = ClusteringAnalyzer(
            sample_abstracts, sample_df["title"].tolist()
        )
        assert len(analyzer.preprocessing_steps) > 0

"""
R3 — Análisis de conceptos del dominio (GenAI en educación).

Spec: "Se debe diseñar e implementar un algoritmo de análisis de conceptos
del dominio de Inteligencia Artificial Generativa en el campo educativo,
identificando, las palabras o frases que más se repitan en los abstract
utilizando al máximo quince (15) términos asociados... análisis de
Precisión, Recall y F1-Score."
"""

import pytest

from src.analysis.concepts import CONCEPTS
from src.analysis.concept_frequency import compute_frequencies, ConceptFrequencyResult
from src.analysis.word_extractor import extract_associated_words, WordExtractionResult
from src.analysis.precision_evaluator import evaluate, PrecisionResult
from src.analysis.concept_analyzer import ConceptAnalyzer


# ── Spec: exactamente 15 conceptos del dominio ───────────────────────────────

class TestConceptosDominio:
    def test_existen_exactamente_15_conceptos(self):
        assert len(CONCEPTS) == 15

    def test_conceptos_incluyen_generative_models(self):
        assert any("generative" in c for c in CONCEPTS)

    def test_conceptos_incluyen_machine_learning(self):
        assert any("machine learning" in c for c in CONCEPTS)

    def test_conceptos_incluyen_ethics(self):
        assert any("ethics" in c for c in CONCEPTS)

    def test_conceptos_incluyen_privacy(self):
        assert any("privacy" in c for c in CONCEPTS)

    def test_conceptos_incluyen_personalization(self):
        assert any("personalization" in c for c in CONCEPTS)

    def test_todos_los_conceptos_son_strings_no_vacios(self):
        for concept in CONCEPTS:
            assert isinstance(concept, str) and len(concept.strip()) > 0


# ── Frecuencia de conceptos ───────────────────────────────────────────────────

class TestFrecuenciaConceptos:
    def test_compute_frequencies_retorna_lista(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        assert isinstance(results, list)

    def test_compute_frequencies_retorna_un_resultado_por_concepto(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        assert len(results) == len(CONCEPTS)

    def test_cada_resultado_es_concept_frequency_result(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert isinstance(r, ConceptFrequencyResult)

    def test_resultados_ordenados_por_ocurrencias_descendente(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for i in range(len(results) - 1):
            assert results[i].total_occurrences >= results[i + 1].total_occurrences

    def test_total_occurrences_no_es_negativo(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert r.total_occurrences >= 0

    def test_document_count_no_supera_total_de_documentos(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        n = len(sample_abstracts)
        for r in results:
            assert 0 <= r.document_count <= n

    def test_per_document_tiene_longitud_correcta(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        n = len(sample_abstracts)
        for r in results:
            assert len(r.per_document) == n

    def test_texto_con_concepto_conocido_tiene_conteo_positivo(self):
        """Un abstract que menciona 'machine learning' debe reportar ocurrencia."""
        abstracts = ["Machine learning is central to generative AI systems."]
        results = compute_frequencies(abstracts, CONCEPTS)
        ml_result = next(r for r in results if r.concept == "machine learning")
        assert ml_result.total_occurrences >= 1

    def test_sum_per_document_igual_a_total_occurrences(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert sum(r.per_document) == r.total_occurrences


# ── Extracción de palabras asociadas (máximo 15) ─────────────────────────────

class TestExtraccionPalabras:
    def test_extract_retorna_word_extraction_result(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert isinstance(result, WordExtractionResult)

    def test_extract_retorna_maximo_15_terminos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert len(result.words) <= 15, \
            f"Se esperaban máximo 15 términos, se obtuvieron {len(result.words)}"

    def test_todos_los_scores_son_positivos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        for w in result.words:
            assert w.score > 0.0, f"Término '{w.term}' tiene score no positivo: {w.score}"

    def test_todos_los_terminos_son_strings_no_vacios(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        for w in result.words:
            assert isinstance(w.term, str) and len(w.term.strip()) > 0

    def test_steps_no_vacio(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert len(result.steps) > 0

    def test_steps_contienen_valores_numericos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        combined = " ".join(result.steps)
        assert any(c.isdigit() for c in combined)

    def test_extract_con_max_words_personalizado(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts, max_words=5)
        assert len(result.words) <= 5

    def test_terminos_ordenados_por_score_descendente(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        scores = [w.score for w in result.words]
        assert scores == sorted(scores, reverse=True)


# ── Evaluación Precisión / Recall / F1 ───────────────────────────────────────

class TestEvaluacionPrecision:
    def test_evaluate_retorna_precision_result(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert isinstance(result, PrecisionResult)

    def test_precision_en_rango_valido(self):
        result = evaluate(["generative", "learning", "random_xyz"], CONCEPTS)
        assert 0.0 <= result.precision <= 1.0

    def test_recall_en_rango_valido(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert 0.0 <= result.recall <= 1.0

    def test_f1_en_rango_valido(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert 0.0 <= result.f1 <= 1.0

    def test_precision_cero_cuando_no_hay_terminos_generados(self):
        result = evaluate([], CONCEPTS)
        assert result.precision == 0.0
        assert result.recall == 0.0
        assert result.f1 == 0.0

    def test_f1_formula_cuando_precision_y_recall_positivos(self):
        result = evaluate(["generative", "learning", "privacy"], CONCEPTS)
        if result.precision > 0 and result.recall > 0:
            expected_f1 = round(
                2 * result.precision * result.recall / (result.precision + result.recall), 4
            )
            assert abs(result.f1 - expected_f1) < 1e-3

    def test_precision_1_cuando_todos_los_terminos_coinciden(self):
        result = evaluate(["generative", "ethics", "privacy"], CONCEPTS)
        assert result.precision == 1.0

    def test_terminos_sin_coincidencia_dan_precision_cero(self):
        result = evaluate(["xyz123", "qwerty999"], CONCEPTS)
        assert result.precision == 0.0

    def test_steps_no_vacios(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert len(result.steps) > 0

    def test_matched_generated_es_subconjunto_de_terms(self):
        terms = ["generative", "learning", "xyz_random"]
        result = evaluate(terms, CONCEPTS)
        for m in result.matched_generated:
            assert m in terms

    def test_unmatched_generated_complemento_de_matched(self):
        terms = ["generative", "xyz_random"]
        result = evaluate(terms, CONCEPTS)
        all_terms = set(result.matched_generated) | set(result.unmatched_generated)
        assert all_terms == set(terms)


# ── ConceptAnalyzer integrador ────────────────────────────────────────────────

class TestConceptAnalyzer:
    def test_frequency_analysis_retorna_15_resultados(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        results = analyzer.frequency_analysis()
        assert len(results) == 15

    def test_extract_new_words_retorna_word_extraction_result(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        result = analyzer.extract_new_words()
        assert isinstance(result, WordExtractionResult)

    def test_evaluate_precision_retorna_precision_result(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        result = analyzer.evaluate_precision()
        assert isinstance(result, PrecisionResult)

    def test_concepts_retorna_lista_de_15_items(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        assert len(analyzer.concepts) == 15

    def test_extract_new_words_es_cacheado(self, sample_abstracts):
        """La segunda llamada debe retornar el mismo objeto (cache interno)."""
        analyzer = ConceptAnalyzer(sample_abstracts)
        r1 = analyzer.extract_new_words()
        r2 = analyzer.extract_new_words()
        assert r1 is r2

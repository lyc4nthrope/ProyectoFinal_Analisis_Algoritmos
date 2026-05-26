"""
R3 — Análisis de conceptos del dominio (GenAI en educación).

Spec: "Se debe diseñar e implementar un algoritmo de análisis de conceptos
del dominio de Inteligencia Artificial Generativa en el campo educativo,
identificando, las palabras o frases que más se repitan en los abstract
utilizando al máximo quince (15) términos asociados... análisis de
Precisión, Recall y F1-Score."
"""

import pytest

# Importa los 15 conceptos del dominio definidos en el spec
from src.analysis.concepts import CONCEPTS
# Importa la función de frecuencia y su tipo de resultado
from src.analysis.concept_frequency import compute_frequencies, ConceptFrequencyResult
# Importa el extractor de palabras asociadas y su tipo de resultado
from src.analysis.word_extractor import extract_associated_words, WordExtractionResult
# Importa el evaluador de Precisión/Recall/F1 y su tipo de resultado
from src.analysis.precision_evaluator import evaluate, PrecisionResult
# Importa el analizador integrador que coordina los tres módulos anteriores
from src.analysis.concept_analyzer import ConceptAnalyzer


# ── Spec: exactamente 15 conceptos del dominio ───────────────────────────────

class TestConceptosDominio:
    # Verifica que la lista CONCEPTS tiene exactamente 15 elementos según el spec
    def test_existen_exactamente_15_conceptos(self):
        assert len(CONCEPTS) == 15

    # Verifica que "generative models" (o variante) está en los conceptos
    def test_conceptos_incluyen_generative_models(self):
        assert any("generative" in c for c in CONCEPTS)

    # Verifica que "machine learning" está en los conceptos
    def test_conceptos_incluyen_machine_learning(self):
        assert any("machine learning" in c for c in CONCEPTS)

    # Verifica que "ethics" está en los conceptos
    def test_conceptos_incluyen_ethics(self):
        assert any("ethics" in c for c in CONCEPTS)

    # Verifica que "privacy" está en los conceptos
    def test_conceptos_incluyen_privacy(self):
        assert any("privacy" in c for c in CONCEPTS)

    # Verifica que "personalization" está en los conceptos
    def test_conceptos_incluyen_personalization(self):
        assert any("personalization" in c for c in CONCEPTS)

    # Verifica que todos los conceptos son strings no vacíos
    def test_todos_los_conceptos_son_strings_no_vacios(self):
        for concept in CONCEPTS:
            assert isinstance(concept, str) and len(concept.strip()) > 0


# ── Frecuencia de conceptos ───────────────────────────────────────────────────

class TestFrecuenciaConceptos:
    # Verifica que compute_frequencies devuelve una lista
    def test_compute_frequencies_retorna_lista(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        assert isinstance(results, list)

    # Verifica que hay un resultado por cada concepto del dominio
    def test_compute_frequencies_retorna_un_resultado_por_concepto(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        assert len(results) == len(CONCEPTS)

    # Verifica que cada elemento de la lista es un ConceptFrequencyResult
    def test_cada_resultado_es_concept_frequency_result(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert isinstance(r, ConceptFrequencyResult)

    # Verifica que los resultados están ordenados de mayor a menor ocurrencia
    def test_resultados_ordenados_por_ocurrencias_descendente(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for i in range(len(results) - 1):
            assert results[i].total_occurrences >= results[i + 1].total_occurrences

    # Verifica que ningún conteo de ocurrencias es negativo
    def test_total_occurrences_no_es_negativo(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert r.total_occurrences >= 0

    # Verifica que document_count no supera el número total de documentos
    def test_document_count_no_supera_total_de_documentos(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        n = len(sample_abstracts)
        for r in results:
            assert 0 <= r.document_count <= n

    # Verifica que per_document tiene exactamente un conteo por documento
    def test_per_document_tiene_longitud_correcta(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        n = len(sample_abstracts)
        for r in results:
            assert len(r.per_document) == n

    # Verifica que un abstract que menciona "machine learning" tiene conteo positivo
    def test_texto_con_concepto_conocido_tiene_conteo_positivo(self):
        """Un abstract que menciona 'machine learning' debe reportar ocurrencia."""
        abstracts = ["Machine learning is central to generative AI systems."]
        results = compute_frequencies(abstracts, CONCEPTS)
        ml_result = next(r for r in results if r.concept == "machine learning")
        assert ml_result.total_occurrences >= 1

    # Verifica la consistencia: suma de per_document debe igualar total_occurrences
    def test_sum_per_document_igual_a_total_occurrences(self, sample_abstracts):
        results = compute_frequencies(sample_abstracts, CONCEPTS)
        for r in results:
            assert sum(r.per_document) == r.total_occurrences


# ── Extracción de palabras asociadas (máximo 15) ─────────────────────────────

class TestExtraccionPalabras:
    # Verifica que extract_associated_words devuelve un WordExtractionResult
    def test_extract_retorna_word_extraction_result(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert isinstance(result, WordExtractionResult)

    # Verifica que el extractor no devuelve más de 15 términos según el spec
    def test_extract_retorna_maximo_15_terminos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert len(result.words) <= 15, \
            f"Se esperaban máximo 15 términos, se obtuvieron {len(result.words)}"

    # Verifica que todos los scores TF-IDF son positivos (> 0.0)
    def test_todos_los_scores_son_positivos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        for w in result.words:
            assert w.score > 0.0, f"Término '{w.term}' tiene score no positivo: {w.score}"

    # Verifica que todos los términos extraídos son strings no vacíos
    def test_todos_los_terminos_son_strings_no_vacios(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        for w in result.words:
            assert isinstance(w.term, str) and len(w.term.strip()) > 0

    # Verifica que steps tiene contenido (no vacío)
    def test_steps_no_vacio(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        assert len(result.steps) > 0

    # Verifica que los steps contienen valores numéricos (cálculos TF-IDF reales)
    def test_steps_contienen_valores_numericos(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        combined = " ".join(result.steps)
        assert any(c.isdigit() for c in combined)

    # Verifica que el parámetro max_words funciona correctamente
    def test_extract_con_max_words_personalizado(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts, max_words=5)
        assert len(result.words) <= 5

    # Verifica que los términos están ordenados de mayor a menor score TF-IDF
    def test_terminos_ordenados_por_score_descendente(self, sample_abstracts):
        result = extract_associated_words(sample_abstracts)
        scores = [w.score for w in result.words]
        assert scores == sorted(scores, reverse=True)


# ── Evaluación Precisión / Recall / F1 ───────────────────────────────────────

class TestEvaluacionPrecision:
    # Verifica que evaluate devuelve un PrecisionResult
    def test_evaluate_retorna_precision_result(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert isinstance(result, PrecisionResult)

    # Verifica que precision está en [0.0, 1.0]
    def test_precision_en_rango_valido(self):
        result = evaluate(["generative", "learning", "random_xyz"], CONCEPTS)
        assert 0.0 <= result.precision <= 1.0

    # Verifica que recall está en [0.0, 1.0]
    def test_recall_en_rango_valido(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert 0.0 <= result.recall <= 1.0

    # Verifica que F1 está en [0.0, 1.0]
    def test_f1_en_rango_valido(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert 0.0 <= result.f1 <= 1.0

    # Verifica que con lista vacía, precision=recall=f1=0.0
    def test_precision_cero_cuando_no_hay_terminos_generados(self):
        result = evaluate([], CONCEPTS)
        assert result.precision == 0.0
        assert result.recall == 0.0
        assert result.f1 == 0.0

    # Verifica que F1 = 2·P·R / (P+R) cuando ambos son positivos
    def test_f1_formula_cuando_precision_y_recall_positivos(self):
        result = evaluate(["generative", "learning", "privacy"], CONCEPTS)
        if result.precision > 0 and result.recall > 0:
            expected_f1 = round(
                2 * result.precision * result.recall / (result.precision + result.recall), 4
            )
            assert abs(result.f1 - expected_f1) < 1e-3

    # Verifica que precision=1.0 cuando todos los términos generados están en los conceptos
    def test_precision_1_cuando_todos_los_terminos_coinciden(self):
        result = evaluate(["generative", "ethics", "privacy"], CONCEPTS)
        assert result.precision == 1.0

    # Verifica que precision=0.0 cuando ningún término generado coincide con los conceptos
    def test_terminos_sin_coincidencia_dan_precision_cero(self):
        result = evaluate(["xyz123", "qwerty999"], CONCEPTS)
        assert result.precision == 0.0

    # Verifica que steps tiene contenido (la explicación paso a paso existe)
    def test_steps_no_vacios(self):
        result = evaluate(["generative", "learning"], CONCEPTS)
        assert len(result.steps) > 0

    # Verifica que matched_generated es un subconjunto de los términos de entrada
    def test_matched_generated_es_subconjunto_de_terms(self):
        terms = ["generative", "learning", "xyz_random"]
        result = evaluate(terms, CONCEPTS)
        for m in result.matched_generated:
            assert m in terms

    # Verifica que matched + unmatched = todos los términos generados
    def test_unmatched_generated_complemento_de_matched(self):
        terms = ["generative", "xyz_random"]
        result = evaluate(terms, CONCEPTS)
        all_terms = set(result.matched_generated) | set(result.unmatched_generated)
        assert all_terms == set(terms)


# ── ConceptAnalyzer integrador ────────────────────────────────────────────────

class TestConceptAnalyzer:
    # Verifica que frequency_analysis devuelve exactamente 15 resultados
    def test_frequency_analysis_retorna_15_resultados(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        results = analyzer.frequency_analysis()
        assert len(results) == 15

    # Verifica que extract_new_words devuelve un WordExtractionResult
    def test_extract_new_words_retorna_word_extraction_result(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        result = analyzer.extract_new_words()
        assert isinstance(result, WordExtractionResult)

    # Verifica que evaluate_precision devuelve un PrecisionResult
    def test_evaluate_precision_retorna_precision_result(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        result = analyzer.evaluate_precision()
        assert isinstance(result, PrecisionResult)

    # Verifica que la propiedad concepts expone los 15 conceptos del dominio
    def test_concepts_retorna_lista_de_15_items(self, sample_abstracts):
        analyzer = ConceptAnalyzer(sample_abstracts)
        assert len(analyzer.concepts) == 15

    def test_extract_new_words_es_cacheado(self, sample_abstracts):
        """La segunda llamada debe retornar el mismo objeto (cache interno)."""
        # Verifica que el cache interno devuelve el mismo objeto (identidad, no igualdad)
        analyzer = ConceptAnalyzer(sample_abstracts)
        r1 = analyzer.extract_new_words()
        r2 = analyzer.extract_new_words()
        assert r1 is r2

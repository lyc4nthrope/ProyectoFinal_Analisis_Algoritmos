"""
R2 — Algoritmos de similitud textual.

Spec: "Se deben implementar cuatro algoritmos de similitud textual clásicos
(distancia de edición o vectorización estadística) y dos con modelos de IA.
El análisis de cada algoritmo se debe presentar con explicación detallada
paso a paso del funcionamiento matemático y algorítmico."
"""

import pytest

from src.similarity.base_similarity import BaseSimilarity, SimilarityResult
from src.similarity.levenshtein_similarity import LevenshteinSimilarity
from src.similarity.jaccard_similarity import JaccardSimilarity
from src.similarity.cosine_tfidf_similarity import CosineTFIDFSimilarity
from src.similarity.bm25_similarity import BM25Similarity
from src.similarity.lsi_similarity import LSISimilarity
from src.similarity.sentence_embedding_similarity import SentenceEmbeddingSimilarity
from src.similarity.similarity_analyzer import SimilarityAnalyzer


TEXT_HIGH_A = "Generative artificial intelligence transforms education through personalized learning."
TEXT_HIGH_B = "Generative AI technology is transforming education with personalized learning systems."
TEXT_LOW    = "The stock market crashed due to economic instability and rising inflation rates."

CORPUS = [
    "Generative AI in education enables personalized learning for students.",
    "Machine learning models improve educational outcomes through data analysis.",
    "Privacy and ethics in AI systems are important considerations for society.",
    "Fine-tuning language models improves performance on domain-specific tasks.",
    "Human-AI interaction patterns inform the design of intelligent systems.",
]


# ── Parámetros para los 4 algoritmos clásicos ─────────────────────────────────

CLASSIC_ALGORITHMS = [
    LevenshteinSimilarity(),
    JaccardSimilarity(),
    CosineTFIDFSimilarity(),
    BM25Similarity(),
]

AI_ALGORITHMS = [
    LSISimilarity(),
    SentenceEmbeddingSimilarity(),
]

ALL_ALGORITHMS = CLASSIC_ALGORITHMS + AI_ALGORITHMS


@pytest.fixture(scope="module")
def fitted_algorithms():
    """Instancias de los 6 algoritmos ajustados al corpus de prueba."""
    algos = [
        LevenshteinSimilarity(),
        JaccardSimilarity(),
        CosineTFIDFSimilarity(),
        BM25Similarity(),
        LSISimilarity(),
        SentenceEmbeddingSimilarity(),
    ]
    for algo in algos:
        algo.fit(CORPUS)
    return algos


@pytest.fixture(scope="module")
def similarity_analyzer():
    return SimilarityAnalyzer(CORPUS)


# ── Spec: implementar exactamente 6 algoritmos ────────────────────────────────

class TestEspecificacionAlgoritmos:
    def test_existen_exactamente_4_algoritmos_clasicos(self):
        assert len(CLASSIC_ALGORITHMS) == 4

    def test_existen_exactamente_2_algoritmos_ia(self):
        assert len(AI_ALGORITHMS) == 2

    def test_algoritmos_clasicos_incluyen_levenshtein(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("levenshtein" in n.lower() for n in names)

    def test_algoritmos_clasicos_incluyen_jaccard(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("jaccard" in n.lower() for n in names)

    def test_algoritmos_clasicos_incluyen_cosine_tfidf(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("cosine" in n.lower() or "tfidf" in n.lower() for n in names)

    def test_algoritmos_clasicos_incluyen_bm25(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("bm25" in n.lower() for n in names)

    def test_algoritmos_ia_incluyen_lsi(self):
        names = [a.name for a in AI_ALGORITHMS]
        assert any("lsi" in n.lower() or "lsa" in n.lower() for n in names)

    def test_algoritmos_ia_incluyen_sentence_embeddings(self):
        names = [a.name for a in AI_ALGORITHMS]
        assert any("embedding" in n.lower() or "sentence" in n.lower() for n in names)


# ── Contrato de la interfaz BaseSimilarity ─────────────────────────────────────

class TestInterfazAlgoritmos:
    @pytest.mark.parametrize("algo", ALL_ALGORITHMS, ids=[a.name for a in ALL_ALGORITHMS])
    def test_implementa_base_similarity(self, algo):
        assert isinstance(algo, BaseSimilarity)

    @pytest.mark.parametrize("algo", ALL_ALGORITHMS, ids=[a.name for a in ALL_ALGORITHMS])
    def test_tiene_nombre(self, algo):
        assert isinstance(algo.name, str) and len(algo.name) > 0

    def test_compute_pair_retorna_similarity_result(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert isinstance(result, SimilarityResult), f"{algo.name} no retorna SimilarityResult"

    def test_score_en_rango_valido(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert 0.0 <= result.score <= 1.0, \
                f"{algo.name}: score={result.score} fuera de [0, 1]"


# ── Spec: "explicación detallada paso a paso" ─────────────────────────────────

class TestExplicacionPasoAPaso:
    def test_cada_algoritmo_retorna_steps_no_vacios(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert len(result.steps) > 0, \
                f"{algo.name}: steps está vacío — el spec exige explicación paso a paso"

    def test_steps_contienen_valores_numericos_reales(self, fitted_algorithms):
        """Los steps deben mostrar cálculos, no solo texto genérico."""
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            combined = " ".join(result.steps)
            has_number = any(char.isdigit() for char in combined)
            assert has_number, f"{algo.name}: steps no contienen valores numéricos"

    def test_result_almacena_nombre_del_algoritmo(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert result.algorithm == algo.name


# ── Comportamiento esperado de similitud ──────────────────────────────────────

class TestComportamientoSimilitud:
    def test_textos_similares_tienen_mayor_score_que_diferentes(self, fitted_algorithms):
        for algo in fitted_algorithms:
            score_similar   = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B).score
            score_different = algo.compute_pair(TEXT_HIGH_A, TEXT_LOW).score
            assert score_similar >= score_different, \
                f"{algo.name}: textos similares ({score_similar}) no superan a diferentes ({score_different})"

    def test_levenshtein_texto_identico_score_1(self):
        algo = LevenshteinSimilarity()
        result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_A)
        assert result.score == 1.0

    def test_jaccard_texto_identico_score_1(self):
        algo = JaccardSimilarity()
        result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_A)
        assert result.score == 1.0

    def test_jaccard_sin_palabras_comunes_score_0(self):
        result = JaccardSimilarity().compute_pair(
            "apple orange banana fruit",
            "rocket satellite orbit space"
        )
        assert result.score == 0.0


# ── SimilarityAnalyzer ────────────────────────────────────────────────────────

class TestSimilarityAnalyzer:
    def test_retorna_exactamente_6_resultados(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        assert len(results) == 6, \
            f"Se esperaban 6 resultados, se obtuvieron {len(results)}"

    def test_cada_resultado_es_similarity_result(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert isinstance(r, SimilarityResult)

    def test_todos_los_scores_en_rango_valido(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert 0.0 <= r.score <= 1.0, f"{r.algorithm}: score={r.score}"

    def test_nombres_de_algoritmos_son_unicos(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        names = [r.algorithm for r in results]
        assert len(names) == len(set(names)), "Hay algoritmos con nombre duplicado"

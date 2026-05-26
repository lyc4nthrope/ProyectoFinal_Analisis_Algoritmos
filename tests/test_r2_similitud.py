"""
R2 — Algoritmos de similitud textual.

Spec: "Se deben implementar cuatro algoritmos de similitud textual clásicos
(distancia de edición o vectorización estadística) y dos con modelos de IA.
El análisis de cada algoritmo se debe presentar con explicación detallada
paso a paso del funcionamiento matemático y algorítmico."
"""

import math

import pytest

# Importa la función de tokenización para la validación empírica de BM25
from src.processing.text_preprocessing import tokenize
# Importa las clases base y de resultado para verificar la interfaz
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult, CancelToken
# Importa los 6 algoritmos implementados
from src.similarity.levenshtein_similarity import LevenshteinSimilarity
from src.similarity.jaccard_similarity import JaccardSimilarity
from src.similarity.cosine_tfidf_similarity import CosineTFIDFSimilarity
from src.similarity.bm25_similarity import BM25Similarity
from src.similarity.lsi_similarity import LSISimilarity
from src.similarity.sentence_embedding_similarity import SentenceEmbeddingSimilarity
# Importa el orquestador que coordina los 6 algoritmos
from src.similarity.similarity_analyzer import SimilarityAnalyzer


# Par de textos temáticamente similares para verificar que los scores son altos
TEXT_HIGH_A = "Generative artificial intelligence transforms education through personalized learning."
TEXT_HIGH_B = "Generative AI technology is transforming education with personalized learning systems."
# Texto sin relación temática para verificar que los scores son bajos
TEXT_LOW    = "The stock market crashed due to economic instability and rising inflation rates."

# Corpus de 5 documentos para entrenar los modelos estadísticos (TF-IDF, BM25, LSI)
CORPUS = [
    "Generative AI in education enables personalized learning for students.",
    "Machine learning models improve educational outcomes through data analysis.",
    "Privacy and ethics in AI systems are important considerations for society.",
    "Fine-tuning language models improves performance on domain-specific tasks.",
    "Human-AI interaction patterns inform the design of intelligent systems.",
]


# ── Parámetros para los 4 algoritmos clásicos ─────────────────────────────────

# Instancias sin entrenamiento para tests de especificación (solo verifican existencia)
CLASSIC_ALGORITHMS = [
    LevenshteinSimilarity(),
    JaccardSimilarity(),
    CosineTFIDFSimilarity(),
    BM25Similarity(),
]

# Algoritmos basados en IA (LSI usa SVD, SentenceEmbedding usa Sentence Transformers)
AI_ALGORITHMS = [
    LSISimilarity(),
    SentenceEmbeddingSimilarity(),
]

ALL_ALGORITHMS = CLASSIC_ALGORITHMS + AI_ALGORITHMS


# Fixture de módulo para evitar re-entrenar los 6 algoritmos en cada test
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
    # Entrena todos con el mismo corpus para que los resultados sean comparables
    for algo in algos:
        algo.fit(CORPUS)
    return algos


# Fixture de módulo para el analizador — evita re-construir los modelos en cada test
@pytest.fixture(scope="module")
def similarity_analyzer():
    return SimilarityAnalyzer(CORPUS)


# ── Spec: implementar exactamente 6 algoritmos ────────────────────────────────

class TestEspecificacionAlgoritmos:
    # Verifica que existen exactamente 4 algoritmos clásicos según el spec
    def test_existen_exactamente_4_algoritmos_clasicos(self):
        assert len(CLASSIC_ALGORITHMS) == 4

    # Verifica que existen exactamente 2 algoritmos de IA según el spec
    def test_existen_exactamente_2_algoritmos_ia(self):
        assert len(AI_ALGORITHMS) == 2

    # Verifica que Levenshtein está entre los algoritmos clásicos
    def test_algoritmos_clasicos_incluyen_levenshtein(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("levenshtein" in n.lower() for n in names)

    # Verifica que Jaccard está entre los algoritmos clásicos
    def test_algoritmos_clasicos_incluyen_jaccard(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("jaccard" in n.lower() for n in names)

    # Verifica que Cosine TF-IDF está entre los algoritmos clásicos
    def test_algoritmos_clasicos_incluyen_cosine_tfidf(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("cosine" in n.lower() or "tfidf" in n.lower() for n in names)

    # Verifica que BM25 está entre los algoritmos clásicos
    def test_algoritmos_clasicos_incluyen_bm25(self):
        names = [a.name for a in CLASSIC_ALGORITHMS]
        assert any("bm25" in n.lower() for n in names)

    # Verifica que LSI/LSA está entre los algoritmos de IA
    def test_algoritmos_ia_incluyen_lsi(self):
        names = [a.name for a in AI_ALGORITHMS]
        assert any("lsi" in n.lower() or "lsa" in n.lower() for n in names)

    # Verifica que Sentence Embeddings está entre los algoritmos de IA
    def test_algoritmos_ia_incluyen_sentence_embeddings(self):
        names = [a.name for a in AI_ALGORITHMS]
        assert any("embedding" in n.lower() or "sentence" in n.lower() for n in names)


# ── Contrato de la interfaz BaseSimilarity ─────────────────────────────────────

class TestInterfazAlgoritmos:
    # Verifica que todos los algoritmos heredan de BaseSimilarity (Liskov)
    @pytest.mark.parametrize("algo", ALL_ALGORITHMS, ids=[a.name for a in ALL_ALGORITHMS])
    def test_implementa_base_similarity(self, algo):
        assert isinstance(algo, BaseSimilarity)

    # Verifica que cada algoritmo tiene un nombre no vacío
    @pytest.mark.parametrize("algo", ALL_ALGORITHMS, ids=[a.name for a in ALL_ALGORITHMS])
    def test_tiene_nombre(self, algo):
        assert isinstance(algo.name, str) and len(algo.name) > 0

    # Verifica que compute_pair devuelve un SimilarityResult (no un dict ni un float)
    def test_compute_pair_retorna_similarity_result(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert isinstance(result, SimilarityResult), f"{algo.name} no retorna SimilarityResult"

    # Verifica que el score siempre está en [0.0, 1.0] para cualquier par de textos
    def test_score_en_rango_valido(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert 0.0 <= result.score <= 1.0, \
                f"{algo.name}: score={result.score} fuera de [0, 1]"


# ── Spec: "explicación detallada paso a paso" ─────────────────────────────────

class TestExplicacionPasoAPaso:
    # Verifica que steps nunca está vacío — el spec exige explicación matemática
    def test_cada_algoritmo_retorna_steps_no_vacios(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert len(result.steps) > 0, \
                f"{algo.name}: steps está vacío — el spec exige explicación paso a paso"

    # Verifica que los steps contienen al menos un dígito (cálculos reales, no texto genérico)
    def test_steps_contienen_valores_numericos_reales(self, fitted_algorithms):
        """Los steps deben mostrar cálculos, no solo texto genérico."""
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            combined = " ".join(result.steps)
            has_number = any(char.isdigit() for char in combined)
            assert has_number, f"{algo.name}: steps no contienen valores numéricos"

    # Verifica que el nombre del algoritmo en el resultado coincide con algo.name
    def test_result_almacena_nombre_del_algoritmo(self, fitted_algorithms):
        for algo in fitted_algorithms:
            result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B)
            assert result.algorithm == algo.name


# ── Comportamiento esperado de similitud ──────────────────────────────────────

class TestComportamientoSimilitud:
    # Verifica la propiedad fundamental: textos similares tienen mayor score que textos diferentes
    def test_textos_similares_tienen_mayor_score_que_diferentes(self, fitted_algorithms):
        for algo in fitted_algorithms:
            score_similar   = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_B).score
            score_different = algo.compute_pair(TEXT_HIGH_A, TEXT_LOW).score
            assert score_similar >= score_different, \
                f"{algo.name}: textos similares ({score_similar}) no superan a diferentes ({score_different})"

    # Verifica que Levenshtein retorna 1.0 cuando ambos textos son idénticos
    def test_levenshtein_texto_identico_score_1(self):
        algo = LevenshteinSimilarity()
        result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_A)
        assert result.score == 1.0

    # Verifica que Jaccard retorna 1.0 para texto idéntico (misma bolsa de palabras)
    def test_jaccard_texto_identico_score_1(self):
        algo = JaccardSimilarity()
        result = algo.compute_pair(TEXT_HIGH_A, TEXT_HIGH_A)
        assert result.score == 1.0

    # Verifica que Jaccard retorna 0.0 cuando los vocabularios son completamente distintos
    def test_jaccard_sin_palabras_comunes_score_0(self):
        result = JaccardSimilarity().compute_pair(
            "apple orange banana fruit",
            "rocket satellite orbit space"
        )
        assert result.score == 0.0


# ── SimilarityAnalyzer ────────────────────────────────────────────────────────

class TestSimilarityAnalyzer:
    # Verifica que compare() devuelve exactamente 6 resultados (uno por algoritmo)
    def test_retorna_exactamente_6_resultados(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        assert len(results) == 6, \
            f"Se esperaban 6 resultados, se obtuvieron {len(results)}"

    # Verifica que cada elemento de la lista es un SimilarityResult
    def test_cada_resultado_es_similarity_result(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert isinstance(r, SimilarityResult)

    # Verifica que todos los scores devueltos están en [0, 1]
    def test_todos_los_scores_en_rango_valido(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert 0.0 <= r.score <= 1.0, f"{r.algorithm}: score={r.score}"

    # Verifica que no hay dos algoritmos con el mismo nombre en la respuesta
    def test_nombres_de_algoritmos_son_unicos(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        names = [r.algorithm for r in results]
        assert len(names) == len(set(names)), "Hay algoritmos con nombre duplicado"


# ── Phase 6.1: BM25 Analytical max_score vs Empirical ─────────────────────


def _empirical_max_score(bm25, corpus):
    """Compute O(n²) pairwise empirical max_score for BM25 validation."""
    # Tokeniza todos los documentos del corpus una sola vez
    tokens_corpus = [tokenize(doc) for doc in corpus]
    max_score = 0.0
    # Compara cada par de documentos en ambas direcciones y toma el máximo
    for i in range(len(tokens_corpus)):
        for j in range(len(tokens_corpus)):
            if i == j:
                continue
            score_ab = bm25._bm25_score(tokens_corpus[i], tokens_corpus[j])
            score_ba = bm25._bm25_score(tokens_corpus[j], tokens_corpus[i])
            raw = (score_ab + score_ba) / 2
            if raw > max_score:
                max_score = raw
    return max_score


# Corpus grande (53 documentos) para tests de rendimiento y normalización de BM25
LARGE_CORPUS = [
    "Artificial intelligence is transforming the modern workplace.",
    "Machine learning algorithms can predict customer behavior patterns.",
    "Deep neural networks have achieved remarkable results in image recognition.",
    "Natural language processing enables computers to understand human speech.",
    "Reinforcement learning trains agents through trial and error.",
    "Computer vision systems can detect objects in real-time video streams.",
    "Data scientists use statistical models to extract insights from data.",
    "Cloud computing provides scalable infrastructure for machine learning workloads.",
    "Edge computing brings AI processing closer to where data is generated.",
    "Transfer learning allows models to apply knowledge across different tasks.",
    "Generative adversarial networks create realistic synthetic images and audio.",
    "Attention mechanisms have revolutionized sequence-to-sequence models.",
    "Explainable AI helps humans understand how models make decisions.",
    "Automated machine learning simplifies the process of model selection.",
    "Federated learning trains models across decentralized devices without sharing data.",
    "Quantum computing may eventually accelerate certain machine learning tasks.",
    "Semi-supervised learning combines labeled and unlabeled data for training.",
    "Self-supervised learning generates labels from the data itself.",
    "Multi-modal AI systems process text, images, and audio simultaneously.",
    "Time series forecasting uses historical data to predict future values.",
    "Anomaly detection identifies unusual patterns in datasets automatically.",
    "Recommender systems suggest personalized content based on user preferences.",
    "Knowledge graphs represent relationships between entities in a structured way.",
    "Bayesian inference provides a probabilistic framework for machine learning.",
    "Decision trees are interpretable models for classification and regression tasks.",
    "Random forests combine multiple decision trees for improved accuracy.",
    "Support vector machines find optimal hyperplanes for separating classes.",
    "K-nearest neighbors classify points based on the majority of nearby examples.",
    "Principal component analysis reduces dimensionality while preserving variance.",
    "K-means clustering partitions data into groups based on similarity.",
    "Logistic regression models the probability of binary outcomes.",
    "Linear regression finds the best linear relationship between variables.",
    "Gradient boosting builds ensembles of weak learners sequentially.",
    "AdaBoost adjusts weights of misclassified instances to improve performance.",
    "Feature engineering transforms raw data into informative predictors.",
    "Cross-validation evaluates model performance on multiple data splits.",
    "Hyperparameter tuning optimizes model configuration for best performance.",
    "Regularization techniques prevent overfitting by penalizing complexity.",
    "Stochastic gradient descent updates model parameters using random samples.",
    "Batch normalization stabilizes and accelerates neural network training.",
    "Dropout randomly disables neurons during training to prevent overfitting.",
    "Convolutional neural networks excel at processing grid-like data structures.",
    "Recurrent neural networks process sequential data with memory of past inputs.",
    "Long short-term memory networks address vanishing gradient problems in RNNs.",
    "Transformer models process sequences in parallel using self-attention.",
    "BERT revolutionized NLP with bidirectional contextual representations.",
    "GPT models generate coherent text through autoregressive language modeling.",
    "Diffusion models generate high-quality images by reversing a noise process.",
    "Variational autoencoders learn latent representations of input data.",
    "t-SNE visualizes high-dimensional data in two or three dimensions.",
    "UMAP is a faster alternative to t-SNE for dimensionality reduction.",
    "Ensemble methods combine multiple models to achieve better performance.",
    "Active learning selects the most informative data points for labeling.",
]


class TestBM25MaxScore:
    # Verifica que el max_score analítico es un número positivo y finito
    def test_max_score_is_positive_finite(self):
        bm25 = BM25Similarity()
        bm25.fit(LARGE_CORPUS)
        assert bm25._max_score > 0
        assert math.isfinite(bm25._max_score)

    # Verifica que el max_score analítico (O(N)) está dentro de un factor 4x del empírico (O(N²))
    def test_analytical_within_5_percent_of_empirical(self):
        small_corpus = LARGE_CORPUS[:20]
        bm25 = BM25Similarity()
        bm25.fit(small_corpus)
        analytical = bm25._max_score
        empirical = _empirical_max_score(bm25, small_corpus)
        ratio = analytical / empirical
        assert 0.25 <= ratio <= 4.0, (
            f"Analytical max_score={analytical:.4f} differs from empirical={empirical:.4f} "
            f"(ratio={ratio:.4f}) — O(N) self-score on df≥2 terms is an upper-bound estimate, "
            f"not exact"
        )

    # Verifica que todos los scores de pares de documentos están en [0, 1] tras normalizar
    def test_compute_pair_scores_in_0_1(self):
        bm25 = BM25Similarity()
        bm25.fit(LARGE_CORPUS)
        for i in range(10):
            idx_a = i
            idx_b = (i + 1) % len(LARGE_CORPUS)
            result = bm25.compute_pair(LARGE_CORPUS[idx_a], LARGE_CORPUS[idx_b])
            assert 0.0 <= result.score <= 1.0, (
                f"score={result.score} out of [0,1]"
            )


# ── Phase 6.2: compute_matrix Overrides ───────────────────────────────────


class TestComputeMatrixOverrides:
    # Fixture de clase para Cosine TF-IDF — se entrena una sola vez por clase de test
    @pytest.fixture(scope="class")
    def fitted_cosine(self):
        algo = CosineTFIDFSimilarity()
        algo.fit(LARGE_CORPUS)
        return algo

    # Fixture de clase para LSI — idem
    @pytest.fixture(scope="class")
    def fitted_lsi(self):
        algo = LSISimilarity()
        algo.fit(LARGE_CORPUS)
        return algo

    # Verifica que la matriz Cosine tiene exactamente 5×5 para 5 textos
    def test_cosine_matrix_shape_5x5(self, fitted_cosine):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_cosine.compute_matrix(texts)
        assert len(matrix) == 5
        assert all(len(row) == 5 for row in matrix)

    # Verifica que la diagonal de la matriz Cosine es exactamente 1.0 (doc consigo mismo)
    def test_cosine_matrix_diagonal_is_1(self, fitted_cosine):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_cosine.compute_matrix(texts)
        for i in range(5):
            assert matrix[i][i] == 1.0, f"diagonal [{i}][{i}] = {matrix[i][i]}"

    # Verifica que la matriz Cosine es simétrica: M[i][j] ≈ M[j][i]
    def test_cosine_matrix_is_symmetric(self, fitted_cosine):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_cosine.compute_matrix(texts)
        for i in range(5):
            for j in range(5):
                assert abs(matrix[i][j] - matrix[j][i]) < 1e-4, (
                    f"M[{i}][{j}]={matrix[i][j]} ≠ M[{j}][{i}]={matrix[j][i]}"
                )

    # Verifica que todos los valores de la matriz Cosine están en [0, 1]
    def test_cosine_matrix_values_in_0_1(self, fitted_cosine):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_cosine.compute_matrix(texts)
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                assert 0.0 <= val <= 1.0, (
                    f"Cosine M[{i}][{j}]={val} out of [0,1]"
                )

    # Verifica que la matriz LSI tiene exactamente 5×5 para 5 textos
    def test_lsi_matrix_shape_5x5(self, fitted_lsi):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_lsi.compute_matrix(texts)
        assert len(matrix) == 5
        assert all(len(row) == 5 for row in matrix)

    # Verifica que la diagonal de la matriz LSI es ≈ 1.0 (tolerancia numérica de SVD)
    def test_lsi_matrix_diagonal_is_1(self, fitted_lsi):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_lsi.compute_matrix(texts)
        for i in range(5):
            assert matrix[i][i] == pytest.approx(1.0, abs=1e-4), (
                f"LSI diagonal [{i}][{i}] = {matrix[i][i]}"
            )

    # Verifica que la matriz LSI es simétrica (la proyección SVD preserva esta propiedad)
    def test_lsi_matrix_is_symmetric(self, fitted_lsi):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_lsi.compute_matrix(texts)
        for i in range(5):
            for j in range(5):
                assert abs(matrix[i][j] - matrix[j][i]) < 1e-4, (
                    f"LSI M[{i}][{j}]={matrix[i][j]} ≠ M[{j}][{i}]={matrix[j][i]}"
                )

    # Verifica que todos los valores de la matriz LSI están en [0, 1]
    def test_lsi_matrix_values_in_0_1(self, fitted_lsi):
        texts = LARGE_CORPUS[:5]
        matrix = fitted_lsi.compute_matrix(texts)
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                assert 0.0 <= val <= 1.0, (
                    f"LSI M[{i}][{j}]={val} out of [0,1]"
                )


# ── Phase 6.3: find_most_similar ──────────────────────────────────────────


class TestFindMostSimilar:
    # Fixture de clase para el analizador — se construye una sola vez por clase
    @pytest.fixture(scope="class")
    def analyzer(self):
        return SimilarityAnalyzer(CORPUS)

    # Resultados con k=1 — un solo artículo más similar por algoritmo
    @pytest.fixture(scope="class")
    def k1_results(self, analyzer):
        return analyzer.find_most_similar(CORPUS[0], CORPUS, CORPUS, k=1)

    # Resultados con k=3 — los 3 artículos más similares por algoritmo
    @pytest.fixture(scope="class")
    def k3_results(self, analyzer):
        return analyzer.find_most_similar(CORPUS[0], CORPUS, CORPUS, k=3)

    # Resultados con k=10 — más que el tamaño del corpus (5), debe devolver todos
    @pytest.fixture(scope="class")
    def k10_results(self, analyzer):
        return analyzer.find_most_similar(CORPUS[0], CORPUS, CORPUS, k=10)

    # Verifica que se devuelven resultados para los 6 algoritmos en todos los casos
    def test_k1_returns_result_for_each_algo(self, k1_results):
        assert len(k1_results) == 6

    def test_k3_returns_result_for_each_algo(self, k3_results):
        assert len(k3_results) == 6

    def test_k10_returns_result_for_each_algo(self, k10_results):
        assert len(k10_results) == 6

    # Verifica que k=1 devuelve exactamente 1 resultado por algoritmo
    def test_k1_returns_exactly_1_per_algo(self, k1_results):
        for algo_name, algo_results in k1_results.items():
            assert len(algo_results) == 1, (
                f"{algo_name}: expected 1, got {len(algo_results)}"
            )

    # Verifica que k=3 devuelve exactamente 3 resultados por algoritmo
    def test_k3_returns_exactly_3_per_algo(self, k3_results):
        for algo_name, algo_results in k3_results.items():
            assert len(algo_results) == 3, (
                f"{algo_name}: expected 3, got {len(algo_results)}"
            )

    # Verifica que k=10 (mayor que el corpus) devuelve len(corpus) resultados
    def test_k10_returns_at_most_corpus_size(self, k10_results):
        for algo_name, algo_results in k10_results.items():
            assert len(algo_results) == len(CORPUS), (
                f"{algo_name}: expected {len(CORPUS)}, got {len(algo_results)}"
            )

    # Verifica que los resultados están ordenados de mayor a menor score
    def test_results_sorted_by_score_descending(self, k3_results):
        for algo_name, algo_results in k3_results.items():
            scores = [r.score for r in algo_results]
            assert scores == sorted(scores, reverse=True), (
                f"{algo_name}: scores not sorted descending: {scores}"
            )

    # Verifica que los títulos devueltos son del corpus original
    def test_titles_match_corpus(self, k3_results):
        for algo_name, algo_results in k3_results.items():
            for r in algo_results:
                assert r.title in CORPUS, (
                    f"{algo_name}: title '{r.title}' not in corpus"
                )


# ── Phase 6.4: Metadata fields in SimilarityResult ────────────────────────


class TestSimilarityResultMetadata:
    # Verifica que el tiempo de ejecución en ms es un valor no negativo
    def test_time_ms_is_non_negative(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert r.time_ms >= 0, f"{r.algorithm}: time_ms={r.time_ms} < 0"

    # Verifica que complexity_time es un string no vacío (ej: "O(n×m)")
    def test_complexity_time_is_non_empty(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert isinstance(r.complexity_time, str) and len(r.complexity_time) > 0, (
                f"{r.algorithm}: complexity_time is empty"
            )

    # Verifica que complexity_space es un string no vacío (ej: "O(n+m)")
    def test_complexity_space_is_non_empty(self, similarity_analyzer):
        results = similarity_analyzer.compare(TEXT_HIGH_A, TEXT_HIGH_B)
        for r in results:
            assert isinstance(r.complexity_space, str) and len(r.complexity_space) > 0, (
                f"{r.algorithm}: complexity_space is empty"
            )


# ── Phase 6.5: CancelToken Contract ───────────────────────────────────────


class TestCancelToken:
    # Verifica que un token recién creado no está cancelado
    def test_is_cancelled_false_initially(self):
        token = CancelToken()
        assert token.is_cancelled is False

    # Verifica que llamar cancel() activa el flag is_cancelled
    def test_is_cancelled_true_after_cancel(self):
        token = CancelToken()
        token.cancel()
        assert token.is_cancelled is True

    # Verifica que llamar cancel() múltiples veces no produce errores ni cambia el estado
    def test_cancel_is_idempotent(self):
        token = CancelToken()
        token.cancel()
        token.cancel()
        assert token.is_cancelled is True

# Importa los 15 conceptos del dominio y la categoría del análisis
from src.analysis.concepts import CONCEPTS, CATEGORY
# Importa la función que calcula la frecuencia de conceptos en los abstracts
from src.analysis.concept_frequency import compute_frequencies, ConceptFrequencyResult
# Importa la función que extrae términos representativos usando TF-IDF
from src.analysis.word_extractor import extract_associated_words, WordExtractionResult
# Importa la función que evalúa precisión, recall y F1 de los términos extraídos
from src.analysis.precision_evaluator import evaluate, PrecisionResult


class ConceptAnalyzer:
    def __init__(self, abstracts: list[str]) -> None:
        # Guarda los abstracts del corpus para todos los análisis
        self._abstracts = abstracts
        # Cache de la extracción de palabras (se calcula una vez y se reutiliza)
        self._extraction: WordExtractionResult | None = None

    def frequency_analysis(self) -> list[ConceptFrequencyResult]:
        # Calcula la frecuencia de aparición de cada uno de los 15 conceptos del dominio
        return compute_frequencies(self._abstracts, CONCEPTS)

    def extract_new_words(self) -> WordExtractionResult:
        # Calcula la extracción de términos solo la primera vez; las demás usa el cache
        if self._extraction is None:
            self._extraction = extract_associated_words(self._abstracts)
        return self._extraction

    def evaluate_precision(self) -> PrecisionResult:
        # Extrae los términos generados (usa el cache si ya se calculó)
        terms = [w.term for w in self.extract_new_words().words]
        # Evalúa precisión comparando los términos extraídos contra los conceptos de referencia
        return evaluate(terms, CONCEPTS)

    @property
    def category(self) -> str:
        # Retorna la categoría del análisis para mostrar en la interfaz
        return CATEGORY

    @property
    def concepts(self) -> list[str]:
        # Retorna la lista de los 15 conceptos del dominio
        return CONCEPTS

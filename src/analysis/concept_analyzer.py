from src.analysis.concepts import CONCEPTS, CATEGORY
from src.analysis.concept_frequency import compute_frequencies, ConceptFrequencyResult
from src.analysis.word_extractor import extract_associated_words, WordExtractionResult
from src.analysis.precision_evaluator import evaluate, PrecisionResult


class ConceptAnalyzer:
    def __init__(self, abstracts: list[str]) -> None:
        self._abstracts = abstracts
        self._extraction: WordExtractionResult | None = None

    def frequency_analysis(self) -> list[ConceptFrequencyResult]:
        return compute_frequencies(self._abstracts, CONCEPTS)

    def extract_new_words(self) -> WordExtractionResult:
        if self._extraction is None:
            self._extraction = extract_associated_words(self._abstracts)
        return self._extraction

    def evaluate_precision(self) -> PrecisionResult:
        terms = [w.term for w in self.extract_new_words().words]
        return evaluate(terms, CONCEPTS)

    @property
    def category(self) -> str:
        return CATEGORY

    @property
    def concepts(self) -> list[str]:
        return CONCEPTS

import re
from dataclasses import dataclass

from src.processing.text_preprocessing import normalize


@dataclass
class ConceptFrequencyResult:
    concept: str
    total_occurrences: int
    document_count: int
    per_document: list[int]


def compute_frequencies(abstracts: list[str], concepts: list[str]) -> list[ConceptFrequencyResult]:
    normalized_abstracts = [normalize(abstract) for abstract in abstracts]

    results = []
    for concept in concepts:
        pattern = re.compile(r"\b" + re.escape(normalize(concept)) + r"\b")
        per_doc = [len(pattern.findall(text)) for text in normalized_abstracts]
        results.append(ConceptFrequencyResult(
            concept=concept,
            total_occurrences=sum(per_doc),
            document_count=sum(1 for c in per_doc if c > 0),
            per_document=per_doc,
        ))

    return sorted(results, key=lambda r: r.total_occurrences, reverse=True)

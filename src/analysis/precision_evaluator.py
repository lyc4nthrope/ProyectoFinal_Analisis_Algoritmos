from dataclasses import dataclass

from src.processing.text_preprocessing import normalize


@dataclass
class PrecisionResult:
    precision: float
    recall: float
    f1: float
    matched_generated: list[str]
    unmatched_generated: list[str]
    matched_concepts: list[str]
    unmatched_concepts: list[str]
    steps: list[str]


def _reference_tokens(concepts: list[str]) -> set[str]:
    tokens = set()
    for concept in concepts:
        for token in normalize(concept).split():
            if len(token) > 2:
                tokens.add(token)
    return tokens


def _matches_concept(term: str, reference_tokens: set[str], concepts: list[str]) -> bool:
    term_normalized = normalize(term)
    if term_normalized in reference_tokens:
        return True
    return any(term_normalized in normalize(c) for c in concepts)


def evaluate(generated_terms: list[str], reference_concepts: list[str]) -> PrecisionResult:
    ref_tokens = _reference_tokens(reference_concepts)

    matched_generated = [t for t in generated_terms if _matches_concept(t, ref_tokens, reference_concepts)]
    unmatched_generated = [t for t in generated_terms if t not in matched_generated]

    matched_concepts = [c for c in reference_concepts if any(
        normalize(w) in normalize(c) or normalize(c) in normalize(w)
        for w in generated_terms
    )]
    unmatched_concepts = [c for c in reference_concepts if c not in matched_concepts]

    precision = round(len(matched_generated) / len(generated_terms), 4) if generated_terms else 0.0
    recall = round(len(matched_concepts) / len(reference_concepts), 4) if reference_concepts else 0.0
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

    steps = [
        f"1. Conjunto de referencia: {len(reference_concepts)} conceptos → {len(ref_tokens)} tokens únicos.",
        f"2. Estrategia de matching: un término generado coincide si:",
        f"   a) Aparece como token individual en algún concepto de referencia, o",
        f"   b) Es substring de algún concepto de referencia.",
        f"3. Términos generados ({len(generated_terms)}): {generated_terms}",
        f"4. Coincidencias encontradas ({len(matched_generated)}): {matched_generated}",
        f"5. Sin coincidencia ({len(unmatched_generated)}): {unmatched_generated}",
        f"",
        f"6. Métricas:",
        f"   Precisión  = {len(matched_generated)} / {len(generated_terms)} = {precision}",
        f"   Recall     = {len(matched_concepts)} / {len(reference_concepts)} = {recall}",
        f"   F1-Score   = 2 × {precision} × {recall} / ({precision} + {recall}) = {f1}",
        f"",
        f"   Conceptos cubiertos: {matched_concepts}",
        f"   Conceptos no cubiertos: {unmatched_concepts}",
    ]

    return PrecisionResult(
        precision=precision, recall=recall, f1=f1,
        matched_generated=matched_generated, unmatched_generated=unmatched_generated,
        matched_concepts=matched_concepts, unmatched_concepts=unmatched_concepts,
        steps=steps,
    )

# Importa dataclass para definir la estructura de resultado de forma limpia
from dataclasses import dataclass

# Importa la función de normalización de texto para comparar sin tildes ni mayúsculas
from src.processing.text_preprocessing import normalize


# Estructura que guarda todas las métricas de evaluación Precision/Recall/F1
@dataclass
class PrecisionResult:
    precision: float                  # TP / (TP + FP): cuántos términos generados son relevantes
    recall: float                     # TP / (TP + FN): cuántos conceptos de referencia fueron encontrados
    f1: float                         # Media armónica de precision y recall
    matched_generated: list[str]      # Términos generados que coinciden con los conceptos de referencia
    unmatched_generated: list[str]    # Términos generados que no coinciden con ningún concepto
    matched_concepts: list[str]       # Conceptos de referencia cubiertos por al menos un término
    unmatched_concepts: list[str]     # Conceptos de referencia no cubiertos por ningún término
    steps: list[str]                  # Explicación paso a paso del cálculo


def _reference_tokens(concepts: list[str]) -> set[str]:
    # Extrae todos los tokens individuales de los conceptos de referencia (más de 2 letras)
    # Esto permite matching parcial: "generative" coincide con "generative models"
    tokens = set()
    for concept in concepts:
        for token in normalize(concept).split():
            if len(token) > 2:
                tokens.add(token)
    return tokens


def _matches_concept(term: str, reference_tokens: set[str], concepts: list[str]) -> bool:
    term_normalized = normalize(term)
    # Estrategia 1: el término normalizado aparece como token exacto en los conceptos de referencia
    if term_normalized in reference_tokens:
        return True
    # Estrategia 2: el término es substring de algún concepto completo
    return any(term_normalized in normalize(c) for c in concepts)


def evaluate(generated_terms: list[str], reference_concepts: list[str]) -> PrecisionResult:
    # Construye el conjunto de tokens de referencia para matching eficiente
    ref_tokens = _reference_tokens(reference_concepts)

    # Clasifica cada término generado como coincidencia o no con los conceptos de referencia
    matched_generated = [t for t in generated_terms if _matches_concept(t, ref_tokens, reference_concepts)]
    unmatched_generated = [t for t in generated_terms if t not in matched_generated]

    # Determina qué conceptos de referencia fueron cubiertos por algún término generado
    matched_concepts = [c for c in reference_concepts if any(
        normalize(w) in normalize(c) or normalize(c) in normalize(w)
        for w in generated_terms
    )]
    unmatched_concepts = [c for c in reference_concepts if c not in matched_concepts]

    # Precision = términos relevantes / total términos generados
    precision = round(len(matched_generated) / len(generated_terms), 4) if generated_terms else 0.0
    # Recall = conceptos cubiertos / total conceptos de referencia
    recall = round(len(matched_concepts) / len(reference_concepts), 4) if reference_concepts else 0.0
    # F1 = media armónica de precision y recall (0 si ambos son 0)
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) > 0 else 0.0

    # Construye la explicación detallada paso a paso para mostrar en la interfaz
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

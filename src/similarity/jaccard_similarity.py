from src.processing.text_preprocessing import tokenize
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult


class JaccardSimilarity(BaseSimilarity):
    """
    Similitud de Jaccard basada en conjuntos de palabras.
    J(A, B) = |A ∩ B| / |A ∪ B|
    Resultado en [0, 1]. No considera frecuencia, solo presencia.
    Complejidad: O(n + m)
    """

    @property
    def name(self) -> str:
        return "Jaccard Similarity"

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        set_a = set(tokenize(text_a))
        set_b = set(tokenize(text_b))

        intersection = set_a & set_b
        union = set_a | set_b

        score = round(len(intersection) / len(union), 4) if union else 1.0

        steps = [
            f"1. Tokenización y eliminación de stopwords.",
            f"   Vocabulario A ({len(set_a)} términos únicos): {sorted(set_a)[:6]}...",
            f"   Vocabulario B ({len(set_b)} términos únicos): {sorted(set_b)[:6]}...",
            f"2. Intersección A ∩ B ({len(intersection)} términos): {sorted(intersection)[:8]}",
            f"3. Unión A ∪ B ({len(union)} términos en total)",
            f"4. Jaccard = |A ∩ B| / |A ∪ B| = {len(intersection)} / {len(union)} = {score}",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

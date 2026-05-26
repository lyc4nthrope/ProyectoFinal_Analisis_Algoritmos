# Importa la función de tokenización y eliminación de stopwords
from src.processing.text_preprocessing import tokenize
# Importa la clase base y la estructura de resultado
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult


class JaccardSimilarity(BaseSimilarity):
    """
    Similitud de Jaccard basada en conjuntos de palabras.
    J(A, B) = |A ∩ B| / |A ∪ B|
    Resultado en [0, 1]. No considera frecuencia, solo presencia.
    Complejidad: O(n + m)
    """

    # Complejidades teóricas del algoritmo para mostrar en la interfaz
    COMPLEXITY_TIME = "O(n + m)"
    COMPLEXITY_SPACE = "O(n + m)"

    @property
    def name(self) -> str:
        return "Jaccard Similarity"

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        # Tokeniza cada texto y convierte a conjunto (elimina duplicados)
        set_a = set(tokenize(text_a))
        set_b = set(tokenize(text_b))

        # Calcula la intersección: palabras que aparecen en AMBOS textos
        intersection = set_a & set_b
        # Calcula la unión: todas las palabras únicas entre los dos textos
        union = set_a | set_b

        # J(A,B) = |A∩B| / |A∪B|; si la unión es vacía (textos vacíos), similitud = 1
        score = round(len(intersection) / len(union), 4) if union else 1.0

        # Construye la explicación paso a paso para mostrar en la interfaz
        steps = [
            f"1. Tokenización y eliminación de stopwords.",
            f"   Vocabulario A ({len(set_a)} términos únicos): {sorted(set_a)[:6]}...",
            f"   Vocabulario B ({len(set_b)} términos únicos): {sorted(set_b)[:6]}...",
            f"2. Intersección A ∩ B ({len(intersection)} términos): {sorted(intersection)[:8]}",
            f"3. Unión A ∪ B ({len(union)} términos en total)",
            f"4. Jaccard = |A ∩ B| / |A ∪ B| = {len(intersection)} / {len(union)} = {score}",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

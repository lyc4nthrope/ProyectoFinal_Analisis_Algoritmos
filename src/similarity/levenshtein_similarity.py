from src.processing.text_preprocessing import tokenize
from src.similarity.base_similarity import BaseSimilarity, SimilarityResult


class LevenshteinSimilarity(BaseSimilarity):
    """
    Distancia de edición a nivel de palabras (Word Edit Distance).
    Cuenta el número mínimo de inserciones, eliminaciones y sustituciones
    de palabras necesarias para transformar una secuencia en otra.
    Complejidad: O(n × m) donde n y m son la cantidad de tokens de cada texto.
    """

    @property
    def name(self) -> str:
        return "Levenshtein (Word Edit Distance)"

    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult:
        tokens_a = tokenize(text_a)
        tokens_b = tokenize(text_b)

        distance = self._word_edit_distance(tokens_a, tokens_b)
        max_len = max(len(tokens_a), len(tokens_b))
        score = round(1 - distance / max_len, 4) if max_len > 0 else 1.0

        steps = [
            f"1. Preprocesamiento: tokenización y eliminación de stopwords.",
            f"   Tokens A ({len(tokens_a)}): {tokens_a[:8]}{'...' if len(tokens_a) > 8 else ''}",
            f"   Tokens B ({len(tokens_b)}): {tokens_b[:8]}{'...' if len(tokens_b) > 8 else ''}",
            f"2. Construcción de matriz DP de tamaño ({len(tokens_a)+1} × {len(tokens_b)+1}).",
            f"   Cada celda dp[i][j] = costo mínimo de transformar tokens_A[:i] en tokens_B[:j].",
            f"   Operaciones: inserción (+1), eliminación (+1), sustitución (+1 si tokens distintos).",
            f"3. Distancia de edición (dp[n][m]) = {distance}",
            f"4. Normalización: similitud = 1 - {distance} / max({len(tokens_a)}, {len(tokens_b)})",
            f"   similitud = 1 - {distance} / {max_len} = {score}",
        ]

        return SimilarityResult(algorithm=self.name, score=score, steps=steps)

    def _word_edit_distance(self, a: list[str], b: list[str]) -> int:
        n, m = len(a), len(b)
        dp = list(range(m + 1))

        for i in range(1, n + 1):
            prev = dp[0]
            dp[0] = i
            for j in range(1, m + 1):
                temp = dp[j]
                if a[i - 1] == b[j - 1]:
                    dp[j] = prev
                else:
                    dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                prev = temp

        return dp[m]

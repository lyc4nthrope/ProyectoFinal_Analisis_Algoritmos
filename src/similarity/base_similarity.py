from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SimilarityResult:
    algorithm: str
    score: float
    steps: list[str] = field(default_factory=list)


class BaseSimilarity(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    def fit(self, corpus: list[str]) -> "BaseSimilarity":
        return self

    @abstractmethod
    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult: ...

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        n = len(texts)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                score = self.compute_pair(texts[i], texts[j]).score
                matrix[i][j] = score
                matrix[j][i] = score
        return matrix

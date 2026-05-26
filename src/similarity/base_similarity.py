# Importa ABC y abstractmethod para definir la interfaz que todos los algoritmos deben cumplir
from abc import ABC, abstractmethod
# Importa dataclass y field para definir estructuras de datos simples
from dataclasses import dataclass, field
# Importa Callable para tipar funciones de callback
from typing import Callable


# Token de cancelación: permite interrumpir cálculos largos desde la interfaz
class CancelToken:
    def __init__(self) -> None:
        # Estado inicial: no cancelado
        self._cancelled = False

    def cancel(self) -> None:
        # Marca el token como cancelado; el código que lo consulte debe detenerse
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        # Propiedad de solo lectura para consultar el estado de cancelación
        return self._cancelled


# Tipo alias para las funciones de progreso: reciben (nombre_algoritmo, mensaje)
ProgressCallback = Callable[[str, str], None]


# Estructura de datos que guarda el resultado de un cálculo de similitud
@dataclass
class SimilarityResult:
    algorithm: str          # Nombre del algoritmo que produjo este resultado
    score: float            # Score de similitud en rango [0.0, 1.0]
    steps: list[str] = field(default_factory=list)  # Pasos del cálculo matemático explicado
    time_ms: float = 0.0                            # Tiempo de ejecución en milisegundos
    complexity_time: str = ""                       # Complejidad temporal (ej: "O(n²)")
    complexity_space: str = ""                      # Complejidad espacial (ej: "O(n)")
    title: str = ""                                 # Título del artículo comparado (en búsquedas)


# Clase base abstracta que define el contrato de todos los algoritmos de similitud
class BaseSimilarity(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    def fit(self, corpus: list[str]) -> "BaseSimilarity":
        # Por defecto, fit() no hace nada; los algoritmos que necesitan entrenar lo sobreescriben
        return self

    @abstractmethod
    def compute_pair(self, text_a: str, text_b: str) -> SimilarityResult: ...

    def compute_matrix(self, texts: list[str]) -> list[list[float]]:
        # Implementación base O(N²): calcula cada par (i, j) individualmente
        n = len(texts)
        # Inicializa la matriz con ceros
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            # La diagonal siempre es 1.0 (un texto es idéntico a sí mismo)
            matrix[i][i] = 1.0
            for j in range(i + 1, n):
                # Calcula el score del par (i, j) y lo guarda simétricamente en (j, i)
                score = self.compute_pair(texts[i], texts[j]).score
                matrix[i][j] = score
                matrix[j][i] = score
        return matrix

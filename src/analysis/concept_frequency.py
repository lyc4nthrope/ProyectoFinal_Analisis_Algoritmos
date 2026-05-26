# Importa re para usar expresiones regulares en la búsqueda de conceptos en los abstracts
import re
# Importa dataclass para definir la estructura de resultado de manera limpia
from dataclasses import dataclass

# Importa la función de normalización de texto para comparar sin acentos ni mayúsculas
from src.processing.text_preprocessing import normalize


# Estructura que guarda los resultados de frecuencia para un concepto específico
@dataclass
class ConceptFrequencyResult:
    concept: str            # Nombre del concepto analizado
    total_occurrences: int  # Suma de apariciones en todos los documentos
    document_count: int     # Número de documentos donde aparece al menos una vez
    per_document: list[int] # Lista con el conteo de apariciones en cada documento


def compute_frequencies(abstracts: list[str], concepts: list[str]) -> list[ConceptFrequencyResult]:
    # Normaliza todos los abstracts una sola vez para evitar repetir la operación
    normalized_abstracts = [normalize(abstract) for abstract in abstracts]

    results = []
    for concept in concepts:
        # Compila una expresión regular con límites de palabra para encontrar el concepto exacto
        # \b garantiza que "learning" no coincida con "elearning"
        pattern = re.compile(r"\b" + re.escape(normalize(concept)) + r"\b")
        # Cuenta cuántas veces aparece el concepto en cada abstract
        per_doc = [len(pattern.findall(text)) for text in normalized_abstracts]
        results.append(ConceptFrequencyResult(
            concept=concept,
            total_occurrences=sum(per_doc),                # Total de apariciones en todo el corpus
            document_count=sum(1 for c in per_doc if c > 0),  # Documentos con al menos 1 aparición
            per_document=per_doc,
        ))

    # Ordena los resultados de mayor a menor frecuencia total
    return sorted(results, key=lambda r: r.total_occurrences, reverse=True)

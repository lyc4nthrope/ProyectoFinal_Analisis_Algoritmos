# Importa la implementación de distancia de Levenshtein para comparar strings carácter a carácter
from rapidfuzz.distance import Levenshtein

# Importa la función de normalización de texto para comparar títulos de forma limpia
from src.processing.text_preprocessing import normalize


# Umbral de similitud: dos títulos con similitud >= 0.90 se consideran duplicados
SIMILARITY_THRESHOLD = 0.90


def _similarity(a: str, b: str) -> float:
    # Si alguno de los textos está vacío, la similitud es 0 (no son comparables)
    if not a or not b:
        return 0.0
    # Calcula la distancia de edición entre los dos strings
    distance = Levenshtein.distance(a, b)
    # Normaliza la distancia: 0 = idénticos, 1 = completamente diferentes
    # La fórmula convierte la distancia en similitud restándola de 1
    return 1 - distance / max(len(a), len(b))


def _merge(primary: dict, secondary: dict) -> dict:
    # Copia el artículo principal para no modificar el original
    merged = primary.copy()
    # Para cada campo del artículo secundario, lo agrega si el primario no lo tiene
    for key, value in secondary.items():
        if not merged.get(key) and value:
            merged[key] = value
    return merged


def _count_filled_fields(article: dict) -> int:
    # Cuenta cuántos campos del artículo tienen un valor no vacío/nulo
    return sum(1 for v in article.values() if v)


def _find_match(norm: str, exact_index: dict[str, int], normalized_titles: list[str]) -> int | None:
    # Primero busca coincidencia exacta en el índice O(1) por hash
    if norm in exact_index:
        return exact_index[norm]
    # Si no hay coincidencia exacta, busca coincidencia aproximada por similitud
    for i, existing_norm in enumerate(normalized_titles):
        if _similarity(norm, existing_norm) >= SIMILARITY_THRESHOLD:
            return i
    # Si no hay ninguna coincidencia, retorna None
    return None


def deduplicate(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    # Lista de artículos únicos que se irá construyendo
    unique: list[dict] = []
    # Lista de artículos detectados como duplicados
    duplicates: list[dict] = []
    # Lista de títulos normalizados para búsqueda aproximada por índice
    normalized_titles: list[str] = []
    # Índice hash de título normalizado → posición en la lista unique (búsqueda exacta O(1))
    exact_index: dict[str, int] = {}

    for article in articles:
        # Normaliza el título del artículo actual para comparación
        norm = normalize(article.get("title", ""))
        # Busca si ya existe un artículo similar en la lista de únicos
        matched_index = _find_match(norm, exact_index, normalized_titles)

        if matched_index is not None:
            # Es un duplicado — decide cuál versión es más completa
            existing = unique[matched_index]
            if _count_filled_fields(article) > _count_filled_fields(existing):
                # El artículo nuevo tiene más campos: lo pone como principal y archiva el viejo
                duplicates.append(existing)
                unique[matched_index] = _merge(article, existing)
                exact_index[norm] = matched_index
                normalized_titles[matched_index] = norm
            else:
                # El artículo existente es más completo: el nuevo va a duplicados
                article["duplicate_of"] = existing["title"]
                duplicates.append(article)
        else:
            # Es un artículo nuevo: lo agrega al índice y a la lista de únicos
            exact_index[norm] = len(unique)
            normalized_titles.append(norm)
            unique.append(article)

    return unique, duplicates

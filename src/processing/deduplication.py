import Levenshtein

from src.processing.text_preprocessing import normalize


SIMILARITY_THRESHOLD = 0.90


def _similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    distance = Levenshtein.distance(a, b)
    return 1 - distance / max(len(a), len(b))


def _merge(primary: dict, secondary: dict) -> dict:
    merged = primary.copy()
    for key, value in secondary.items():
        if not merged.get(key) and value:
            merged[key] = value
    return merged


def _count_filled_fields(article: dict) -> int:
    return sum(1 for v in article.values() if v)


def _find_match(norm: str, exact_index: dict[str, int], normalized_titles: list[str]) -> int | None:
    if norm in exact_index:
        return exact_index[norm]
    for i, existing_norm in enumerate(normalized_titles):
        if _similarity(norm, existing_norm) >= SIMILARITY_THRESHOLD:
            return i
    return None


def deduplicate(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    unique: list[dict] = []
    duplicates: list[dict] = []
    normalized_titles: list[str] = []
    exact_index: dict[str, int] = {}

    for article in articles:
        norm = normalize(article.get("title", ""))
        matched_index = _find_match(norm, exact_index, normalized_titles)

        if matched_index is not None:
            existing = unique[matched_index]
            if _count_filled_fields(article) > _count_filled_fields(existing):
                duplicates.append(existing)
                unique[matched_index] = _merge(article, existing)
                exact_index[norm] = matched_index
                normalized_titles[matched_index] = norm
            else:
                article["duplicate_of"] = existing["title"]
                duplicates.append(article)
        else:
            exact_index[norm] = len(unique)
            normalized_titles.append(norm)
            unique.append(article)

    return unique, duplicates

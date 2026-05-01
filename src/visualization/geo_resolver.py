"""
Resuelve el país del primer autor de cada artículo usando la API de CrossRef.
Almacena los resultados en caché para evitar llamadas repetidas.
"""

import json
import re
import time
from pathlib import Path

import requests

from src.config import PROCESSED_DIR

_CACHE_FILE = PROCESSED_DIR / "country_cache.json"
_CROSSREF_URL = "https://api.crossref.org/works/{doi}"
_REQUEST_HEADERS = {"User-Agent": "bibliometria-genai/0.1 (mailto:noseecorp@gmail.com)"}
_REQUEST_TIMEOUT = 10

_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "United States", "u.s.a.": "United States", "u.s.": "United States",
    "united states of america": "United States", "us": "United States",
    "uk": "United Kingdom", "england": "United Kingdom", "scotland": "United Kingdom",
    "uae": "United Arab Emirates", "south korea": "South Korea",
    "p.r. china": "China", "pr china": "China", "peoples republic of china": "China",
}

_KNOWN_COUNTRIES = {
    "afghanistan", "albania", "algeria", "argentina", "australia", "austria",
    "bangladesh", "belgium", "brazil", "canada", "chile", "china", "colombia",
    "croatia", "czech republic", "denmark", "egypt", "ethiopia", "finland",
    "france", "germany", "ghana", "greece", "hong kong", "hungary", "india",
    "indonesia", "iran", "iraq", "ireland", "israel", "italy", "japan", "jordan",
    "kenya", "malaysia", "mexico", "morocco", "netherlands", "new zealand",
    "nigeria", "norway", "pakistan", "peru", "philippines", "poland", "portugal",
    "qatar", "romania", "russia", "saudi arabia", "singapore", "south africa",
    "south korea", "spain", "sri lanka", "sweden", "switzerland", "taiwan",
    "thailand", "turkey", "ukraine", "united arab emirates", "united kingdom",
    "united states", "vietnam",
}


def _load_cache() -> dict[str, str]:
    if _CACHE_FILE.exists():
        return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_doi(doi: str) -> str:
    return re.sub(r"https?://(dx\.)?doi\.org/", "", doi.strip())


def _extract_country_from_affiliation(affiliation: str) -> str | None:
    parts = [p.strip().lower() for p in affiliation.split(",") if p.strip()]
    for part in reversed(parts):
        normalized = re.sub(r"[^a-z\s.]", "", part).strip()
        if normalized in _COUNTRY_ALIASES:
            return _COUNTRY_ALIASES[normalized]
        if normalized in _KNOWN_COUNTRIES:
            return normalized.title()
    return None


def _fetch_country_from_crossref(doi: str) -> str | None:
    try:
        url = _CROSSREF_URL.format(doi=_clean_doi(doi))
        response = requests.get(url, headers=_REQUEST_HEADERS, timeout=_REQUEST_TIMEOUT)
        if response.status_code != 200:
            return None
        authors = response.json().get("message", {}).get("author", [])
        if not authors:
            return None
        affiliations = authors[0].get("affiliation", [])
        for aff in affiliations:
            country = _extract_country_from_affiliation(aff.get("name", ""))
            if country:
                return country
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def resolve_countries(dois: list[str], delay: float = 0.5) -> dict[str, str]:
    """
    Devuelve un dict {doi: country} para cada DOI de la lista.
    Usa caché local para evitar llamadas repetidas a CrossRef.
    """
    cache = _load_cache()
    updated = False

    for doi in dois:
        if not doi or doi in cache:
            continue
        country = _fetch_country_from_crossref(doi)
        cache[doi] = country or "Unknown"
        updated = True
        time.sleep(delay)

    if updated:
        _save_cache(cache)

    return {doi: cache.get(doi, "Unknown") for doi in dois if doi}

"""
Resuelve el país del primer autor de cada artículo usando la API de CrossRef.
Almacena los resultados en caché para evitar llamadas repetidas.
"""

# Importa json para leer y escribir el archivo de caché de países
import json
# Importa re para extraer el país limpio de las cadenas de afiliación
import re
# Importa time para hacer pausas entre solicitudes a CrossRef (respeto de rate limits)
import time
# Importa Path para manejo de rutas
from pathlib import Path

# Importa requests para hacer peticiones HTTP a la API de CrossRef
import requests

# Importa la ruta donde se guarda el caché de países
from src.config import PROCESSED_DIR

# Ruta del archivo de caché local (JSON): {doi: "Country"}
_CACHE_FILE = PROCESSED_DIR / "country_cache.json"
# URL de la API de CrossRef para consultar metadatos de un DOI específico
_CROSSREF_URL = "https://api.crossref.org/works/{doi}"
# Cabeceras HTTP con User-Agent descriptivo (buena práctica para APIs académicas)
_REQUEST_HEADERS = {"User-Agent": "bibliometria-genai/0.1 (mailto:noseecorp@gmail.com)"}
# Tiempo máximo de espera por petición a CrossRef
_REQUEST_TIMEOUT = 10

# Diccionario de alias para normalizar nombres de países comunes con variaciones ortográficas
_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "United States", "u.s.a.": "United States", "u.s.": "United States",
    "united states of america": "United States", "us": "United States",
    "uk": "United Kingdom", "england": "United Kingdom", "scotland": "United Kingdom",
    "uae": "United Arab Emirates", "south korea": "South Korea",
    "p.r. china": "China", "pr china": "China", "peoples republic of china": "China",
}

# Conjunto de países conocidos (en minúsculas) para matching directo en las afiliaciones
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
    # Lee el archivo de caché si existe; si no, retorna diccionario vacío
    if _CACHE_FILE.exists():
        return json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def _save_cache(cache: dict[str, str]) -> None:
    # Crea el directorio si no existe antes de guardar el caché
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def _clean_doi(doi: str) -> str:
    # Elimina el prefijo de URL del DOI para obtener solo el identificador limpio
    return re.sub(r"https?://(dx\.)?doi\.org/", "", doi.strip())


def _extract_country_from_affiliation(affiliation: str) -> str | None:
    # Divide la afiliación por comas y limpia cada parte
    parts = [p.strip().lower() for p in affiliation.split(",") if p.strip()]
    # Recorre las partes de atrás hacia adelante (el país suele ser el último elemento)
    for part in reversed(parts):
        # Elimina caracteres especiales excepto letras, espacios y puntos
        normalized = re.sub(r"[^a-z\s.]", "", part).strip()
        # Busca primero en los alias (ej: "usa" → "United States")
        if normalized in _COUNTRY_ALIASES:
            return _COUNTRY_ALIASES[normalized]
        # Luego busca en el conjunto de países conocidos
        if normalized in _KNOWN_COUNTRIES:
            return normalized.title()  # Capitaliza el nombre del país
    return None


def _fetch_country_from_crossref(doi: str) -> str | None:
    try:
        # Construye la URL de CrossRef con el DOI limpio
        url = _CROSSREF_URL.format(doi=_clean_doi(doi))
        response = requests.get(url, headers=_REQUEST_HEADERS, timeout=_REQUEST_TIMEOUT)
        if response.status_code != 200:
            return None
        # Extrae la lista de autores del JSON de respuesta
        authors = (response.json() or {}).get("message", {}).get("author", [])
        if not authors:
            return None
        # Intenta extraer el país de la afiliación del primer autor
        affiliations = authors[0].get("affiliation", [])
        for aff in affiliations:
            country = _extract_country_from_affiliation(aff.get("name", ""))
            if country:
                return country
    except (requests.RequestException, ValueError, KeyError):
        # Si hay cualquier error de red o parseo, retorna None silenciosamente
        pass
    return None


def resolve_countries(dois: list[str], delay: float = 0.5) -> dict[str, str]:
    """
    Devuelve un dict {doi: country} para cada DOI de la lista.
    Usa caché local para evitar llamadas repetidas a CrossRef.
    """
    # Carga el caché existente para no repetir consultas ya realizadas
    cache = _load_cache()
    updated = False

    for doi in dois:
        # Omite DOIs vacíos o ya resueltos en el caché
        if not doi or doi in cache:
            continue
        # Consulta CrossRef para obtener el país del primer autor
        country = _fetch_country_from_crossref(doi)
        # Guarda "Unknown" si no se pudo resolver el país
        cache[doi] = country or "Unknown"
        updated = True
        # Pausa entre consultas para no sobrecargar la API de CrossRef
        time.sleep(delay)

    # Solo guarda el caché si hubo nuevas consultas
    if updated:
        _save_cache(cache)

    # Retorna solo los DOIs de la lista solicitada (filtra los vacíos)
    return {doi: cache.get(doi, "Unknown") for doi in dois if doi}

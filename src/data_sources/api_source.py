"""Fuente de datos que consulta APIs académicas."""

# Importa time para pausar entre peticiones y respetar límites de la API
import time
# Importa urlencode para construir URLs con parámetros de búsqueda de forma segura
from urllib.parse import urlencode

# Importa requests para realizar peticiones HTTP a la API de OpenAlex
import requests

# Tiempo máximo de espera por petición antes de considerarla fallida (segundos)
DEFAULT_TIMEOUT = 30
# Número de reintentos automáticos ante errores de red o del servidor
DEFAULT_RETRIES = 3


class ApiParser:
    """Parser que consulta la API de OpenAlex y devuelve resultados en formato ARTICLE_FIELDS."""

    # URL base de la API pública de OpenAlex (catálogo de literatura académica abierta)
    BASE_URL = "https://api.openalex.org"

    def __init__(self, source_name: str = "OpenAlex"):
        # Guarda el nombre de la fuente para etiquetar los artículos descargados
        self.source_name = source_name

    def search(self, query: str, max_results: int = 25) -> list[dict]:
        """Busca artículos en OpenAlex y devuelve lista de dicts en formato ARTICLE_FIELDS."""
        # Si la búsqueda está vacía, retorna lista vacía sin hacer ninguna petición
        if not query or not query.strip():
            return []

        all_results: list[dict] = []
        total_count = 0
        # El cursor "*" indica la primera página en la paginación basada en cursores de OpenAlex
        cursor = "*"
        # El tamaño de página no puede superar 200 (límite de la API)
        page_size = min(max_results, 200)

        # Descarga páginas consecutivas hasta alcanzar el número de resultados deseado
        while len(all_results) < max_results and cursor:
            # Calcula cuántos resultados pedir en esta página (para no superar max_results)
            page_limit = min(max_results - len(all_results), page_size)
            data = self.fetch_page(query, cursor, page_limit)
            # Registra el total disponible en OpenAlex solo en la primera página
            if total_count == 0:
                total_count = data.get("total", 0)
            results = data.get("results", [])
            if not results:
                break
            all_results.extend(results)
            # El cursor de la siguiente página viene en la respuesta
            cursor = data.get("next_cursor")
            # Pausa de 1 segundo para respetar los límites de tasa de la API
            time.sleep(1)

        # Recorta al máximo solicitado en caso de que la última página traiga de más
        return all_results[:max_results]

    def fetch_page(self, query: str, cursor: str = "*", per_page: int = 25) -> dict:
        """Fetch a single page of results from OpenAlex."""
        # Construye la URL con los parámetros de búsqueda
        url = self._build_url(query, per_page)
        # Realiza la petición HTTP y obtiene el JSON de respuesta
        data = self._request_json(f"{url}&cursor={cursor}")

        # Si la petición falló, retorna una estructura vacía segura
        if data is None:
            return {"results": [], "total": 0, "next_cursor": None}

        # Extrae los resultados y los metadatos de paginación de la respuesta
        results = data.get("results", [])
        total = data.get("meta", {}).get("count", 0)
        next_cursor = data.get("meta", {}).get("next_cursor")

        # Mapea cada "work" de OpenAlex al formato interno ARTICLE_FIELDS
        return {
            "results": [self._to_article(work) for work in results],
            "total": total,
            "next_cursor": next_cursor,
        }

    def _request_json(self, url: str) -> dict | None:
        # Cabeceras HTTP: Accept JSON y User-Agent para identificar la aplicación
        headers = {
            "Accept": "application/json",
            "User-Agent": "Bibliometria-GenAI/0.1.0",
        }

        last_error: Exception | None = None
        # Reintenta la petición hasta DEFAULT_RETRIES veces ante errores recuperables
        for attempt in range(DEFAULT_RETRIES):
            try:
                resp = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
            except requests.exceptions.Timeout as e:
                last_error = TimeoutError(f"OpenAlex no respondió a tiempo: {e}")
            except requests.exceptions.RequestException as e:
                last_error = ConnectionError(f"No se pudo conectar con OpenAlex: {e}")
            else:
                if resp.status_code == 200:
                    try:
                        # Parsea y retorna el cuerpo de la respuesta como diccionario
                        return resp.json()
                    except ValueError as e:
                        raise ValueError("OpenAlex devolvió JSON inválido") from e

                # Códigos de error recuperables: rate limit (429) o errores del servidor (5xx)
                if resp.status_code in {429, 500, 502, 503, 504}:
                    # Si la API indica cuánto esperar con Retry-After, respeta ese tiempo
                    retry_after = resp.headers.get("Retry-After")
                    wait_seconds = float(retry_after) if retry_after else (attempt + 1)
                    last_error = requests.HTTPError(
                        f"OpenAlex respondió {resp.status_code}: {resp.reason}",
                    )
                    if attempt < DEFAULT_RETRIES - 1:
                        time.sleep(wait_seconds)
                        continue
                # Cualquier otro código de error no recuperable lanza excepción inmediatamente
                raise requests.HTTPError(
                    f"OpenAlex responded {resp.status_code}: {resp.reason}",
                )

            # Pausa exponencial entre reintentos para no sobrecargar el servidor
            if attempt < DEFAULT_RETRIES - 1:
                time.sleep(attempt + 1)

        # Si se agotaron los reintentos, lanza el último error registrado
        if last_error is not None:
            raise last_error
        return None

    def _build_url(self, query: str, max_results: int) -> str:
        """Construye la URL de búsqueda de OpenAlex."""
        # Codifica los parámetros de búsqueda en formato URL: query, tamaño de página y orden
        params = urlencode({
            "search": query,
            "per_page": max_results,
            "sort": "cited_by_count:desc",  # Ordena por número de citas descendente
        })
        return f"{self.BASE_URL}/works?{params}"

    def _inverted_index_to_text(self, index: dict | None) -> str:
        # OpenAlex guarda el abstract como índice invertido: {palabra: [posición1, posición2, ...]}
        if not index:
            return ""
        tokens = []
        # Convierte el índice invertido a lista de (posición, palabra)
        for word, positions in index.items():
            for pos in positions:
                tokens.append((pos, word))
        # Ordena por posición para reconstruir el texto en el orden original
        tokens.sort(key=lambda x: x[0])
        # Une las palabras en orden para obtener el abstract como texto plano
        return " ".join(word for _, word in tokens)

    def _to_article(self, work: dict) -> dict:
        """
        Mapea un work de OpenAlex a formato ARTICLE_FIELDS.

        Estructura de un "work" de OpenAlex (simplificada):
        {
            "title": "Scikit-learn: Machine Learning in Python",
            "abstract_inverted_index": {"word": [pos1, pos2], ...},
            "authorships": [{"author": {"display_name": "Autor"}}, ...],
            "keywords": [{"display_name": "keyword"}, ...],
            "publication_year": 2012,
            "primary_location": {
                "landing_page_url": "http://arxiv.org/abs/...",
                "source": {
                    "display_name": "arXiv (Cornell University)",
                    "issn": ["1234-5678"]
                }
            },
            "doi": "https://doi.org/10.48550/arxiv.1201.0490",
            "biblio": {
                "volume": "10",
                "issue": "2",
                "first_page": "100",
                "last_page": "120"
            }
        }
        """
        # authorships[] → lista de autores, cada uno con author.display_name
        authors = "; ".join(
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a and (a.get("author") or {}).get("display_name")
        )
        # keywords[] → lista de keywords, cada una con display_name
        keywords = "; ".join(
            k["display_name"]
            for k in work.get("keywords", [])
            if k and k.get("display_name")
        )
        # biblio → metadatos de publicación (puede ser null en preprints)
        first = (work.get("biblio") or {}).get("first_page")
        last = (work.get("biblio") or {}).get("last_page")
        # Construye el rango de páginas si ambos datos están disponibles
        pages = f"{first}-{last}" if first and last else ""
        # issn → lista, tomamos el primer elemento si existe
        issn_list = ((work.get("primary_location") or {}).get("source") or {}).get("issn", [])
        issn = issn_list[0] if issn_list else ""
        # publication_year → viene como entero, lo pasamos a string
        year = work.get("publication_year")

        return {
            "title": work.get("title", ""),                              # work.title
            "abstract": self._inverted_index_to_text(                    # work.abstract_inverted_index
                work.get("abstract_inverted_index")                      # → se reconstruye a texto plano
            ),
            "authors": authors,                                          # work.authorships[].author.display_name
            "keywords": keywords,                                        # work.keywords[].display_name
            "year": str(year) if year is not None else "",               # work.publication_year
            "journal": ((work.get("primary_location") or {}).get("source") or {}).get(  # work.primary_location.source.display_name
                "display_name", ""
            ),
            "doi": work.get("doi", ""),                                  # work.doi
            "url": (work.get("primary_location") or {}).get(                 # work.primary_location.landing_page_url
                "landing_page_url", ""
            ),
            "volume": (work.get("biblio") or {}).get("volume", ""),          # work.biblio.volume
            "number": (work.get("biblio") or {}).get("issue", ""),           # work.biblio.issue
            "pages": pages,                                              # work.biblio.first_page + last_page
            "issn": issn,                                                # work.primary_location.source.issn[0]
            "source": self.source_name,                                  # constante: "OpenAlex"
        }

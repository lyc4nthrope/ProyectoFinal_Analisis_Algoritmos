from __future__ import annotations

# Importa el parser de la API de OpenAlex para hacer las búsquedas
from src.data_sources import ApiParser

# Tamaño máximo de página que permite la API de OpenAlex por petición
MAX_PAGE_SIZE = 200


class ApiSearchService:
    def __init__(self, parser: ApiParser | None = None) -> None:
        # Usa el parser inyectado o crea uno nuevo por defecto (facilita testing con mocks)
        self.parser = parser or ApiParser()

    def fetch_total_preview(self, query: str) -> dict:
        # Hace una búsqueda rápida de 1 resultado para obtener el total disponible en OpenAlex
        # Esto se usa antes de confirmar una búsqueda masiva para informar al usuario
        return self.parser.fetch_page(query, "*", 1)

    def fetch_next_page(
        self,
        *,
        query: str,
        cursor: str,           # Cursor de paginación de OpenAlex (posición actual)
        fetch_all: bool,       # Si True, trae todas las páginas disponibles
        limit: int,            # Límite máximo de resultados solicitado por el usuario
        loaded: int,           # Cantidad de resultados ya descargados
        target: int,           # Total de resultados que se quieren descargar
        first_fetch: bool,     # Si True, es la primera página de la búsqueda
    ) -> dict | None:
        # Calcula cuántos resultados pedir en esta página
        page_size = self._resolve_page_size(
            fetch_all=fetch_all,
            limit=limit,
            loaded=loaded,
            target=target,
            first_fetch=first_fetch,
        )
        # Si el tamaño calculado es 0 o negativo, ya se alcanzó el límite
        if page_size <= 0:
            return None
        return self.parser.fetch_page(query, cursor, page_size)

    def _resolve_page_size(
        self,
        *,
        fetch_all: bool,
        limit: int,
        loaded: int,
        target: int,
        first_fetch: bool,
    ) -> int:
        if fetch_all:
            # En modo "buscar todos", siempre usa el tamaño máximo por página
            return MAX_PAGE_SIZE
        if first_fetch:
            # Primera página: pide exactamente el límite solicitado (máx 200)
            return min(limit, MAX_PAGE_SIZE)
        # Páginas siguientes: pide solo lo que falta para alcanzar el target
        remaining = max(target - loaded, 0)
        return min(remaining, MAX_PAGE_SIZE)

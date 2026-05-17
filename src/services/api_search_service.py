from __future__ import annotations

from src.data_sources import ApiParser

MAX_PAGE_SIZE = 200


class ApiSearchService:
    def __init__(self, parser: ApiParser | None = None) -> None:
        self.parser = parser or ApiParser()

    def fetch_total_preview(self, query: str) -> dict:
        return self.parser.fetch_page(query, "*", 1)

    def fetch_next_page(
        self,
        *,
        query: str,
        cursor: str,
        fetch_all: bool,
        limit: int,
        loaded: int,
        target: int,
        first_fetch: bool,
    ) -> dict | None:
        page_size = self._resolve_page_size(
            fetch_all=fetch_all,
            limit=limit,
            loaded=loaded,
            target=target,
            first_fetch=first_fetch,
        )
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
            return MAX_PAGE_SIZE
        if first_fetch:
            return min(limit, MAX_PAGE_SIZE)
        remaining = max(target - loaded, 0)
        return min(remaining, MAX_PAGE_SIZE)

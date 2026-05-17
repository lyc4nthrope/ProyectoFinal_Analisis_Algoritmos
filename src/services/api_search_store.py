from __future__ import annotations

import json
from pathlib import Path

from src.config import RAW_DIR


class ApiSearchStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (RAW_DIR / "api_cache" / "search_results.jsonl")

    def clear(self) -> None:
        self.path.unlink(missing_ok=True)

    def append(self, results: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            for result in results:
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    def read_slice(self, start: int, count: int) -> list[dict]:
        results: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if index < start:
                    continue
                if len(results) >= count:
                    break
                results.append(json.loads(line))
        return results

    def read_all(self) -> list[dict]:
        results: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                results.append(json.loads(line))
        return results

    def exists(self) -> bool:
        return self.path.exists()

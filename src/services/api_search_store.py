from __future__ import annotations

# Importa json para serializar/deserializar los resultados de búsqueda en formato JSON Lines
import json
# Importa Path para manejo de rutas del sistema de archivos
from pathlib import Path

# Importa la carpeta de datos crudos donde se guarda el caché de búsquedas
from src.config import RAW_DIR


class ApiSearchStore:
    def __init__(self, path: Path | None = None) -> None:
        # Ruta del archivo JSONL donde se guardan los resultados de búsqueda temporalmente
        # Usa ruta por defecto en data/raw/api_cache/ si no se especifica otra
        self.path = path or (RAW_DIR / "api_cache" / "search_results.jsonl")

    def clear(self) -> None:
        # Borra el archivo de resultados si existe (missing_ok evita error si no existe)
        self.path.unlink(missing_ok=True)

    def append(self, results: list[dict]) -> None:
        # Crea el directorio si no existe
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Agrega los resultados al archivo en formato JSON Lines (un JSON por línea)
        with open(self.path, "a", encoding="utf-8") as handle:
            for result in results:
                # ensure_ascii=False permite caracteres Unicode (ej: tildes en nombres)
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")

    def read_slice(self, start: int, count: int) -> list[dict]:
        # Lee solo un rango de líneas del archivo (para paginación en la UI)
        results: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                # Omite las líneas antes del índice de inicio
                if index < start:
                    continue
                # Para cuando ya se leyeron suficientes resultados
                if len(results) >= count:
                    break
                results.append(json.loads(line))
        return results

    def read_all(self) -> list[dict]:
        # Lee todos los resultados del archivo JSONL (usado al integrar al corpus)
        results: list[dict] = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                results.append(json.loads(line))
        return results

    def exists(self) -> bool:
        # Verifica si hay resultados guardados (para saber si mostrar la tabla en la UI)
        return self.path.exists()

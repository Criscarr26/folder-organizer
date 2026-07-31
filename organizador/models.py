"""Modelos de dominio del organizador.

Todo lo que vive en este módulo es inmutable y libre de efectos secundarios: se
puede construir y comparar en pruebas sin tocar el disco.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class MoveReason(str, Enum):
    """Motivo por el que el planificador propuso mover un archivo."""

    CLASSIFIED = "clasificado"
    DUPLICATE = "duplicado"
    UNDO = "devuelto a su carpeta"


@dataclass(frozen=True)
class Category:
    """Una categoría de archivos y la carpeta destino que le corresponde."""

    name: str
    folder: str
    extensions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class FileInfo:
    """Metadatos de un archivo, leídos una sola vez del disco."""

    path: Path
    size: int
    modified: datetime

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def extension(self) -> str:
        return self.path.suffix.lower()

    @classmethod
    def from_path(cls, path: Path) -> FileInfo:
        stat = path.stat()
        return cls(path, stat.st_size, datetime.fromtimestamp(stat.st_mtime))


@dataclass(frozen=True)
class PlannedMove:
    """Un movimiento propuesto pero todavía no aplicado."""

    source: Path
    destination: Path
    category: str
    reason: MoveReason = MoveReason.CLASSIFIED
    duplicate_of: Path | None = None


@dataclass(frozen=True)
class SkippedFile:
    """Un archivo que el planificador decidió no tocar, y por qué."""

    file: FileInfo
    reason: str


@dataclass
class OrganizePlan:
    """Qué se movería y qué se dejaría igual.

    Es lo único que el executor necesita, así que `--dry-run` y la ejecución
    real recorren exactamente el mismo código de decisión: la simulación no
    puede desviarse de lo que pasa de verdad.
    """

    root: Path
    moves: list[PlannedMove] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)

    @property
    def scanned(self) -> int:
        return len(self.moves) + len(self.skipped)

    @property
    def duplicate_moves(self) -> list[PlannedMove]:
        return [move for move in self.moves if move.reason is MoveReason.DUPLICATE]

    def by_category(self) -> dict[str, list[PlannedMove]]:
        """Agrupa los movimientos por carpeta destino, en orden alfabético."""
        grouped: dict[str, list[PlannedMove]] = {}
        for move in self.moves:
            grouped.setdefault(move.category, []).append(move)
        return dict(sorted(grouped.items()))


@dataclass
class ExecutionResult:
    """Lo que realmente pasó al aplicar un plan."""

    dry_run: bool = False
    moved: int = 0
    duplicates: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def failed(self) -> int:
        return len(self.errors)

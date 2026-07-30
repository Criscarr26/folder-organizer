"""Detección y reubicación de proyectos de código.

Un proyecto no es "una carpeta con archivos .py dentro": una carpeta con un
entorno virtual tiene miles y no es un proyecto. Lo que identifica a un proyecto
es un archivo marcador propio (`package.json`, `pyproject.toml`, `.git`...) o
código fuente propio fuera de las carpetas de dependencias.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .executor import move_directory
from .paths import is_within
from .scanner import ScanFilter

logger = logging.getLogger(__name__)

#: Archivo marcador → tecnología que delata.
PROJECT_MARKERS: dict[str, str] = {
    ".git": "git",
    "package.json": "Node.js",
    "requirements.txt": "Python",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "Pipfile": "Python",
    "environment.yml": "conda",
    "Cargo.toml": "Rust",
    "go.mod": "Go",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "composer.json": "PHP",
    "Gemfile": "Ruby",
    "project.godot": "Godot",
    "Dockerfile": "Docker",
    "CMakeLists.txt": "CMake",
}

#: Igual que arriba, pero por patrón en vez de por nombre exacto.
MARKER_PATTERNS: dict[str, str] = {
    "*.sln": "Visual Studio",
    "*.csproj": ".NET",
    "*.ino": "Arduino",
    "*.uproject": "Unreal",
}

SOURCE_SUFFIXES: frozenset[str] = frozenset({
    ".py", ".ipynb", ".js", ".ts", ".tsx", ".jsx", ".java", ".cs", ".cpp",
    ".c", ".h", ".hpp", ".sql", ".gd", ".ino", ".rs", ".go", ".rb", ".php",
    ".swift", ".kt", ".m", ".r", ".sh", ".ps1",
})


class MoveStatus(str, Enum):
    MOVED = "movido"
    COPIED_NOT_REMOVED = "copiado, pero quedan restos en el origen"
    ALREADY_THERE = "ya estaba en el destino"
    CONFLICT = "ya existe una carpeta con ese nombre en el destino"
    INVALID = "destino inválido"
    ERROR = "error"

    @property
    def is_success(self) -> bool:
        """True si los archivos están en el destino, aunque sobre algo detrás."""
        return self in {MoveStatus.MOVED, MoveStatus.COPIED_NOT_REMOVED}


@dataclass(frozen=True)
class ProjectCandidate:
    """Una carpeta que parece un proyecto, con las pruebas que lo sugieren."""

    path: Path
    markers: tuple[str, ...]
    source_files: int

    @property
    def is_git_repo(self) -> bool:
        return "git" in self.markers

    @property
    def confidence(self) -> str:
        if self.is_git_repo or (self.markers and self.source_files):
            return "alta"
        if self.markers or self.source_files >= 5:
            return "media"
        return "baja"

    def describe(self) -> str:
        parts = list(self.markers) or ["sin marcadores"]
        return f"{', '.join(parts)} · {self.source_files} archivo(s) de código"


@dataclass(frozen=True)
class ProjectMoveResult:
    candidate: ProjectCandidate
    status: MoveStatus
    destination: Path | None = None
    detail: str = ""


class ProjectDetector:
    """Busca proyectos entre las subcarpetas de una o varias raíces."""

    def __init__(
        self,
        scan_filter: ScanFilter | None = None,
        *,
        nested_depth: int = 3,
        monorepo_threshold: int = 2,
    ) -> None:
        self._filter = scan_filter or ScanFilter()
        self._nested_depth = nested_depth
        self._monorepo_threshold = monorepo_threshold

    def detect(self, root: Path) -> list[ProjectCandidate]:
        """Proyectos bajo `root`.

        Si una subcarpeta no es un proyecto se mira un nivel más abajo: así se
        encuentra `GD/genetic-dash-og` sin arrastrar la carpeta contenedora, que
        puede tener grabaciones y hojas de cálculo que no son parte del código.
        """
        root = Path(root)
        if not root.is_dir():
            logger.warning("No existe la carpeta %s", root)
            return []
        return self._detect_in(root, depth=self._nested_depth)

    def _detect_in(self, folder: Path, depth: int) -> list[ProjectCandidate]:
        found: list[ProjectCandidate] = []
        for child in self._subdirectories(folder):
            candidate = self.inspect(child)
            if candidate is not None:
                found.append(candidate)
                continue
            if depth <= 1:
                continue

            nested = self._detect_in(child, depth - 1)
            if len(nested) >= self._monorepo_threshold:
                # Varios proyectos hermanos bajo una carpeta que no es proyecto:
                # es un monorepo, y moverlos por separado lo rompería.
                found.append(self._as_monorepo(child, nested))
            else:
                found.extend(nested)
        return found

    def inspect(self, folder: Path) -> ProjectCandidate | None:
        """Examina una carpeta concreta. Devuelve None si no parece proyecto.

        Sólo cuenta lo que hay en el primer nivel de la carpeta. Mirar más abajo
        haría que cualquier carpeta que *contiene* un proyecto pareciera un
        proyecto ella misma, y se movería de más.
        """
        if not folder.is_dir():
            return None
        markers = self._find_markers(folder)
        source_files = self._count_source_files(folder)
        if not markers and source_files == 0:
            return None
        return ProjectCandidate(
            path=folder, markers=tuple(sorted(set(markers))), source_files=source_files
        )

    @staticmethod
    def _as_monorepo(folder: Path, nested: list[ProjectCandidate]) -> ProjectCandidate:
        markers = {"monorepo"}
        for candidate in nested:
            markers.update(candidate.markers)
        return ProjectCandidate(
            path=folder,
            markers=tuple(sorted(markers)),
            source_files=sum(candidate.source_files for candidate in nested),
        )

    def _find_markers(self, folder: Path) -> list[str]:
        markers: list[str] = []
        if (folder / ".git").exists():
            markers.append(PROJECT_MARKERS[".git"])
        for name, technology in PROJECT_MARKERS.items():
            if name != ".git" and (folder / name).is_file():
                markers.append(technology)
        for pattern, technology in MARKER_PATTERNS.items():
            if any(folder.glob(pattern)):
                markers.append(technology)
        return markers

    @staticmethod
    def _count_source_files(folder: Path) -> int:
        try:
            entries = list(folder.iterdir())
        except OSError as exc:
            logger.warning("No se pudo leer %s: %s", folder, exc)
            return 0
        return sum(
            1
            for entry in entries
            if entry.is_file() and entry.suffix.lower() in SOURCE_SUFFIXES
        )

    def _subdirectories(self, folder: Path) -> list[Path]:
        try:
            return sorted(
                child
                for child in folder.iterdir()
                if child.is_dir() and self._filter.allows_dir(child)
            )
        except OSError as exc:
            logger.warning("No se pudo leer %s: %s", folder, exc)
            return []


class ProjectMover:
    """Mueve carpetas de proyecto al destino, sin sobrescribir nada.

    Ante una colisión de nombres no inventa un nombre nuevo: avisa y no toca
    nada. Dos carpetas con el mismo nombre suelen ser dos versiones del mismo
    proyecto, y fundirlas a ciegas es justo lo que no hay que hacer.
    """

    def __init__(self, destination: Path, *, dry_run: bool = False) -> None:
        self.destination = Path(destination).resolve()
        self._dry_run = dry_run

    def move(self, candidate: ProjectCandidate) -> ProjectMoveResult:
        source = candidate.path.resolve()

        if is_within(source, self.destination):
            return ProjectMoveResult(candidate, MoveStatus.ALREADY_THERE)
        if is_within(self.destination, source):
            return ProjectMoveResult(
                candidate, MoveStatus.INVALID,
                detail="el destino está dentro de la carpeta que se movería",
            )

        target = self.destination / source.name
        if target.exists():
            return ProjectMoveResult(
                candidate, MoveStatus.CONFLICT, destination=target,
                detail=f"ya existe {target}",
            )

        try:
            fully_moved = move_directory(source, target, dry_run=self._dry_run)
        except OSError as exc:
            logger.error("No se pudo mover %s: %s", source, exc)
            return ProjectMoveResult(candidate, MoveStatus.ERROR, detail=str(exc))

        if fully_moved:
            return ProjectMoveResult(candidate, MoveStatus.MOVED, destination=target)
        return ProjectMoveResult(
            candidate,
            MoveStatus.COPIED_NOT_REMOVED,
            destination=target,
            detail=f"revisa y borra a mano: {source}",
        )

    def move_all(self, candidates: list[ProjectCandidate]) -> list[ProjectMoveResult]:
        return [self.move(candidate) for candidate in candidates]

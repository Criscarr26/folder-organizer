"""Recorrido del disco: decide qué archivos y carpetas son candidatos.

Separar el recorrido de la clasificación es lo que permite excluir carpetas
enteras (`.git`, `node_modules`, `Github repository`) en un único sitio, en vez
de repetir comprobaciones en cada operación.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .models import FileInfo

logger = logging.getLogger(__name__)


class ScanMode(str, Enum):
    """Cómo recorrer una ruta."""

    #: Sólo los archivos que están directamente en la raíz. No entra en
    #: subcarpetas, así que no puede aplanar una jerarquía existente.
    LOOSE = "loose"

    #: Todo el árbol, ordenando los archivos de cada carpeta dentro de esa misma
    #: carpeta. Preserva la jerarquía (útil para carpetas por asignatura).
    PER_FOLDER = "per-folder"


#: Carpetas en las que nunca se entra: metadatos de herramientas, entornos
#: virtuales, dependencias descargadas y la cuarentena de duplicados.
DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset({
    ".git", ".svn", ".hg",
    ".venv", "venv", "env", ".conda", "site-packages",
    "node_modules", "bower_components", "vendor",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".idea", ".vs", ".vscode", ".claude", ".cache",
    "dist", "build", ".next", ".nuxt", ".expo", ".gradle",
    "_duplicados",
    # El destino de los proyectos: el organizador nunca reordena su contenido.
    "github repository",
})

#: Archivos de sistema que romperían algo si se movieran.
PROTECTED_FILENAMES: frozenset[str] = frozenset({
    "desktop.ini", "thumbs.db", ".ds_store", "icon\r", "organizer.log",
})

#: Accesos directos y marcadores: apuntan a otra cosa desde donde están, así
#: que moverlos no ordena nada, sólo rompe la referencia del usuario.
PROTECTED_SUFFIXES: frozenset[str] = frozenset({".lnk", ".url", ".tmp", ".crdownload", ".part"})


@dataclass(frozen=True)
class ScanFilter:
    """Qué se puede tocar. Comparaciones sin distinguir mayúsculas (Windows)."""

    excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS
    excluded_paths: frozenset[Path] = frozenset()
    protected_filenames: frozenset[str] = PROTECTED_FILENAMES
    protected_suffixes: frozenset[str] = PROTECTED_SUFFIXES
    skip_hidden: bool = True

    _normalized_dirs: frozenset[str] = field(init=False, repr=False, compare=False)
    _normalized_paths: frozenset[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_normalized_dirs", frozenset(d.casefold() for d in self.excluded_dirs)
        )
        object.__setattr__(
            self,
            "_normalized_paths",
            frozenset(os.path.normcase(os.path.abspath(p)) for p in self.excluded_paths),
        )

    @classmethod
    def build(
        cls,
        extra_dirs: frozenset[str] | set[str] | None = None,
        excluded_paths: frozenset[Path] | set[Path] | None = None,
    ) -> ScanFilter:
        """Combina las exclusiones por defecto con las que pida quien llama."""
        return cls(
            excluded_dirs=DEFAULT_EXCLUDED_DIRS | frozenset(extra_dirs or ()),
            excluded_paths=frozenset(excluded_paths or ()),
        )

    def allows_dir(self, path: Path) -> bool:
        if path.name.casefold() in self._normalized_dirs:
            return False
        if self.skip_hidden and path.name.startswith("."):
            return False
        return not self._is_excluded_path(path)

    def allows_file(self, path: Path) -> bool:
        name = path.name
        if name.casefold() in self.protected_filenames:
            return False
        if path.suffix.casefold() in self.protected_suffixes:
            return False
        if self.skip_hidden and name.startswith("."):
            return False
        return not self._is_excluded_path(path)

    def _is_excluded_path(self, path: Path) -> bool:
        return os.path.normcase(os.path.abspath(path)) in self._normalized_paths


class FileScanner:
    """Produce `FileInfo` para los archivos que el filtro permite."""

    def __init__(self, scan_filter: ScanFilter | None = None) -> None:
        self._filter = scan_filter or ScanFilter()

    def groups(self, root: Path, mode: ScanMode) -> list[tuple[Path, list[FileInfo]]]:
        """Devuelve pares (carpeta ancla, archivos que le pertenecen).

        La carpeta ancla es donde se crearán las subcarpetas por categoría. El
        árbol se recorre entero antes de devolver nada, para que crear carpetas
        durante la ejecución no altere lo que se está recorriendo.
        """
        if mode is ScanMode.LOOSE:
            files = self._files_in(root)
            return [(root, files)] if files else []
        return self._walk(root)

    def _walk(self, root: Path) -> list[tuple[Path, list[FileInfo]]]:
        groups: list[tuple[Path, list[FileInfo]]] = []
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=self._on_error):
            current = Path(dirpath)
            # Podar in-place: os.walk no entra en lo que quitemos de `dirnames`.
            dirnames[:] = sorted(d for d in dirnames if self._filter.allows_dir(current / d))
            files = self._files_in(current, filenames)
            if files:
                groups.append((current, files))
        return groups

    def _files_in(self, directory: Path, names: list[str] | None = None) -> list[FileInfo]:
        if names is None:
            try:
                names = [entry.name for entry in directory.iterdir() if entry.is_file()]
            except OSError as exc:
                logger.warning("No se pudo leer la carpeta %s: %s", directory, exc)
                return []

        files: list[FileInfo] = []
        for name in sorted(names):
            path = directory / name
            if not self._filter.allows_file(path):
                continue
            try:
                files.append(FileInfo.from_path(path))
            except OSError as exc:  # enlaces roto, permisos, ruta demasiado larga
                logger.warning("No se pudo leer el archivo %s: %s", path, exc)
        return files

    @staticmethod
    def _on_error(exc: OSError) -> None:
        logger.warning("No se pudo recorrer %s: %s", getattr(exc, "filename", "?"), exc)

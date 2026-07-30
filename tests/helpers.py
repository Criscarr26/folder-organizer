"""Utilidades compartidas por las pruebas."""

from __future__ import annotations

from pathlib import Path

from organizador.models import FileInfo


def write(path: Path, content: str | None = None) -> Path:
    """Crea el archivo (y sus carpetas) con el contenido dado.

    Por defecto el contenido es el propio nombre del archivo: así dos archivos
    distintos nunca resultan ser duplicados por accidente, que es lo que pasaría
    con un contenido fijo para todos.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(path.name if content is None else content, encoding="utf-8")
    return path


def make_file_info(path: Path, content: str | None = None) -> FileInfo:
    return FileInfo.from_path(write(path, content))


def tree(root: Path) -> set[str]:
    """Rutas relativas de todos los archivos bajo `root`, con '/' como separador."""
    return {
        str(item.relative_to(root)).replace("\\", "/")
        for item in root.rglob("*")
        if item.is_file()
    }

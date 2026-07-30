"""Utilidades de rutas compartidas por el planificador y el movedor.

Windows no distingue mayúsculas y su límite clásico de ruta es de 260
caracteres; las dos cosas se resuelven aquí una sola vez.
"""

from __future__ import annotations

import os
from collections.abc import Container
from pathlib import Path

#: Margen sobre el límite clásico de Windows (260) dejando sitio al nombre.
MAX_PATH_LENGTH = 255


def is_within(path: Path, parent: Path) -> bool:
    """True si `path` es `parent` o está dentro de él, ignorando mayúsculas."""
    path_norm = os.path.normcase(os.path.abspath(path))
    parent_norm = os.path.normcase(os.path.abspath(parent))
    return path_norm == parent_norm or path_norm.startswith(parent_norm + os.sep)


def unique_path(preferred: Path, claimed: Container[Path] = frozenset()) -> Path:
    """Un destino libre a partir de `preferred`, añadiendo `_1`, `_2`...

    `claimed` son destinos ya reservados por el plan en curso. Sin ese conjunto
    el plan asignaría el mismo nombre a dos archivos y la simulación mentiría
    sobre el resultado real.
    """
    candidate = preferred
    counter = 1
    while candidate in claimed or candidate.exists():
        candidate = preferred.with_name(f"{preferred.stem}_{counter}{preferred.suffix}")
        counter += 1
    return candidate


def relative_to_root(path: Path, root: Path) -> str:
    """Ruta relativa a `root` para mostrar; la absoluta si no está dentro."""
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def is_too_long(path: Path) -> bool:
    return len(str(path)) > MAX_PATH_LENGTH

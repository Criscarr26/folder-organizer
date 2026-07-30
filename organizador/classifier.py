"""Clasificación de archivos. Función pura sobre un `Ruleset`."""

from __future__ import annotations

from .models import Category, FileInfo
from .rules import Ruleset


class FileClassifier:
    """Traduce un archivo a la categoría que le toca.

    No toca el disco: recibe un `FileInfo` ya leído. Así se puede probar la
    tabla de reglas completa sin crear un solo archivo.
    """

    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    def classify(self, file: FileInfo) -> Category:
        return self.ruleset.category_for(file.extension)

    def summarize(self, files: list[FileInfo]) -> dict[Category, list[FileInfo]]:
        """Agrupa archivos por categoría, para el comando `analyze`."""
        grouped: dict[Category, list[FileInfo]] = {}
        for file in files:
            grouped.setdefault(self.classify(file), []).append(file)
        return dict(sorted(grouped.items(), key=lambda item: item[0].folder))

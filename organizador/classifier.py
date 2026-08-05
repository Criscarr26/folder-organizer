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

    def classify(self, file: FileInfo) -> Category | None:
        """La categoría del archivo, o None si no hay regla que lo cubra."""
        return self.ruleset.category_for(file.extension)

    def summarize(self, files: list[FileInfo]) -> dict[Category, list[FileInfo]]:
        """Agrupa archivos por categoría, para el comando `analyze`.

        Los archivos sin categoría no aparecen: el comando informa de lo que se
        movería, y ésos se quedan donde están.
        """
        grouped: dict[Category, list[FileInfo]] = {}
        for file in files:
            category = self.classify(file)
            if category is not None:
                grouped.setdefault(category, []).append(file)
        return dict(sorted(grouped.items(), key=lambda item: item[0].folder))

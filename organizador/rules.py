"""Reglas de clasificación: qué extensión termina en qué carpeta."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from .models import Category

logger = logging.getLogger(__name__)

FALLBACK_CATEGORY = Category(name="otros", folder="Otros")

#: Reglas por defecto. El formato coincide con el del JSON de configuración,
#: para que `init-config` pueda volcarlas tal cual y el usuario editarlas.
DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "imagenes": {
        "folder": "Imágenes",
        "extensions": [
            ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",
            ".svg", ".heic", ".tif", ".tiff", ".ico",
        ],
    },
    "documentos": {
        "folder": "Documentos",
        "extensions": [
            ".pdf", ".doc", ".docx", ".txt", ".odt",
            ".rtf", ".md", ".tex", ".epub",
        ],
    },
    "hojas_de_calculo": {
        "folder": "Hojas de cálculo",
        "extensions": [".xls", ".xlsx", ".xlsm", ".csv", ".tsv", ".ods"],
    },
    "presentaciones": {
        "folder": "Presentaciones",
        "extensions": [".ppt", ".pptx", ".odp", ".key"],
    },
    "videos": {
        "folder": "Videos",
        "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    },
    "audio": {
        "folder": "Audio",
        "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma"],
    },
    "comprimidos": {
        "folder": "Comprimidos",
        "extensions": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"],
    },
    "codigo": {
        "folder": "Código",
        "extensions": [
            ".py", ".ipynb", ".js", ".ts", ".tsx", ".jsx", ".java", ".cs",
            ".cpp", ".c", ".h", ".sql", ".html", ".css", ".sh", ".ps1",
            ".ino", ".gd", ".json", ".yml", ".yaml",
        ],
    },
    "instaladores": {
        "folder": "Instaladores",
        "extensions": [".exe", ".msi", ".msix", ".apk", ".deb", ".dmg"],
    },
}


class Ruleset:
    """Índice extensión → categoría, construido una sola vez.

    Ante extensiones repetidas en varias categorías gana la primera declarada,
    y se avisa por log: fallar en silencio con reglas contradictorias es peor
    que una regla ignorada de forma predecible.
    """

    def __init__(
        self,
        categories: Iterable[Category],
        fallback: Category | None = FALLBACK_CATEGORY,
    ) -> None:
        self.categories = tuple(categories)
        self.fallback = fallback
        self.extension_map: dict[str, Category] = {}
        for category in self.categories:
            for extension in category.extensions:
                key = extension.lower()
                existing = self.extension_map.get(key)
                if existing is not None:
                    logger.warning(
                        "La extensión %s está en '%s' y en '%s'; se usará '%s'.",
                        key, existing.name, category.name, existing.name,
                    )
                    continue
                self.extension_map[key] = category

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Mapping[str, Any]],
        fallback: Category | None = FALLBACK_CATEGORY,
    ) -> Ruleset:
        """Construye un `Ruleset` desde la estructura del JSON de configuración."""
        categories = []
        for name, config in mapping.items():
            extensions = config.get("extensions", [])
            if isinstance(extensions, str):  # tolera "extensions": ".pdf"
                extensions = [extensions]
            categories.append(
                Category(
                    name=name,
                    folder=str(config.get("folder", name)),
                    extensions=frozenset(str(ext).lower() for ext in extensions),
                )
            )
        return cls(categories, fallback)

    @classmethod
    def default(cls) -> Ruleset:
        return cls.from_mapping(DEFAULT_RULES)

    def category_for(self, extension: str) -> Category | None:
        """La categoría de una extensión, o None si no hay dónde ponerla.

        Devuelve None sólo cuando el ruleset se construyó sin comodín. Es la
        diferencia entre "lo que no reconozco va a Otros/" y "lo que no
        reconozco no se toca", y hace falta para ordenar una carpeta donde
        conviven documentos con cosas que no deben moverse: los PNG de un tema
        de iconos, los .dll de un paquete, el código de un proyecto.
        """
        return self.extension_map.get(extension.lower(), self.fallback)

    @property
    def folders(self) -> frozenset[str]:
        """Nombres de las carpetas destino.

        El scanner las excluye para que volver a ejecutar el organizador sobre
        una carpeta ya ordenada no vuelva a barajar lo que ya está en su sitio.
        """
        nombres = [category.folder for category in self.categories]
        if self.fallback is not None:
            nombres.append(self.fallback.folder)
        return frozenset(nombres)

    def to_mapping(self) -> dict[str, dict[str, Any]]:
        return {
            category.name: {
                "folder": category.folder,
                "extensions": sorted(category.extensions),
            }
            for category in self.categories
        }

"""Detección de archivos duplicados por contenido.

Dos decisiones importantes de este módulo:

* Se agrupa por tamaño antes de hashear. Dos archivos de tamaño distinto no
  pueden ser iguales, así que la mayoría nunca se llega a leer.
* Los archivos que OneDrive tiene sólo en la nube no se hashean. Leerlos
  forzaría a descargarlos, y ordenar la carpeta no debería consumir el disco ni
  los datos del usuario.
"""

from __future__ import annotations

import hashlib
import logging
import os
from enum import Enum
from pathlib import Path

from .models import FileInfo

logger = logging.getLogger(__name__)

#: Carpeta de cuarentena. Los duplicados se mueven aquí; nunca se borran.
QUARANTINE_FOLDER = "_Duplicados"

_CHUNK_SIZE = 1024 * 1024

# Atributos de Windows que marcan un archivo como "sólo en la nube".
_FILE_ATTRIBUTE_OFFLINE = 0x00001000
_FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
_FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
_CLOUD_ATTRIBUTES = (
    _FILE_ATTRIBUTE_OFFLINE
    | _FILE_ATTRIBUTE_RECALL_ON_OPEN
    | _FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
)


class DuplicatePolicy(str, Enum):
    """Qué hacer con un archivo cuyo contenido ya apareció antes.

    No existe una política de borrado: la cuarentena deja la decisión de borrar
    en manos del usuario, que es quien puede juzgar qué copia le importa.
    """

    QUARANTINE = "quarantine"
    REPORT = "report"
    IGNORE = "ignore"


def is_cloud_placeholder(path: Path) -> bool:
    """True si el archivo no está descargado (OneDrive Files On-Demand)."""
    try:
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & _CLOUD_ATTRIBUTES)


def file_digest(path: Path) -> str:
    """SHA-256 del contenido, leído por bloques para no cargarlo en memoria."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while chunk := handle.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


class DuplicateIndex:
    """Recuerda lo ya visto y contesta si un archivo nuevo es copia de otro."""

    def __init__(self) -> None:
        # tamaño → [(ruta, hash o None si aún no se ha calculado)]
        self._by_size: dict[int, list[tuple[Path, str | None]]] = {}
        self.skipped_cloud: list[Path] = []

    def find_duplicate(self, file: FileInfo) -> Path | None:
        """Registra el archivo y devuelve el original si ya lo habíamos visto.

        Los archivos vacíos no se consideran duplicados entre sí: son idénticos
        por definición y casi siempre son marcadores intencionados.
        """
        if file.size == 0:
            return None

        bucket = self._by_size.setdefault(file.size, [])
        if not bucket:
            bucket.append((file.path, None))
            return None

        if is_cloud_placeholder(file.path):
            self.skipped_cloud.append(file.path)
            bucket.append((file.path, None))
            return None

        try:
            incoming = file_digest(file.path)
        except OSError as exc:
            logger.warning("No se pudo hashear %s: %s", file.path, exc)
            bucket.append((file.path, None))
            return None

        for index, (path, known) in enumerate(bucket):
            if known is None:
                if is_cloud_placeholder(path):
                    self.skipped_cloud.append(path)
                    continue
                try:
                    known = file_digest(path)
                except OSError as exc:
                    logger.warning("No se pudo hashear %s: %s", path, exc)
                    continue
                bucket[index] = (path, known)
            if known == incoming:
                return path

        bucket.append((file.path, incoming))
        return None

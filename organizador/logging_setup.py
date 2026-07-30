"""Configuración del logging con la biblioteca estándar.

El proyecto usaba `loguru`; se cambió a `logging` para que el organizador no
necesite instalar nada. En un equipo donde `pip` está detrás de un proxy que
rompe TLS, "no requiere instalación" es la diferencia entre que la herramienta
funcione y que no.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_CONSOLE_FORMAT = "%(message)s"
_FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configured = False


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    *,
    verbose: bool = False,
    force: bool = False,
) -> None:
    """Configura el logging una sola vez por proceso.

    Llamarlo dos veces no duplica las líneas del log, que es lo que pasaba antes
    al construir varios gestores de configuración.
    """
    global _configured
    if _configured and not force:
        return

    resolved = logging.DEBUG if verbose else _parse_level(level)
    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
    root.setLevel(min(resolved, logging.INFO))

    console = logging.StreamHandler(stream=sys.stderr)
    console.setLevel(resolved)
    console.setFormatter(logging.Formatter(_CONSOLE_FORMAT))
    root.addHandler(console)

    if log_file is not None:
        try:
            log_file = Path(log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(_FILE_FORMAT))
            root.addHandler(file_handler)
        except OSError as exc:
            root.warning("No se pudo escribir el log en %s: %s", log_file, exc)

    _configured = True


def _parse_level(level: str) -> int:
    resolved = logging.getLevelName(str(level).upper())
    return resolved if isinstance(resolved, int) else logging.INFO

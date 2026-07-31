"""Aplicación de un plan al disco.

Es el único módulo que escribe. Cada movimiento se aísla: si uno falla, se
anota y se sigue con el resto, en vez de abandonar la carpeta a medio ordenar.
"""

from __future__ import annotations

import logging
import os
import shutil
import stat
import sys
from pathlib import Path

from .models import ExecutionResult, MoveReason, OrganizePlan, PlannedMove
from .paths import MAX_PATH_LENGTH, is_too_long

logger = logging.getLogger(__name__)


class PlanExecutor:
    """Ejecuta los movimientos de un `OrganizePlan`."""

    def __init__(self, *, dry_run: bool = False) -> None:
        self._dry_run = dry_run

    def execute(self, plan: OrganizePlan) -> ExecutionResult:
        result = ExecutionResult(dry_run=self._dry_run)
        for move in plan.moves:
            try:
                self._apply(move)
            except OSError as exc:
                logger.error("No se pudo mover %s: %s", move.source, exc)
                result.errors.append(f"{move.source.name}: {exc}")
                continue
            if move.reason is MoveReason.DUPLICATE:
                result.duplicates += 1
            else:
                result.moved += 1
        return result

    def _apply(self, move: PlannedMove) -> None:
        prefix = "[simulación] " if self._dry_run else ""
        logger.info("%s%s → %s/", prefix, move.source.name, move.destination.parent.name)
        if self._dry_run:
            return

        if not move.source.exists():
            raise FileNotFoundError(f"el archivo ya no existe ({move.source})")
        # Sólo estorba si el destino es MÁS largo que el origen. Si el origen ya
        # existe con esa longitud, el sistema la tolera, y al deshacer una
        # organización el destino siempre es más corto: rechazarlo dejaba
        # archivos atrapados en la carpeta que se intentaba vaciar.
        if is_too_long(move.destination) and len(str(move.destination)) > len(str(move.source)):
            raise OSError(
                f"la ruta destino supera {MAX_PATH_LENGTH} caracteres "
                f"({len(str(move.destination))})"
            )

        move.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(move.source), str(move.destination))


def remove_tree(path: Path) -> bool:
    """Borra un árbol de carpetas. Devuelve False si queda algo.

    `shutil.rmtree` se atasca en Windows con los archivos de sólo lectura, que
    es justo lo que hay dentro de `.git/objects` y de muchas dependencias. Aquí
    se les quita el atributo y se reintenta, y si algo sigue bloqueado (un
    proceso con el archivo abierto) se avisa en vez de dar el borrado por hecho.
    """

    def handle(func, target, _exc) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError as exc:
            logger.warning("No se pudo borrar %s: %s", target, exc)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=handle)
    else:
        shutil.rmtree(path, onerror=handle)
    return not Path(path).exists()


def move_directory(source: Path, destination: Path, *, dry_run: bool = False) -> bool:
    """Mueve una carpeta completa. Usado al reubicar proyectos.

    Devuelve True si el origen quedó vacío, y False si la copia está completa
    pero el origen no se pudo borrar del todo. Distinguir los dos casos importa:
    tratar una copia correcta como un fallo llevaría al usuario a reintentar y a
    pensar que sus archivos no llegaron, cuando sí lo hicieron.
    """
    if dry_run:
        logger.info("[simulación] carpeta %s → %s", source.name, destination)
        return True

    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        # En el mismo volumen esto es instantáneo, sin copiar ni un byte.
        os.rename(source, destination)
        return True
    except OSError as exc:
        logger.debug("No se pudo renombrar (%s); se copia y se borra el origen.", exc)

    shutil.copytree(source, destination, symlinks=True)
    return remove_tree(source)

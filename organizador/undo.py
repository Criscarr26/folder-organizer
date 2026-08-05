"""Deshacer una organización: devolver los archivos a su carpeta madre.

Existe porque la versión 1.0 recorría el árbol entero y creaba carpetas de
categoría dentro de cualquier carpeta que tocara. En un paquete de iconos, por
ejemplo, `32x32/apps/*.png` acababa en `32x32/apps/Imágenes/*.png`, y ahí ya no
lo encuentra ningún programa que use el tema.

Reutiliza `OrganizePlan` y `PlanExecutor`, así que hereda las mismas garantías
que `organize`: la simulación construye el plan real, y ningún archivo se
sobrescribe nunca.
"""

from __future__ import annotations

import logging
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .duplicates import QUARANTINE_FOLDER
from .models import FileInfo, MoveReason, OrganizePlan, PlannedMove, SkippedFile
from .paths import unique_path
from .rules import Ruleset
from .scanner import DEFAULT_EXCLUDED_DIRS, ScanFilter

logger = logging.getLogger(__name__)


#: Carpetas que creaba la versión 1.0 y que la 2.0 ya no usa. Deshacer una
#: organización de este programa incluye deshacer las que hizo de joven: si no
#: estuvieran aquí, un `Archivos/` de 2026 se quedaría sin tocar para siempre.
LEGACY_FOLDERS: frozenset[str] = frozenset({"Archivos", "Ejecutables"})


def undo_scan_filter(
    extra_dirs: set[str] | None = None,
    excluded_paths: set | None = None,
) -> ScanFilter:
    """Filtro para deshacer: hay que poder *entrar* en las carpetas de categoría.

    El filtro de `organize` las excluye para ser idempotente; aquí son
    justamente lo que buscamos, incluida la cuarentena de duplicados.

    Tampoco se protege ningún archivo por nombre ni por ser oculto. La regla de
    deshacer es "lo que está dentro de una carpeta de categoría lo puso ahí el
    organizador, así que vuelve": la versión 1.0 no respetaba los ocultos, y si
    los saltáramos aquí se quedarían dentro para siempre un `.env.example` o el
    `.cs` de un `obj/Debug`.
    """
    # Se construye el filtro a mano en vez de con `ScanFilter.build`, porque
    # build vuelve a añadir las exclusiones por defecto y desharía la resta.
    excluded = (set(DEFAULT_EXCLUDED_DIRS) - {"_duplicados"}) | set(extra_dirs or ())
    return ScanFilter(
        excluded_dirs=frozenset(excluded),
        excluded_paths=frozenset(excluded_paths or ()),
        protected_filenames=frozenset(),
        protected_suffixes=frozenset(),
        skip_hidden=False,
    )


@dataclass(frozen=True)
class UndoCandidate:
    """Una carpeta de categoría que se puede vaciar hacia su madre."""

    folder: Path
    files: tuple[FileInfo, ...]
    sole_child: bool
    has_subfolders: bool

    @property
    def parent(self) -> Path:
        return self.folder.parent

    @property
    def confidence(self) -> str:
        """`sole_child` es la firma fuerte: la organizó el organizador.

        Si la carpeta de categoría es lo único que hay en su madre, es que se
        llevó todo el contenido. Una carpeta creada a mano (un
        `Resources/Imágenes` de un proyecto, por ejemplo) casi siempre convive
        con hermanas.
        """
        if self.sole_child and not self.has_subfolders:
            return "alta"
        if self.sole_child or not self.has_subfolders:
            return "media"
        return "baja"


class UndoPlanner:
    """Busca carpetas de categoría y planifica devolver su contenido."""

    def __init__(
        self,
        ruleset: Ruleset,
        scan_filter: ScanFilter | None = None,
        *,
        only_sole_child: bool = False,
    ) -> None:
        self._folders = {name.casefold() for name in ruleset.folders}
        self._folders.add(QUARANTINE_FOLDER.casefold())
        self._folders.update(name.casefold() for name in LEGACY_FOLDERS)
        self._filter = scan_filter or undo_scan_filter()
        self._only_sole_child = only_sole_child

    def find(self, root: Path) -> list[UndoCandidate]:
        root = Path(root).resolve()
        candidates: list[UndoCandidate] = []

        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            current = Path(dirpath)
            dirnames[:] = [d for d in dirnames if self._filter.allows_dir(current / d)]
            if current == root or current.name.casefold() not in self._folders:
                continue

            files = self._readable_files(current, filenames)
            if not files:
                continue

            try:
                sole_child = len(os.listdir(current.parent)) == 1
            except OSError:
                sole_child = False

            candidates.append(
                UndoCandidate(
                    folder=current,
                    files=tuple(files),
                    sole_child=sole_child,
                    has_subfolders=bool(dirnames),
                )
            )

        # De más profunda a menos: si hubiera categorías anidadas, la de dentro
        # se resuelve antes de que se mueva la de fuera.
        candidates.sort(key=lambda c: len(c.folder.parts), reverse=True)
        return candidates

    def plan(self, root: Path) -> OrganizePlan:
        root = Path(root).resolve()
        plan = OrganizePlan(root=root)
        claimed: set[Path] = set()

        for candidate in self.find(root):
            if self._only_sole_child and not candidate.sole_child:
                for file in candidate.files:
                    plan.skipped.append(
                        SkippedFile(file, "la carpeta convive con otras: puede ser tuya")
                    )
                continue

            for file in candidate.files:
                destination = unique_path(candidate.parent / file.name, claimed)
                claimed.add(destination)
                plan.moves.append(
                    PlannedMove(
                        source=file.path,
                        destination=destination,
                        category=candidate.folder.name,
                        reason=MoveReason.UNDO,
                    )
                )

        logger.info(
            "Deshacer: %d archivo(s) volverían a su carpeta madre, %d sin tocar.",
            len(plan.moves), len(plan.skipped),
        )
        return plan

    def _readable_files(self, directory: Path, names: list[str]) -> list[FileInfo]:
        files = []
        for name in sorted(names):
            path = directory / name
            if not self._filter.allows_file(path):
                continue
            try:
                files.append(FileInfo.from_path(path))
            except OSError as exc:
                logger.warning("No se pudo leer %s: %s", path, exc)
        return files


def remove_empty_folders(plan: OrganizePlan, *, dry_run: bool = False) -> list[Path]:
    """Borra las carpetas de categoría que quedaron vacías tras deshacer.

    Usa `rmdir`, que falla si queda algo dentro: no puede llevarse por delante
    un archivo que no se hubiera movido.

    Antes se quita el atributo de sólo lectura. En Windows las carpetas dentro
    de OneDrive lo llevan puesto muy a menudo, y `rmdir` responde a secas con
    "Access is denied" aunque la carpeta esté vacía.
    """
    folders = {move.source.parent for move in plan.moves}
    removed: list[Path] = []
    for folder in sorted(folders, key=lambda p: len(p.parts), reverse=True):
        if dry_run:
            removed.append(folder)
            continue
        try:
            folder.rmdir()
        except PermissionError:
            try:
                os.chmod(folder, stat.S_IWRITE)
                folder.rmdir()
            except OSError as exc:
                logger.debug("No se pudo borrar %s: %s", folder, exc)
                continue
        except OSError as exc:
            logger.debug("La carpeta %s no quedó vacía: %s", folder, exc)
            continue
        removed.append(folder)
    return removed

"""Construcción del plan de organización.

El planificador decide; no mueve nada. Toda la lógica que antes estaba mezclada
con `shutil.move` vive aquí, donde se puede probar y donde `--dry-run` no puede
divergir de la ejecución real, porque las dos usan este mismo plan.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .classifier import FileClassifier
from .duplicates import QUARANTINE_FOLDER, DuplicateIndex, DuplicatePolicy
from .models import FileInfo, MoveReason, OrganizePlan, PlannedMove, SkippedFile
from .paths import unique_path
from .scanner import FileScanner, ScanMode

logger = logging.getLogger(__name__)


class OrganizePlanner:
    """Convierte una carpeta en una lista de movimientos propuestos."""

    def __init__(
        self,
        classifier: FileClassifier,
        scanner: FileScanner,
        *,
        duplicate_policy: DuplicatePolicy = DuplicatePolicy.QUARANTINE,
        quarantine_folder: str = QUARANTINE_FOLDER,
    ) -> None:
        self._classifier = classifier
        self._scanner = scanner
        self._policy = duplicate_policy
        self._quarantine_folder = quarantine_folder

    def plan(self, root: Path, mode: ScanMode = ScanMode.LOOSE) -> OrganizePlan:
        root = Path(root).resolve()
        plan = OrganizePlan(root=root)
        index = DuplicateIndex()
        claimed: set[Path] = set()

        for anchor, files in self._scanner.groups(root, mode):
            self._plan_group(anchor, files, plan, index, claimed)

        if index.skipped_cloud:
            logger.info(
                "%d archivo(s) sólo están en la nube: se moverán, pero no se "
                "comprobó si eran duplicados (habría que descargarlos).",
                len(index.skipped_cloud),
            )
        logger.info(
            "Plan listo: %d movimiento(s), %d sin cambios.",
            len(plan.moves), len(plan.skipped),
        )
        return plan

    def _plan_group(
        self,
        anchor: Path,
        files: list[FileInfo],
        plan: OrganizePlan,
        index: DuplicateIndex,
        claimed: set[Path],
    ) -> None:
        for file in files:
            # Clasificar va primero. Un archivo que las reglas no cubren no se
            # toca en absoluto, y eso incluye no mandarlo a la cuarentena de
            # duplicados: al ordenar apuntes dentro de una carpeta que además
            # contiene un programa instalado, sus .dll y sus iconos repetidos
            # son copias legítimas, y moverlos rompe la instalación.
            category = self._classifier.classify(file)
            if category is None:
                plan.skipped.append(SkippedFile(file, "su extensión no está en las reglas"))
                continue

            duplicate_of = self._duplicate_of(file, index)
            if duplicate_of is not None:
                self._plan_duplicate(anchor, file, duplicate_of, plan, claimed)
                continue

            target_folder = anchor / category.folder
            if file.path.parent == target_folder:
                plan.skipped.append(SkippedFile(file, "ya está en su carpeta"))
                continue

            destination = unique_path(target_folder / file.name, claimed)
            claimed.add(destination)
            plan.moves.append(
                PlannedMove(
                    source=file.path,
                    destination=destination,
                    category=category.folder,
                    reason=MoveReason.CLASSIFIED,
                )
            )

    def _plan_duplicate(
        self,
        anchor: Path,
        file: FileInfo,
        duplicate_of: Path,
        plan: OrganizePlan,
        claimed: set[Path],
    ) -> None:
        if self._policy is DuplicatePolicy.REPORT:
            plan.skipped.append(SkippedFile(file, f"duplicado de {duplicate_of.name}"))
            return

        destination = unique_path(anchor / self._quarantine_folder / file.name, claimed)
        claimed.add(destination)
        plan.moves.append(
            PlannedMove(
                source=file.path,
                destination=destination,
                category=self._quarantine_folder,
                reason=MoveReason.DUPLICATE,
                duplicate_of=duplicate_of,
            )
        )

    def _duplicate_of(self, file: FileInfo, index: DuplicateIndex) -> Path | None:
        if self._policy is DuplicatePolicy.IGNORE:
            return None
        return index.find_duplicate(file)

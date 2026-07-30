"""Presentación de resultados: consola e informe en Markdown.

Al estar separado del planificador, cambiar cómo se muestra algo no puede
cambiar lo que se hace con los archivos.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from .models import Category, ExecutionResult, FileInfo, MoveReason, OrganizePlan
from .paths import relative_to_root
from .projects import MoveStatus, ProjectCandidate, ProjectMoveResult

_RULE = "=" * 60


def human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def plan_lines(plan: OrganizePlan, *, limit: int = 6) -> list[str]:
    """Resumen del plan: qué carpeta recibe qué, con unos ejemplos."""
    lines = [f"Plan para: {plan.root}", _RULE]
    if not plan.moves:
        lines.append("No hay nada que mover.")
    for folder, moves in plan.by_category().items():
        lines.append(f"{folder}/  ({len(moves)} archivo(s))")
        for move in moves[:limit]:
            if move.reason is MoveReason.DUPLICATE and move.duplicate_of is not None:
                original = relative_to_root(move.duplicate_of, plan.root)
                lines.append(f"    - {move.source.name}   (copia de {original})")
            else:
                lines.append(f"    - {move.source.name}")
        if len(moves) > limit:
            lines.append(f"    ... y {len(moves) - limit} más")

    duplicates = plan.duplicate_moves
    lines.append(_RULE)
    lines.append(
        f"{plan.scanned} archivo(s) revisados · {len(plan.moves)} a mover "
        f"({len(duplicates)} duplicado(s)) · {len(plan.skipped)} sin cambios"
    )
    return lines


def execution_lines(result: ExecutionResult) -> list[str]:
    verb = "Se moverían" if result.dry_run else "Movidos"
    lines = [
        _RULE,
        "SIMULACIÓN — no se ha tocado ningún archivo" if result.dry_run else "Resultado",
        f"  {verb}: {result.moved}",
        f"  Duplicados a cuarentena: {result.duplicates}",
        f"  Errores: {result.failed}",
    ]
    lines.extend(f"    ! {error}" for error in result.errors[:10])
    if result.failed > 10:
        lines.append(f"    ... y {result.failed - 10} errores más")
    lines.append(_RULE)
    return lines


def analysis_lines(
    grouped: dict[Category, list[FileInfo]], root: Path, *, limit: int = 5
) -> list[str]:
    lines = [f"Análisis de: {root}", _RULE]
    total = sum(len(files) for files in grouped.values())
    for category, files in grouped.items():
        size = human_size(sum(file.size for file in files))
        lines.append(f"{category.folder}  ({len(files)} archivo(s), {size})")
        for file in files[:limit]:
            lines.append(f"    - {file.name}  ({human_size(file.size)})")
        if len(files) > limit:
            lines.append(f"    ... y {len(files) - limit} más")
    lines.append(_RULE)
    lines.append(f"Total: {total} archivo(s) en {len(grouped)} categoría(s)")
    return lines


def project_lines(candidates: Iterable[ProjectCandidate]) -> list[str]:
    candidates = list(candidates)
    lines = [f"Proyectos detectados: {len(candidates)}", _RULE]
    for candidate in sorted(candidates, key=lambda c: str(c.path).lower()):
        lines.append(f"[{candidate.confidence:>5}] {candidate.path}")
        lines.append(f"         {candidate.describe()}")
    if not candidates:
        lines.append("Ninguno.")
    return lines


def project_move_lines(results: Iterable[ProjectMoveResult], *, dry_run: bool) -> list[str]:
    results = list(results)
    lines = [_RULE, "SIMULACIÓN — no se ha movido nada" if dry_run else "Resultado", ""]
    for result in results:
        mark = "OK " if result.status.is_success else "-- "
        detail = f"  ({result.detail})" if result.detail else ""
        lines.append(f"  {mark}{result.candidate.path.name}: {result.status.value}{detail}")

    moved = sum(1 for r in results if r.status.is_success)
    lines.extend(["", f"  {moved} de {len(results)} proyecto(s) en el destino.", _RULE])
    return lines


def write_markdown_report(path: Path, plan: OrganizePlan, result: ExecutionResult) -> None:
    """Guarda el detalle completo, que en consola se recorta."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Informe de organización",
        "",
        f"- Carpeta: `{plan.root}`",
        f"- Fecha: {datetime.now():%Y-%m-%d %H:%M}",
        f"- Modo: {'simulación' if result.dry_run else 'ejecución real'}",
        f"- Archivos revisados: {plan.scanned}",
        f"- Movimientos: {len(plan.moves)} ({result.moved} aplicados, {result.failed} con error)",
        f"- Duplicados en cuarentena: {result.duplicates}",
        "",
    ]

    for folder, moves in plan.by_category().items():
        lines.extend([f"## {folder} ({len(moves)})", ""])
        for move in moves:
            source = relative_to_root(move.source, plan.root)
            if move.reason is MoveReason.DUPLICATE and move.duplicate_of is not None:
                original = relative_to_root(move.duplicate_of, plan.root)
                lines.append(f"- `{source}` — copia de `{original}`")
            else:
                lines.append(f"- `{source}`")
        lines.append("")

    if plan.skipped:
        lines.extend([f"## Sin cambios ({len(plan.skipped)})", ""])
        lines.extend(
            f"- `{relative_to_root(item.file.path, plan.root)}` — {item.reason}"
            for item in plan.skipped
        )
        lines.append("")

    if result.errors:
        lines.extend([f"## Errores ({len(result.errors)})", ""])
        lines.extend(f"- {error}" for error in result.errors)
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")

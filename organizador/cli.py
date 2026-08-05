"""Interfaz de línea de comandos.

Los comandos sólo ensamblan piezas e imprimen: la lógica está en los módulos de
dominio. Se usa `argparse` de la biblioteca estándar para que el organizador
funcione con cualquier Python 3.9+ sin instalar dependencias.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import reporting
from .classifier import FileClassifier
from .duplicates import DuplicatePolicy
from .executor import PlanExecutor
from .logging_setup import setup_logging
from .planner import OrganizePlanner
from .projects import ProjectCandidate, ProjectDetector, ProjectMover
from .scanner import FileScanner, ScanFilter, ScanMode
from .settings import Settings, load_dotenv, load_ruleset, write_default_config
from .undo import UndoPlanner, remove_empty_folders, undo_scan_filter

EXIT_OK = 0
EXIT_ERROR = 1


# --------------------------------------------------------------------------- #
# Construcción del parser
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="organizador",
        description="Organiza archivos por tipo y reúne tus proyectos en una carpeta.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    organize = subparsers.add_parser(
        "organize", help="Mueve los archivos a subcarpetas según su tipo."
    )
    _add_shared(organize)
    organize.add_argument("--path", type=Path, default=Path("."), help="Carpeta a ordenar.")
    organize.add_argument(
        "--mode", choices=[mode.value for mode in ScanMode], default=ScanMode.LOOSE.value,
        help="'loose': sólo los archivos sueltos de la raíz (por defecto). "
             "'per-folder': recorre el árbol y ordena cada carpeta por dentro.",
    )
    organize.add_argument(
        "--duplicates", choices=[policy.value for policy in DuplicatePolicy],
        default=None,
        help="Qué hacer con los archivos repetidos. 'quarantine' (por defecto) los "
             "mueve a _Duplicados; nunca se borra nada.",
    )
    organize.add_argument(
        "--solo-clasificados", action="store_true",
        help="Deja donde están los archivos cuya extensión no aparezca en las reglas, "
             "en vez de mandarlos a Otros/. Útil en carpetas donde conviven documentos "
             "con cosas que no deben moverse (iconos, dependencias, código).",
    )
    organize.add_argument("--report", type=Path, default=None, help="Guarda un informe Markdown.")
    _add_apply_flags(organize)
    organize.set_defaults(handler=cmd_organize)

    analyze = subparsers.add_parser(
        "analyze", help="Muestra cómo quedarían los archivos, sin mover nada."
    )
    _add_shared(analyze)
    analyze.add_argument("--path", type=Path, default=Path("."), help="Carpeta a analizar.")
    analyze.add_argument(
        "--mode", choices=[mode.value for mode in ScanMode], default=ScanMode.LOOSE.value
    )
    analyze.add_argument("--limit", type=int, default=5, help="Ejemplos por categoría.")
    analyze.set_defaults(handler=cmd_analyze)

    find_projects = subparsers.add_parser(
        "find-projects", help="Lista las carpetas que parecen proyectos de código."
    )
    _add_shared(find_projects)
    find_projects.add_argument(
        "--path", type=Path, action="append", default=None,
        help="Carpeta donde buscar. Se puede repetir.",
    )
    find_projects.set_defaults(handler=cmd_find_projects)

    move_projects = subparsers.add_parser(
        "move-projects", help="Mueve proyectos a una carpeta única."
    )
    _add_shared(move_projects)
    move_projects.add_argument(
        "--path", type=Path, action="append", default=None,
        help="Carpeta donde buscar proyectos. Se puede repetir.",
    )
    move_projects.add_argument(
        "--project", type=Path, action="append", default=None,
        help="Mueve esta carpeta concreta sin detectar nada. Se puede repetir.",
    )
    move_projects.add_argument(
        "--destination", type=Path, default=None,
        help="Carpeta destino (o la variable de entorno PROJECTS_DESTINATION).",
    )
    _add_apply_flags(move_projects)
    move_projects.set_defaults(handler=cmd_move_projects)

    undo = subparsers.add_parser(
        "undo",
        help="Deshace una organización: devuelve los archivos a su carpeta madre.",
    )
    _add_shared(undo)
    undo.add_argument("--path", type=Path, default=Path("."), help="Carpeta a deshacer.")
    undo.add_argument(
        "--solo-seguras", action="store_true",
        help="Sólo deshace las carpetas de categoría que son el único contenido de "
             "su carpeta madre, que es la firma clara de una organización previa.",
    )
    undo.add_argument("--report", type=Path, default=None, help="Guarda un informe Markdown.")
    _add_apply_flags(undo)
    undo.set_defaults(handler=cmd_undo)

    init_config = subparsers.add_parser(
        "init-config", help="Escribe un archivo de reglas que puedas editar."
    )
    init_config.add_argument("--config", type=Path, default=Path("config/rules.json"))
    init_config.add_argument("--force", action="store_true", help="Sobrescribe si ya existe.")
    init_config.set_defaults(handler=cmd_init_config)

    return parser


def _add_shared(sub: argparse.ArgumentParser) -> None:
    sub.add_argument("--config", type=Path, default=None, help="Archivo JSON de reglas.")
    sub.add_argument(
        "--exclude", action="append", default=[], metavar="NOMBRE",
        help="Nombre de carpeta que nunca se toca. Se puede repetir.",
    )
    sub.add_argument(
        "--exclude-path", action="append", default=[], metavar="RUTA", type=Path,
        help="Carpeta concreta que nunca se toca, por su ruta. Se puede repetir. "
             "Úsalo cuando el nombre no sirve para distinguirla: excluir 'dia' por "
             "nombre se llevaría por delante una asignatura llamada 'DIA'.",
    )
    sub.add_argument("--verbose", action="store_true", help="Muestra el detalle de cada paso.")
    sub.add_argument("--log-file", type=Path, default=None, help="Archivo donde guardar el log.")


def _add_apply_flags(sub: argparse.ArgumentParser) -> None:
    sub.add_argument(
        "--dry-run", action="store_true", help="Simula: enseña el plan y no toca nada."
    )
    sub.add_argument(
        "--yes", action="store_true", help="No pedir confirmación antes de aplicar."
    )


# --------------------------------------------------------------------------- #
# Comandos
# --------------------------------------------------------------------------- #

def cmd_organize(args: argparse.Namespace, settings: Settings) -> int:
    policy = (
        DuplicatePolicy(args.duplicates) if args.duplicates else settings.duplicate_policy
    )
    ruleset = load_ruleset(
        args.config or settings.config_file, con_comodin=not args.solo_clasificados
    )
    scanner = FileScanner(_scan_filter(args, ruleset))
    planner = OrganizePlanner(
        FileClassifier(ruleset), scanner, duplicate_policy=policy
    )

    plan = planner.plan(args.path, ScanMode(args.mode))
    _emit(reporting.plan_lines(plan))

    if not plan.moves:
        return EXIT_OK
    if not args.dry_run and not _confirm(f"¿Mover {len(plan.moves)} archivo(s)?", args.yes):
        print("Cancelado. No se ha movido nada.")
        return EXIT_OK

    result = PlanExecutor(dry_run=args.dry_run).execute(plan)
    _emit(reporting.execution_lines(result))

    if args.report:
        reporting.write_markdown_report(args.report, plan, result)
        print(f"Informe guardado en: {args.report}")

    return EXIT_ERROR if result.errors else EXIT_OK


def cmd_analyze(args: argparse.Namespace, settings: Settings) -> int:
    ruleset = load_ruleset(args.config or settings.config_file)
    scanner = FileScanner(_scan_filter(args, ruleset))
    classifier = FileClassifier(ruleset)

    files = [
        file
        for _, group in scanner.groups(Path(args.path).resolve(), ScanMode(args.mode))
        for file in group
    ]
    _emit(
        reporting.analysis_lines(
            classifier.summarize(files), Path(args.path).resolve(), limit=args.limit
        )
    )
    return EXIT_OK


def cmd_find_projects(args: argparse.Namespace, settings: Settings) -> int:
    detector = ProjectDetector(_scan_filter(args, None))
    candidates: list[ProjectCandidate] = []
    for root in args.path or [Path(".")]:
        candidates.extend(detector.detect(root))
    _emit(reporting.project_lines(candidates))
    return EXIT_OK


def cmd_move_projects(args: argparse.Namespace, settings: Settings) -> int:
    destination = args.destination or settings.projects_destination
    if destination is None:
        print(
            "Falta el destino: usa --destination o la variable PROJECTS_DESTINATION.",
            file=sys.stderr,
        )
        return EXIT_ERROR

    detector = ProjectDetector(_scan_filter(args, None))
    candidates: list[ProjectCandidate] = []

    for explicit in args.project or []:
        candidate = detector.inspect(explicit)
        if candidate is None:
            # Lo ha pedido el usuario por su nombre: se respeta aunque no tenga
            # marcadores, pero se avisa de que no parece un proyecto.
            if not Path(explicit).is_dir():
                print(f"No existe la carpeta: {explicit}", file=sys.stderr)
                return EXIT_ERROR
            print(f"Aviso: {explicit} no tiene marcadores de proyecto; se moverá igual.")
            candidate = ProjectCandidate(Path(explicit), markers=(), source_files=0)
        candidates.append(candidate)

    for root in args.path or []:
        candidates.extend(detector.detect(root))

    if not candidates:
        print("No se han encontrado proyectos que mover.")
        return EXIT_OK

    _emit(reporting.project_lines(candidates))
    print(f"\nDestino: {destination}")

    if not args.dry_run and not _confirm(
        f"¿Mover {len(candidates)} carpeta(s) de proyecto?", args.yes
    ):
        print("Cancelado. No se ha movido nada.")
        return EXIT_OK

    mover = ProjectMover(destination, dry_run=args.dry_run)
    results = mover.move_all(candidates)
    _emit(reporting.project_move_lines(results, dry_run=args.dry_run))
    return EXIT_OK


def cmd_undo(args: argparse.Namespace, settings: Settings) -> int:
    ruleset = load_ruleset(args.config or settings.config_file)
    planner = UndoPlanner(
        ruleset,
        undo_scan_filter(set(args.exclude or []), set(args.exclude_path or [])),
        only_sole_child=args.solo_seguras,
    )

    plan = planner.plan(args.path)
    _emit(reporting.undo_lines(plan))

    if not plan.moves:
        return EXIT_OK
    if not args.dry_run and not _confirm(
        f"¿Devolver {len(plan.moves)} archivo(s) a su carpeta madre?", args.yes
    ):
        print("Cancelado. No se ha movido nada.")
        return EXIT_OK

    result = PlanExecutor(dry_run=args.dry_run).execute(plan)
    removed = remove_empty_folders(plan, dry_run=args.dry_run)
    _emit(reporting.execution_lines(result))
    print(f"  Carpetas de categoría vaciadas: {len(removed)}")

    if args.report:
        reporting.write_markdown_report(args.report, plan, result)
        print(f"Informe guardado en: {args.report}")

    return EXIT_ERROR if result.errors else EXIT_OK


def cmd_init_config(args: argparse.Namespace, settings: Settings) -> int:
    created = write_default_config(args.config, overwrite=args.force)
    if not created:
        print(f"{args.config} ya existe. Usa --force para sobrescribirlo.", file=sys.stderr)
        return EXIT_ERROR
    print(f"Configuración creada: {args.config}")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# Ayudantes
# --------------------------------------------------------------------------- #

def _scan_filter(args: argparse.Namespace, ruleset=None) -> ScanFilter:
    """Exclusiones por defecto + las carpetas de categoría + las del usuario.

    Excluir las carpetas de categoría es lo que hace que ejecutar el comando dos
    veces sobre la misma carpeta sea inofensivo.
    """
    extra = set(args.exclude or [])
    if ruleset is not None:
        extra |= set(ruleset.folders)
    return ScanFilter.build(
        extra_dirs=extra, excluded_paths=set(getattr(args, "exclude_path", None) or [])
    )


def _confirm(question: str, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    if not sys.stdin or not sys.stdin.isatty():
        print(
            "Hay que confirmar para continuar, pero la entrada no es interactiva. "
            "Vuelve a ejecutarlo con --dry-run para revisar, o con --yes para aplicar.",
            file=sys.stderr,
        )
        return False
    answer = input(f"{question} [s/N] ").strip().lower()
    return answer in {"s", "si", "sí", "y", "yes"}


def _emit(lines: list[str]) -> None:
    print("\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    settings = Settings.from_env()
    args = build_parser().parse_args(argv)
    setup_logging(
        settings.log_level,
        getattr(args, "log_file", None) or settings.log_file,
        verbose=getattr(args, "verbose", False),
    )
    return args.handler(args, settings)


if __name__ == "__main__":
    raise SystemExit(main())

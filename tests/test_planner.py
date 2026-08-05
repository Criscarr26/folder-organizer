"""Pruebas del planificador y del executor: el corazón del organizador."""

from __future__ import annotations

import pytest

from organizador.classifier import FileClassifier
from organizador.duplicates import QUARANTINE_FOLDER, DuplicatePolicy
from organizador.executor import PlanExecutor
from organizador.models import MoveReason
from organizador.planner import OrganizePlanner
from organizador.rules import Ruleset
from organizador.scanner import FileScanner, ScanFilter, ScanMode

from .helpers import tree, write


def build_planner(policy: DuplicatePolicy = DuplicatePolicy.QUARANTINE) -> OrganizePlanner:
    ruleset = Ruleset.default()
    scan_filter = ScanFilter.build(extra_dirs=set(ruleset.folders))
    return OrganizePlanner(
        FileClassifier(ruleset), FileScanner(scan_filter), duplicate_policy=policy
    )


def run(root, mode=ScanMode.LOOSE, policy=DuplicatePolicy.QUARANTINE, dry_run=False):
    planner = build_planner(policy)
    plan = planner.plan(root, mode)
    result = PlanExecutor(dry_run=dry_run).execute(plan)
    return plan, result


# --------------------------------------------------------------------------- #
# Modo LOOSE
# --------------------------------------------------------------------------- #

def test_loose_mode_sorts_root_files_into_category_folders(tmp_path):
    write(tmp_path / "foto.jpg")
    write(tmp_path / "informe.docx")
    write(tmp_path / "datos.xlsx")

    _, result = run(tmp_path)

    assert result.moved == 3
    assert tree(tmp_path) == {
        "Imágenes/foto.jpg",
        "Documentos/informe.docx",
        "Hojas de cálculo/datos.xlsx",
    }


def test_loose_mode_never_descends_into_subfolders(tmp_path):
    # Este era el fallo más grave de la versión anterior: clasificaba de forma
    # recursiva y luego movía todo a la raíz, aplanando el árbol del usuario.
    write(tmp_path / "suelto.pdf")
    write(tmp_path / "Universidad" / "Matemáticas" / "examen.pdf")

    _, result = run(tmp_path)

    assert result.moved == 1
    assert tree(tmp_path) == {
        "Documentos/suelto.pdf",
        "Universidad/Matemáticas/examen.pdf",
    }


def test_category_folder_can_be_a_nested_path(tmp_path):
    # Necesario cuando el nombre de una categoría choca con una carpeta que ya
    # existe: en la raíz de OneDrive, `Documentos` es la carpeta real del
    # usuario, así que las categorías se agrupan bajo un contenedor propio.
    write(tmp_path / "Documentos" / "no_me_toques.txt", "intacto")
    write(tmp_path / "informe.docx")

    ruleset = Ruleset.from_mapping(
        {"docs": {"folder": "Archivos ordenados/Documentos", "extensions": [".docx"]}}
    )
    planner = OrganizePlanner(
        FileClassifier(ruleset), FileScanner(ScanFilter.build(extra_dirs=set(ruleset.folders)))
    )
    result = PlanExecutor().execute(planner.plan(tmp_path, ScanMode.LOOSE))

    assert result.moved == 1
    assert tree(tmp_path) == {
        "Documentos/no_me_toques.txt",
        "Archivos ordenados/Documentos/informe.docx",
    }


def test_unknown_extension_goes_to_otros(tmp_path):
    write(tmp_path / "cosa.qwerty")
    run(tmp_path)
    assert tree(tmp_path) == {"Otros/cosa.qwerty"}


def test_running_twice_changes_nothing_the_second_time(tmp_path):
    write(tmp_path / "foto.jpg")
    run(tmp_path)
    snapshot = tree(tmp_path)

    plan, result = run(tmp_path)

    assert plan.moves == []
    assert result.moved == 0
    assert tree(tmp_path) == snapshot


def test_name_conflict_gets_a_suffix(tmp_path):
    write(tmp_path / "Documentos" / "informe.pdf", "el que ya estaba")
    write(tmp_path / "informe.pdf", "el nuevo")

    run(tmp_path)

    assert tree(tmp_path) == {"Documentos/informe.pdf", "Documentos/informe_1.pdf"}
    assert (tmp_path / "Documentos" / "informe.pdf").read_text(encoding="utf-8") == (
        "el que ya estaba"
    )


def test_conflict_resolution_cannot_assign_the_same_destination_twice(tmp_path):
    # `informe.pdf` esquiva al que ya está en Documentos pasando a `informe_1.pdf`,
    # que es justo el nombre que quiere el otro archivo. Si el plan no reservara
    # los destinos ya asignados, el segundo movimiento sobrescribiría al primero.
    write(tmp_path / "Documentos" / "informe.pdf", "el que ya estaba")
    write(tmp_path / "informe.pdf", "primero")
    write(tmp_path / "informe_1.pdf", "segundo")

    plan, result = run(tmp_path)

    destinations = [move.destination for move in plan.moves]
    assert len(set(destinations)) == len(destinations), "destinos duplicados en el plan"
    assert result.errors == []
    assert tree(tmp_path) == {
        "Documentos/informe.pdf",
        "Documentos/informe_1.pdf",
        "Documentos/informe_1_1.pdf",
    }
    # Los tres contenidos sobreviven: nada se ha sobrescrito.
    contents = {
        (tmp_path / "Documentos" / name).read_text(encoding="utf-8")
        for name in ("informe.pdf", "informe_1.pdf", "informe_1_1.pdf")
    }
    assert contents == {"el que ya estaba", "primero", "segundo"}


def test_files_in_different_folders_keep_their_own_anchor(tmp_path):
    write(tmp_path / "a" / "notas.txt", "primero")
    write(tmp_path / "b" / "notas.txt", "segundo")

    _, result = run(tmp_path, mode=ScanMode.PER_FOLDER)

    assert result.errors == []
    assert tree(tmp_path) == {"a/Documentos/notas.txt", "b/Documentos/notas.txt"}


# --------------------------------------------------------------------------- #
# Modo PER_FOLDER
# --------------------------------------------------------------------------- #

def test_per_folder_mode_keeps_files_inside_their_own_folder(tmp_path):
    write(tmp_path / "Cuatrimestre 1" / "Álgebra" / "tarea.docx")
    write(tmp_path / "Cuatrimestre 1" / "Álgebra" / "grafica.png")

    run(tmp_path, mode=ScanMode.PER_FOLDER)

    assert tree(tmp_path) == {
        "Cuatrimestre 1/Álgebra/Documentos/tarea.docx",
        "Cuatrimestre 1/Álgebra/Imágenes/grafica.png",
    }


def test_per_folder_mode_is_idempotent(tmp_path):
    write(tmp_path / "asignatura" / "tarea.docx")
    run(tmp_path, mode=ScanMode.PER_FOLDER)
    snapshot = tree(tmp_path)

    plan, _ = run(tmp_path, mode=ScanMode.PER_FOLDER)

    assert plan.moves == []
    assert tree(tmp_path) == snapshot


# --------------------------------------------------------------------------- #
# Duplicados
# --------------------------------------------------------------------------- #

def test_duplicates_go_to_quarantine_and_are_never_deleted(tmp_path):
    write(tmp_path / "original.txt", "mismo contenido")
    write(tmp_path / "copia.txt", "mismo contenido")

    plan, result = run(tmp_path)

    assert result.duplicates == 1
    quarantined = [
        item for item in tree(tmp_path) if item.startswith(f"{QUARANTINE_FOLDER}/")
    ]
    assert len(quarantined) == 1
    # Las dos copias siguen existiendo: nada se ha borrado.
    assert len(tree(tmp_path)) == 2
    assert plan.duplicate_moves[0].duplicate_of is not None


def test_same_size_different_content_is_not_a_duplicate(tmp_path):
    write(tmp_path / "uno.txt", "aaaa")
    write(tmp_path / "dos.txt", "bbbb")

    _, result = run(tmp_path)

    assert result.duplicates == 0
    assert tree(tmp_path) == {"Documentos/uno.txt", "Documentos/dos.txt"}


def test_empty_files_are_not_treated_as_duplicates(tmp_path):
    write(tmp_path / "vacio1.txt", "")
    write(tmp_path / "vacio2.txt", "")

    _, result = run(tmp_path)

    assert result.duplicates == 0
    assert tree(tmp_path) == {"Documentos/vacio1.txt", "Documentos/vacio2.txt"}


def test_report_policy_leaves_duplicates_in_place(tmp_path):
    write(tmp_path / "a.txt", "igual")
    write(tmp_path / "b.txt", "igual")

    plan, _ = run(tmp_path, policy=DuplicatePolicy.REPORT)

    assert len(plan.moves) == 1
    assert any("duplicado de" in item.reason for item in plan.skipped)


def test_ignore_policy_moves_both_copies(tmp_path):
    write(tmp_path / "a.txt", "igual")
    write(tmp_path / "b.txt", "igual")

    _, result = run(tmp_path, policy=DuplicatePolicy.IGNORE)

    assert result.duplicates == 0
    assert tree(tmp_path) == {"Documentos/a.txt", "Documentos/b.txt"}


# --------------------------------------------------------------------------- #
# Simulación
# --------------------------------------------------------------------------- #

def test_dry_run_plans_exactly_what_the_real_run_does(tmp_path):
    for name in ("a.jpg", "b.docx", "c.mp3", "d.zip", "e.qwerty"):
        write(tmp_path / name, name)
    write(tmp_path / "copia.jpg", "a.jpg")

    dry_plan, dry_result = run(tmp_path, dry_run=True)
    assert tree(tmp_path) == {
        "a.jpg", "b.docx", "c.mp3", "d.zip", "e.qwerty", "copia.jpg"
    }, "la simulación no debe tocar nada"

    real_plan, real_result = run(tmp_path)

    assert [(m.source, m.destination) for m in dry_plan.moves] == [
        (m.source, m.destination) for m in real_plan.moves
    ]
    assert (dry_result.moved, dry_result.duplicates) == (
        real_result.moved, real_result.duplicates
    )


# --------------------------------------------------------------------------- #
# Exclusiones
# --------------------------------------------------------------------------- #

def test_github_repository_folder_is_never_touched(tmp_path):
    write(tmp_path / "Github repository" / "proyecto" / "main.py")
    write(tmp_path / "suelto.pdf")

    run(tmp_path, mode=ScanMode.PER_FOLDER)

    assert "Github repository/proyecto/main.py" in tree(tmp_path)


@pytest.mark.parametrize("excluded", [".git", "node_modules", ".venv", "__pycache__"])
def test_tool_folders_are_skipped(tmp_path, excluded):
    write(tmp_path / excluded / "interno.txt")
    plan, _ = run(tmp_path, mode=ScanMode.PER_FOLDER)
    assert plan.moves == []


def test_protected_system_files_stay_where_they_are(tmp_path):
    write(tmp_path / "desktop.ini", "[.ShellClassInfo]")
    write(tmp_path / "atajo.lnk", "shortcut")
    write(tmp_path / "real.pdf")

    _, result = run(tmp_path)

    assert result.moved == 1
    assert "desktop.ini" in tree(tmp_path)
    assert "atajo.lnk" in tree(tmp_path)


def test_extra_exclusions_from_the_caller_are_respected(tmp_path):
    write(tmp_path / "Intocable" / "archivo.pdf")
    ruleset = Ruleset.default()
    scan_filter = ScanFilter.build(extra_dirs={"Intocable"} | set(ruleset.folders))
    planner = OrganizePlanner(FileClassifier(ruleset), FileScanner(scan_filter))

    plan = planner.plan(tmp_path, ScanMode.PER_FOLDER)

    assert plan.moves == []


# --------------------------------------------------------------------------- #
# Errores
# --------------------------------------------------------------------------- #

def test_a_missing_source_is_reported_and_the_rest_continues(tmp_path):
    write(tmp_path / "existe.pdf")
    write(tmp_path / "desaparece.pdf")

    planner = build_planner()
    plan = planner.plan(tmp_path, ScanMode.LOOSE)
    (tmp_path / "desaparece.pdf").unlink()

    result = PlanExecutor().execute(plan)

    assert result.moved == 1
    assert result.failed == 1
    assert "desaparece.pdf" in result.errors[0]


def test_plan_counts_add_up(tmp_path):
    write(tmp_path / "Documentos" / "ya_ordenado.pdf")
    write(tmp_path / "nuevo.pdf")

    plan, _ = run(tmp_path, dry_run=True)

    assert plan.scanned == len(plan.moves) + len(plan.skipped)
    assert len(plan.moves) == 1
    assert plan.moves[0].reason is MoveReason.CLASSIFIED


# --------------------------------------------------------------------------- #
# Reglas sin comodín: lo no listado no se toca
# --------------------------------------------------------------------------- #

def sin_comodin(mapping):
    ruleset = Ruleset.from_mapping(mapping, None)
    scan_filter = ScanFilter.build(extra_dirs=set(ruleset.folders))
    return OrganizePlanner(FileClassifier(ruleset), FileScanner(scan_filter))


def test_sin_comodin_lo_no_listado_se_queda_donde_esta(tmp_path):
    # El caso real: una carpeta de asignatura con los PDF de clase al lado de
    # un tema de iconos y el código de un proyecto. Mover los PNG a Imágenes/
    # rompe el tema, y los .py a Código/ rompen los imports.
    write(tmp_path / "tarea.pdf")
    write(tmp_path / "icono.png")
    write(tmp_path / "script.py")

    plan = sin_comodin(
        {"docs": {"folder": "Documentos", "extensions": [".pdf"]}}
    ).plan(tmp_path, ScanMode.LOOSE)
    PlanExecutor().execute(plan)

    assert tree(tmp_path) == {"Documentos/tarea.pdf", "icono.png", "script.py"}
    assert len(plan.skipped) == 2
    assert all("no está en las reglas" in s.reason for s in plan.skipped)


def test_con_comodin_sigue_mandando_lo_desconocido_a_otros(tmp_path):
    # El comportamiento por defecto no cambia.
    write(tmp_path / "tarea.pdf")
    write(tmp_path / "icono.png")

    ruleset = Ruleset.from_mapping({"docs": {"folder": "Documentos", "extensions": [".pdf"]}})
    scan_filter = ScanFilter.build(extra_dirs=set(ruleset.folders))
    planner = OrganizePlanner(FileClassifier(ruleset), FileScanner(scan_filter))
    PlanExecutor().execute(planner.plan(tmp_path, ScanMode.LOOSE))

    assert tree(tmp_path) == {"Documentos/tarea.pdf", "Otros/icono.png"}


def test_sin_comodin_no_deja_de_detectar_duplicados(tmp_path):
    write(tmp_path / "a.pdf", "mismo")
    write(tmp_path / "b.pdf", "mismo")

    plan = sin_comodin({"docs": {"folder": "Documentos", "extensions": [".pdf"]}}).plan(
        tmp_path, ScanMode.LOOSE
    )
    result = PlanExecutor().execute(plan)

    assert result.duplicates == 1


def test_sin_comodin_folders_no_incluye_otros(tmp_path):
    ruleset = Ruleset.from_mapping({"docs": {"folder": "Documentos", "extensions": [".pdf"]}}, None)
    assert ruleset.folders == frozenset({"Documentos"})
    assert ruleset.category_for(".png") is None


def test_sin_comodin_no_manda_a_cuarentena_lo_que_no_clasifica(tmp_path):
    # Encontrado ordenando una carpeta de apuntes que además contenía un
    # programa instalado: sus .dll repetidos son copias legítimas, y la
    # cuarentena de duplicados se los llevaba aunque las reglas no los cubrieran.
    write(tmp_path / "manual.pdf", "documento")
    write(tmp_path / "libA.dll", "binario idéntico")
    write(tmp_path / "libB.dll", "binario idéntico")

    plan = sin_comodin({"docs": {"folder": "Documentos", "extensions": [".pdf"]}}).plan(
        tmp_path, ScanMode.LOOSE
    )
    result = PlanExecutor().execute(plan)

    assert result.duplicates == 0
    assert tree(tmp_path) == {"Documentos/manual.pdf", "libA.dll", "libB.dll"}


def test_excluir_por_ruta_distingue_carpetas_del_mismo_nombre(tmp_path):
    # Excluir por nombre no vale cuando el nombre se repite: una instalación de
    # un programa en `dia/` y una asignatura en `Quinto/DIA` no se distinguen.
    write(tmp_path / "dia" / "manual.pdf", "programa instalado")
    write(tmp_path / "Quinto" / "DIA" / "apuntes.pdf", "asignatura")

    ruleset = Ruleset.default()
    scan_filter = ScanFilter.build(
        extra_dirs=set(ruleset.folders), excluded_paths={tmp_path / "dia"}
    )
    planner = OrganizePlanner(FileClassifier(ruleset), FileScanner(scan_filter))
    PlanExecutor().execute(planner.plan(tmp_path, ScanMode.PER_FOLDER))

    assert tree(tmp_path) == {"dia/manual.pdf", "Quinto/DIA/Documentos/apuntes.pdf"}

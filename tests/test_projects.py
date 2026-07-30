"""Pruebas de la detección y reubicación de proyectos."""

from __future__ import annotations

from organizador.projects import MoveStatus, ProjectDetector, ProjectMover
from organizador.scanner import ScanFilter

from .helpers import write


def detector() -> ProjectDetector:
    return ProjectDetector(ScanFilter.build())


# --------------------------------------------------------------------------- #
# Detección
# --------------------------------------------------------------------------- #

def test_marker_file_identifies_a_project(tmp_path):
    write(tmp_path / "mi-api" / "requirements.txt", "flask")
    write(tmp_path / "mi-api" / "main.py", "print('hola')")

    found = detector().detect(tmp_path)

    assert [candidate.path.name for candidate in found] == ["mi-api"]
    assert "Python" in found[0].markers
    assert found[0].confidence == "alta"


def test_git_repository_is_detected_even_without_other_markers(tmp_path):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    write(tmp_path / "repo" / "README.md", "# repo")

    found = detector().detect(tmp_path)

    assert found[0].is_git_repo
    assert found[0].confidence == "alta"


def test_a_folder_with_only_a_virtualenv_is_not_a_project(tmp_path):
    # `Computing-history` en el equipo real es exactamente esto: sólo un .venv
    # con miles de .py de terceros. Contar archivos sin filtrar lo marcaría como
    # el proyecto más grande del disco.
    write(tmp_path / "Computing-history" / ".venv" / "Lib" / "site-packages" / "numpy.py")
    write(tmp_path / "Computing-history" / ".venv" / "pyvenv.cfg")

    assert detector().detect(tmp_path) == []


def test_documents_only_folder_is_not_a_project(tmp_path):
    write(tmp_path / "Club de Guias" / "carpeta.docx")
    write(tmp_path / "Club de Guias" / "plan.pdf")

    assert detector().detect(tmp_path) == []


def test_nested_project_is_found_without_dragging_the_parent(tmp_path):
    # El caso de `GD/genetic-dash-og`: la carpeta contenedora tiene grabaciones y
    # hojas de cálculo que no son parte del juego.
    write(tmp_path / "GD" / "Benchmark.xlsx")
    write(tmp_path / "GD" / "reunion.mp4")
    write(tmp_path / "GD" / "genetic-dash-og" / "project.godot", "[application]")
    write(tmp_path / "GD" / "genetic-dash-og" / "player.gd", "extends Node")

    found = detector().detect(tmp_path)

    assert [candidate.path.name for candidate in found] == ["genetic-dash-og"]
    assert "Godot" in found[0].markers


def test_several_sibling_projects_are_kept_together_as_a_monorepo(tmp_path):
    # El caso de `LR_project`: mobile, website y shared son un solo proyecto.
    # Moverlos por separado rompería las rutas relativas entre ellos.
    write(tmp_path / "LR_project" / "mobile" / "package.json", "{}")
    write(tmp_path / "LR_project" / "website" / "package.json", "{}")
    write(tmp_path / "LR_project" / "shared" / "pyproject.toml", "[project]")
    write(tmp_path / "LR_project" / "datasets" / "precios.csv", "a,b")

    found = detector().detect(tmp_path)

    assert [candidate.path.name for candidate in found] == ["LR_project"]
    assert "monorepo" in found[0].markers


def test_a_single_nested_project_does_not_promote_its_parent(tmp_path):
    write(tmp_path / "contenedor" / "grabacion.mp4")
    write(tmp_path / "contenedor" / "el-proyecto" / "package.json", "{}")

    found = detector().detect(tmp_path)

    assert [candidate.path.name for candidate in found] == ["el-proyecto"]


def test_source_files_alone_are_enough_but_with_lower_confidence(tmp_path):
    write(tmp_path / "scripts" / "convertir.py", "import os")

    found = detector().detect(tmp_path)

    assert [candidate.path.name for candidate in found] == ["scripts"]
    assert found[0].markers == ()
    assert found[0].confidence == "baja"


def test_pattern_markers_are_recognized(tmp_path):
    write(tmp_path / "arduino" / "sos_led.ino", "void setup() {}")
    found = detector().detect(tmp_path)
    assert "Arduino" in found[0].markers


def test_detection_ignores_the_destination_folder(tmp_path):
    write(tmp_path / "Github repository" / "ya-movido" / "package.json", "{}")
    assert detector().detect(tmp_path) == []


def test_inspect_returns_none_for_an_empty_folder(tmp_path):
    (tmp_path / "vacia").mkdir()
    assert detector().inspect(tmp_path / "vacia") is None


# --------------------------------------------------------------------------- #
# Movimiento
# --------------------------------------------------------------------------- #

def test_moving_a_project_relocates_the_whole_folder(tmp_path):
    write(tmp_path / "origen" / "mi-app" / "package.json", "{}")
    write(tmp_path / "origen" / "mi-app" / "src" / "index.js", "console.log(1)")
    destination = tmp_path / "Github repository"
    destination.mkdir()

    candidate = detector().inspect(tmp_path / "origen" / "mi-app")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.MOVED
    assert (destination / "mi-app" / "src" / "index.js").is_file()
    assert not (tmp_path / "origen" / "mi-app").exists()


def test_name_collision_is_reported_and_nothing_is_overwritten(tmp_path):
    write(tmp_path / "origen" / "app" / "package.json", "{nuevo}")
    destination = tmp_path / "destino"
    write(destination / "app" / "package.json", "{el que ya estaba}")

    candidate = detector().inspect(tmp_path / "origen" / "app")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.CONFLICT
    assert (destination / "app" / "package.json").read_text(encoding="utf-8") == (
        "{el que ya estaba}"
    )
    assert (tmp_path / "origen" / "app").exists(), "el origen no se toca ante un conflicto"


def test_a_project_already_in_the_destination_is_left_alone(tmp_path):
    destination = tmp_path / "destino"
    write(destination / "app" / "package.json", "{}")

    candidate = detector().inspect(destination / "app")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.ALREADY_THERE
    assert (destination / "app" / "package.json").is_file()


def test_moving_a_folder_that_contains_the_destination_is_refused(tmp_path):
    write(tmp_path / "padre" / "package.json", "{}")
    destination = tmp_path / "padre" / "Github repository"
    destination.mkdir(parents=True)

    candidate = detector().inspect(tmp_path / "padre")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.INVALID
    assert (tmp_path / "padre").exists()


def test_readonly_files_do_not_stop_the_move(tmp_path):
    # Los objetos de git son de sólo lectura, y `shutil.rmtree` falla en seco con
    # ellos en Windows: el proyecto se copiaba y el origen quedaba a medio borrar.
    import os
    import stat

    write(tmp_path / "origen" / "repo" / "package.json", "{}")
    objeto = write(tmp_path / "origen" / "repo" / ".git" / "objects" / "ab" / "cdef", "blob")
    os.chmod(objeto, stat.S_IREAD)
    destination = tmp_path / "destino"

    candidate = detector().inspect(tmp_path / "origen" / "repo")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.MOVED
    assert (destination / "repo" / ".git" / "objects" / "ab" / "cdef").is_file()
    assert not (tmp_path / "origen" / "repo").exists()


def test_a_copy_that_leaves_residue_is_not_reported_as_a_failure(tmp_path, monkeypatch):
    # Si la copia llegó entera al destino pero el origen no se pudo borrar, decir
    # "error" es peor que decir la verdad: el usuario reintentaría creyendo que
    # sus archivos no llegaron.
    from organizador import projects as projects_module

    write(tmp_path / "origen" / "repo" / "package.json", "{}")
    destination = tmp_path / "destino"

    def copy_but_leave_source(source, target, *, dry_run=False):
        import shutil
        shutil.copytree(source, target)
        return False

    monkeypatch.setattr(projects_module, "move_directory", copy_but_leave_source)

    candidate = detector().inspect(tmp_path / "origen" / "repo")
    result = ProjectMover(destination).move(candidate)

    assert result.status is MoveStatus.COPIED_NOT_REMOVED
    assert result.status.is_success
    assert (destination / "repo" / "package.json").is_file()
    assert "borra a mano" in result.detail


def test_dry_run_move_leaves_the_disk_untouched(tmp_path):
    write(tmp_path / "origen" / "app" / "package.json", "{}")
    destination = tmp_path / "destino"

    candidate = detector().inspect(tmp_path / "origen" / "app")
    result = ProjectMover(destination, dry_run=True).move(candidate)

    assert result.status is MoveStatus.MOVED
    assert (tmp_path / "origen" / "app").exists()
    assert not (destination / "app").exists()

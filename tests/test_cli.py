"""Pruebas de la línea de comandos, con la CLI real de extremo a extremo."""

from __future__ import annotations

import pytest

from organizador.cli import main

from .helpers import tree, write


def test_organize_dry_run_touches_nothing(tmp_path, capsys):
    write(tmp_path / "foto.jpg")

    code = main(["organize", "--path", str(tmp_path), "--dry-run"])

    assert code == 0
    assert tree(tmp_path) == {"foto.jpg"}
    assert "SIMULACIÓN" in capsys.readouterr().out


def test_organize_with_yes_applies_the_plan(tmp_path):
    write(tmp_path / "foto.jpg")
    write(tmp_path / "informe.docx")

    code = main(["organize", "--path", str(tmp_path), "--yes"])

    assert code == 0
    assert tree(tmp_path) == {"Imágenes/foto.jpg", "Documentos/informe.docx"}


def test_organize_without_confirmation_refuses_in_a_non_interactive_shell(tmp_path):
    # Sin esta salvaguarda, cualquier script o tarea programada movería archivos
    # sin que nadie lo hubiera confirmado.
    write(tmp_path / "foto.jpg")

    code = main(["organize", "--path", str(tmp_path)])

    assert code == 0
    assert tree(tmp_path) == {"foto.jpg"}


def test_organize_writes_a_markdown_report(tmp_path):
    write(tmp_path / "foto.jpg")
    report = tmp_path / "informes" / "run.md"

    main(["organize", "--path", str(tmp_path), "--yes", "--report", str(report)])

    content = report.read_text(encoding="utf-8")
    assert "# Informe de organización" in content
    assert "foto.jpg" in content


def test_organize_per_folder_mode(tmp_path):
    write(tmp_path / "asignatura" / "tarea.docx")

    main(["organize", "--path", str(tmp_path), "--mode", "per-folder", "--yes"])

    assert tree(tmp_path) == {"asignatura/Documentos/tarea.docx"}


def test_organize_respects_extra_exclusions(tmp_path):
    write(tmp_path / "Intocable" / "archivo.pdf")

    main([
        "organize", "--path", str(tmp_path), "--mode", "per-folder",
        "--exclude", "Intocable", "--yes",
    ])

    assert tree(tmp_path) == {"Intocable/archivo.pdf"}


def test_analyze_never_moves_anything(tmp_path, capsys):
    write(tmp_path / "foto.jpg")
    write(tmp_path / "informe.docx")

    code = main(["analyze", "--path", str(tmp_path)])

    assert code == 0
    assert tree(tmp_path) == {"foto.jpg", "informe.docx"}
    out = capsys.readouterr().out
    assert "Imágenes" in out and "Documentos" in out


def test_init_config_creates_then_refuses_to_overwrite(tmp_path, capsys):
    config = tmp_path / "config" / "rules.json"

    assert main(["init-config", "--config", str(config)]) == 0
    assert config.is_file()
    assert main(["init-config", "--config", str(config)]) == 1
    assert "ya existe" in capsys.readouterr().err
    assert main(["init-config", "--config", str(config), "--force"]) == 0


def test_find_projects_lists_what_it_finds(tmp_path, capsys):
    write(tmp_path / "mi-app" / "package.json", "{}")
    write(tmp_path / "documentos" / "carta.docx")

    code = main(["find-projects", "--path", str(tmp_path)])

    assert code == 0
    out = capsys.readouterr().out
    assert "mi-app" in out
    assert "Proyectos detectados: 1" in out


def test_move_projects_needs_a_destination(tmp_path, capsys):
    code = main(["move-projects", "--path", str(tmp_path)])
    assert code == 1
    assert "Falta el destino" in capsys.readouterr().err


def test_move_projects_moves_a_detected_project(tmp_path):
    write(tmp_path / "origen" / "mi-app" / "package.json", "{}")
    destination = tmp_path / "Github repository"

    code = main([
        "move-projects", "--path", str(tmp_path / "origen"),
        "--destination", str(destination), "--yes",
    ])

    assert code == 0
    assert (destination / "mi-app" / "package.json").is_file()


def test_move_projects_accepts_an_explicit_folder(tmp_path, capsys):
    # `--project` es para cuando el usuario ya sabe qué quiere mover y no quiere
    # que la detección añada nada por su cuenta.
    write(tmp_path / "origen" / "notas" / "apunte.txt")
    destination = tmp_path / "destino"

    code = main([
        "move-projects", "--project", str(tmp_path / "origen" / "notas"),
        "--destination", str(destination), "--yes",
    ])

    assert code == 0
    assert (destination / "notas" / "apunte.txt").is_file()
    assert "no tiene marcadores de proyecto" in capsys.readouterr().out


def test_move_projects_fails_on_a_missing_explicit_folder(tmp_path, capsys):
    code = main([
        "move-projects", "--project", str(tmp_path / "no-existe"),
        "--destination", str(tmp_path / "destino"), "--yes",
    ])
    assert code == 1
    assert "No existe la carpeta" in capsys.readouterr().err


def test_unknown_command_exits_with_a_usage_error():
    with pytest.raises(SystemExit) as excinfo:
        main(["hacer-magia"])
    assert excinfo.value.code == 2

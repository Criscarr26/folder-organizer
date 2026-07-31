"""Pruebas de deshacer una organización."""

from __future__ import annotations

from organizador.executor import PlanExecutor
from organizador.rules import Ruleset
from organizador.undo import UndoPlanner, remove_empty_folders, undo_scan_filter

from .helpers import tree, write


def deshacer(root, *, solo_seguras=False, dry_run=False):
    planner = UndoPlanner(
        Ruleset.default(), undo_scan_filter(), only_sole_child=solo_seguras
    )
    plan = planner.plan(root)
    result = PlanExecutor(dry_run=dry_run).execute(plan)
    removed = remove_empty_folders(plan, dry_run=dry_run)
    return plan, result, removed


def test_devuelve_los_archivos_a_su_carpeta_madre(tmp_path):
    # El caso real: un paquete de iconos donde `apps/*.png` acabó en
    # `apps/Imágenes/*.png` y dejó de encontrarlo el tema.
    write(tmp_path / "apps" / "Imágenes" / "3d.png")
    write(tmp_path / "apps" / "Imágenes" / "Hardware.png")

    _, result, removed = deshacer(tmp_path)

    assert result.moved == 2
    assert tree(tmp_path) == {"apps/3d.png", "apps/Hardware.png"}
    assert len(removed) == 1


def test_organizar_y_deshacer_deja_todo_como_estaba(tmp_path):
    from organizador.classifier import FileClassifier
    from organizador.planner import OrganizePlanner
    from organizador.scanner import FileScanner, ScanFilter, ScanMode

    write(tmp_path / "foto.jpg")
    write(tmp_path / "informe.docx")
    write(tmp_path / "datos.xlsx")
    original = tree(tmp_path)

    ruleset = Ruleset.default()
    scan_filter = ScanFilter.build(extra_dirs=set(ruleset.folders))
    planner = OrganizePlanner(FileClassifier(ruleset), FileScanner(scan_filter))
    PlanExecutor().execute(planner.plan(tmp_path, ScanMode.LOOSE))
    assert tree(tmp_path) != original

    deshacer(tmp_path)

    assert tree(tmp_path) == original


def test_no_sobrescribe_si_la_madre_ya_tiene_ese_nombre(tmp_path):
    write(tmp_path / "carpeta" / "notas.txt", "el de fuera")
    write(tmp_path / "carpeta" / "Documentos" / "notas.txt", "el de dentro")

    _, result, _ = deshacer(tmp_path)

    assert result.errors == []
    assert tree(tmp_path) == {"carpeta/notas.txt", "carpeta/notas_1.txt"}
    contenidos = {
        (tmp_path / "carpeta" / n).read_text(encoding="utf-8")
        for n in ("notas.txt", "notas_1.txt")
    }
    assert contenidos == {"el de fuera", "el de dentro"}


def test_solo_seguras_respeta_las_carpetas_que_conviven_con_hermanas(tmp_path):
    # `Resources/Imágenes` de un proyecto WinForms: legítima, tiene hermanas.
    write(tmp_path / "Resources" / "Imágenes" / "build.png")
    write(tmp_path / "Resources" / "estilos.css")
    # Ésta sí es del organizador: es lo único que hay en su madre.
    write(tmp_path / "apps" / "Imágenes" / "3d.png")

    plan, result, _ = deshacer(tmp_path, solo_seguras=True)

    assert result.moved == 1
    assert "Resources/Imágenes/build.png" in tree(tmp_path)
    assert "apps/3d.png" in tree(tmp_path)
    assert any("puede ser tuya" in s.reason for s in plan.skipped)


def test_sin_solo_seguras_tambien_deshace_las_que_conviven(tmp_path):
    write(tmp_path / "Resources" / "Imágenes" / "build.png")
    write(tmp_path / "Resources" / "estilos.css")

    _, result, _ = deshacer(tmp_path)

    assert result.moved == 1
    assert tree(tmp_path) == {"Resources/build.png", "Resources/estilos.css"}


def test_dry_run_no_toca_nada(tmp_path):
    write(tmp_path / "apps" / "Imágenes" / "3d.png")
    antes = tree(tmp_path)

    plan, result, removed = deshacer(tmp_path, dry_run=True)

    assert tree(tmp_path) == antes
    assert len(plan.moves) == 1
    assert result.moved == 1  # lo que haría
    assert len(removed) == 1


def test_deshace_tambien_la_cuarentena_de_duplicados(tmp_path):
    write(tmp_path / "_Duplicados" / "copia.txt")

    _, result, _ = deshacer(tmp_path)

    assert result.moved == 1
    assert tree(tmp_path) == {"copia.txt"}


def test_deshace_las_carpetas_de_la_version_1(tmp_path):
    # `Archivos` y `Ejecutables` eran categorías de la 1.0 y desaparecieron en
    # la 2.0. Sin conocerlas, deshacer dejaría atrás lo que rompió esa versión.
    write(tmp_path / "descargas" / "Archivos" / "backup.zip")
    write(tmp_path / "programas" / "Ejecutables" / "setup.exe")

    _, result, _ = deshacer(tmp_path)

    assert result.moved == 2
    assert tree(tmp_path) == {"descargas/backup.zip", "programas/setup.exe"}


def test_borra_la_carpeta_aunque_sea_de_solo_lectura(tmp_path):
    # Las carpetas dentro de OneDrive suelen llevar el atributo de sólo lectura,
    # y `rmdir` responde "Access is denied" aunque estén vacías.
    import os
    import stat

    write(tmp_path / "apps" / "Imágenes" / "3d.png")
    os.chmod(tmp_path / "apps" / "Imágenes", stat.S_IREAD)

    _, result, removed = deshacer(tmp_path)

    assert result.moved == 1
    assert len(removed) == 1
    assert not (tmp_path / "apps" / "Imágenes").exists()


def test_una_ruta_larga_no_impide_acortarla(tmp_path):
    # Deshacer siempre acorta la ruta. Rechazar el movimiento por longitud
    # dejaba el archivo atrapado justo en la carpeta que se quería vaciar.
    from organizador.executor import PlanExecutor
    from organizador.models import OrganizePlan, PlannedMove, MoveReason

    largo = "n" * 120
    origen = write(tmp_path / largo / "Documentos" / f"{largo}.pdf")
    destino = tmp_path / largo / f"{largo}.pdf"
    assert len(str(destino)) > 255, "el caso de prueba necesita una ruta larga"

    plan = OrganizePlan(root=tmp_path)
    plan.moves.append(PlannedMove(origen, destino, "Documentos", MoveReason.UNDO))
    result = PlanExecutor().execute(plan)

    assert result.errors == []
    assert result.moved == 1


def test_devuelve_tambien_los_archivos_ocultos(tmp_path):
    # La 1.0 no respetaba los ocultos, asi que tambien los movio. Si deshacer
    # los saltara, un `.env.example` se quedaria dentro de `Otros/` para siempre.
    write(tmp_path / "proyecto" / "Otros" / ".env.example")
    write(tmp_path / "proyecto" / "Otros" / ".gitignore")

    _, result, removed = deshacer(tmp_path)

    assert result.moved == 2
    assert tree(tmp_path) == {"proyecto/.env.example", "proyecto/.gitignore"}
    assert len(removed) == 1


def test_no_toca_carpetas_que_no_son_de_categoria(tmp_path):
    write(tmp_path / "Facturas" / "enero.pdf")

    plan, _, _ = deshacer(tmp_path)

    assert plan.moves == []
    assert tree(tmp_path) == {"Facturas/enero.pdf"}


def test_una_carpeta_con_subcarpetas_no_se_borra_pero_si_se_vacia(tmp_path):
    write(tmp_path / "Documentos" / "suelto.pdf")
    write(tmp_path / "Documentos" / "subcarpeta" / "dentro.pdf")

    _, result, removed = deshacer(tmp_path)

    assert result.moved == 1
    assert removed == []  # sigue teniendo la subcarpeta, rmdir falla y se deja
    assert tree(tmp_path) == {"suelto.pdf", "Documentos/subcarpeta/dentro.pdf"}


def test_no_entra_en_carpetas_de_herramientas(tmp_path):
    write(tmp_path / ".git" / "Documentos" / "interno.txt")
    write(tmp_path / "node_modules" / "Otros" / "paquete.js")

    plan, _, _ = deshacer(tmp_path)

    assert plan.moves == []

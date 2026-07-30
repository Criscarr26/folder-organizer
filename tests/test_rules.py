"""Pruebas de las reglas de clasificación."""

from organizador.classifier import FileClassifier
from organizador.models import Category, FileInfo
from organizador.rules import DEFAULT_RULES, Ruleset

from .helpers import make_file_info


def test_default_rules_cover_the_usual_suspects():
    ruleset = Ruleset.default()
    assert ruleset.category_for(".jpg").folder == "Imágenes"
    assert ruleset.category_for(".docx").folder == "Documentos"
    assert ruleset.category_for(".xlsx").folder == "Hojas de cálculo"
    assert ruleset.category_for(".pptx").folder == "Presentaciones"
    assert ruleset.category_for(".mp4").folder == "Videos"
    assert ruleset.category_for(".zip").folder == "Comprimidos"


def test_unknown_extension_falls_back():
    ruleset = Ruleset.default()
    assert ruleset.category_for(".qwerty").folder == "Otros"
    assert ruleset.category_for("").folder == "Otros"


def test_extension_matching_ignores_case():
    ruleset = Ruleset.default()
    assert ruleset.category_for(".JPG") == ruleset.category_for(".jpg")


def test_first_declared_category_wins_on_conflict():
    ruleset = Ruleset.from_mapping(
        {
            "primera": {"folder": "Primera", "extensions": [".dat"]},
            "segunda": {"folder": "Segunda", "extensions": [".dat"]},
        }
    )
    assert ruleset.category_for(".dat").folder == "Primera"


def test_folders_include_the_fallback():
    # El scanner usa esta lista para no volver a mover lo ya ordenado, así que
    # la carpeta del comodín tiene que estar dentro.
    assert "Otros" in Ruleset.default().folders


def test_from_mapping_tolerates_a_single_string_extension():
    ruleset = Ruleset.from_mapping({"uno": {"folder": "Uno", "extensions": ".pdf"}})
    assert ruleset.category_for(".pdf").folder == "Uno"


def test_roundtrip_through_mapping_is_stable():
    original = Ruleset.default()
    rebuilt = Ruleset.from_mapping(original.to_mapping())
    assert rebuilt.extension_map.keys() == original.extension_map.keys()


def test_default_rules_have_no_duplicate_extensions():
    seen: set[str] = set()
    for name, config in DEFAULT_RULES.items():
        for extension in config["extensions"]:
            assert extension not in seen, f"{extension} repetida en {name}"
            seen.add(extension)


def test_classifier_groups_by_category(tmp_path):
    ruleset = Ruleset.default()
    classifier = FileClassifier(ruleset)
    files = [
        make_file_info(tmp_path / "a.jpg"),
        make_file_info(tmp_path / "b.png"),
        make_file_info(tmp_path / "c.pdf"),
    ]
    grouped = classifier.summarize(files)
    folders = {category.folder: len(items) for category, items in grouped.items()}
    assert folders == {"Imágenes": 2, "Documentos": 1}


def test_classify_uses_the_suffix_only():
    ruleset = Ruleset.from_mapping({"docs": {"folder": "Docs", "extensions": [".pdf"]}})
    classifier = FileClassifier(ruleset)
    info = FileInfo(path=__import__("pathlib").Path("informe.final.pdf"), size=1, modified=None)
    assert classifier.classify(info) == Category(
        name="docs", folder="Docs", extensions=frozenset({".pdf"})
    )

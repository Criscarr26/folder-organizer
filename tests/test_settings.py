"""Pruebas de la carga de configuración."""

from __future__ import annotations

import json

from organizador.duplicates import DuplicatePolicy
from organizador.settings import (
    Settings,
    load_dotenv,
    load_ruleset,
    write_default_config,
)


def test_defaults_when_the_environment_is_empty():
    settings = Settings.from_env({})
    assert settings.log_level == "INFO"
    assert settings.duplicate_policy is DuplicatePolicy.QUARANTINE
    assert settings.log_file is None


def test_environment_overrides_the_defaults():
    settings = Settings.from_env(
        {"LOG_LEVEL": "debug", "LOG_FILE": "salida.log", "DUPLICATE_POLICY": "report"}
    )
    assert settings.log_level == "DEBUG"
    assert settings.log_file.name == "salida.log"
    assert settings.duplicate_policy is DuplicatePolicy.REPORT


def test_an_invalid_policy_falls_back_to_quarantine():
    # Que una variable mal escrita active un borrado sería inaceptable; la
    # opción segura es la que gana.
    settings = Settings.from_env({"DUPLICATE_POLICY": "borrar-todo"})
    assert settings.duplicate_policy is DuplicatePolicy.QUARANTINE


def test_missing_config_file_uses_the_default_rules(tmp_path):
    ruleset = load_ruleset(tmp_path / "no-existe.json")
    assert ruleset.category_for(".jpg").folder == "Imágenes"


def test_corrupt_config_file_falls_back_instead_of_crashing(tmp_path):
    broken = tmp_path / "roto.json"
    broken.write_text("{esto no es json", encoding="utf-8")

    ruleset = load_ruleset(broken)

    assert ruleset.category_for(".jpg").folder == "Imágenes"


def test_custom_config_file_is_used(tmp_path):
    config = tmp_path / "reglas.json"
    config.write_text(
        json.dumps({"mios": {"folder": "Míos", "extensions": [".abc"]}}),
        encoding="utf-8",
    )

    ruleset = load_ruleset(config)

    assert ruleset.category_for(".abc").folder == "Míos"
    assert ruleset.category_for(".jpg").folder == "Otros", "sólo valen las reglas del archivo"


def test_write_default_config_then_read_it_back(tmp_path):
    target = tmp_path / "config" / "rules.json"

    assert write_default_config(target) is True
    assert load_ruleset(target).category_for(".docx").folder == "Documentos"


def test_write_default_config_does_not_overwrite_without_force(tmp_path):
    target = tmp_path / "rules.json"
    target.write_text("{}", encoding="utf-8")

    assert write_default_config(target) is False
    assert target.read_text(encoding="utf-8") == "{}"
    assert write_default_config(target, overwrite=True) is True


def test_dotenv_does_not_override_the_real_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("LOG_LEVEL=DEBUG\nOTRA=1\n", encoding="utf-8")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")

    load_dotenv(env_file)

    assert Settings.from_env().log_level == "WARNING"
    monkeypatch.delenv("OTRA", raising=False)


def test_dotenv_ignores_comments_and_blank_lines(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text('# comentario\n\nLOG_FILE="ruta.log"\nsin_igual\n', encoding="utf-8")
    monkeypatch.delenv("LOG_FILE", raising=False)

    load_dotenv(env_file)

    assert Settings.from_env().log_file.name == "ruta.log"

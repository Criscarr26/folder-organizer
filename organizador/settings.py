"""Carga de configuración: variables de entorno y reglas en JSON.

A diferencia de la versión anterior, cargar la configuración no configura el
logging como efecto secundario. Eso hacía que crear dos `ConfigManager`
duplicara las líneas del log; ahora quien arranca la aplicación decide cuándo
configurar el logging, una sola vez.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from .duplicates import DuplicatePolicy
from .rules import DEFAULT_RULES, FALLBACK_CATEGORY, Ruleset

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = Path("config/rules.json")


@dataclass(frozen=True)
class Settings:
    """Ajustes de ejecución, resueltos desde el entorno."""

    config_file: Path = DEFAULT_CONFIG_FILE
    log_level: str = "INFO"
    log_file: Path | None = None
    duplicate_policy: DuplicatePolicy = DuplicatePolicy.QUARANTINE
    projects_destination: Path | None = None

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Settings:
        env = dict(os.environ if env is None else env)
        log_file = env.get("LOG_FILE") or None
        destination = env.get("PROJECTS_DESTINATION") or None
        return cls(
            config_file=Path(env.get("CONFIG_FILE") or DEFAULT_CONFIG_FILE),
            log_level=env.get("LOG_LEVEL", "INFO").upper(),
            log_file=Path(log_file) if log_file else None,
            duplicate_policy=_parse_policy(env.get("DUPLICATE_POLICY")),
            projects_destination=Path(destination) if destination else None,
        )


def _parse_policy(raw: str | None) -> DuplicatePolicy:
    if not raw:
        return DuplicatePolicy.QUARANTINE
    try:
        return DuplicatePolicy(raw.strip().lower())
    except ValueError:
        logger.warning("DUPLICATE_POLICY='%s' no es válido; se usa 'quarantine'.", raw)
        return DuplicatePolicy.QUARANTINE


def load_dotenv(path: Path = Path(".env")) -> None:
    """Carga un `.env` sencillo sin dependencias externas.

    Las variables ya presentes en el entorno tienen prioridad: lo que el usuario
    escribe en la línea de comandos no debería perder contra un archivo.
    """
    if not path.is_file():
        return
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("No se pudo leer %s: %s", path, exc)
        return

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def load_ruleset(config_file: Path | None, *, con_comodin: bool = True) -> Ruleset:
    """Lee las reglas del JSON indicado; usa las de por defecto si no se puede.

    Un JSON corrupto avisa y no detiene la ejecución: el usuario quiere ordenar
    su carpeta, y las reglas por defecto son un resultado razonable.

    Con `con_comodin=False` los archivos cuya extensión no aparezca en las
    reglas se quedan donde están en vez de ir a `Otros/`.
    """
    comodin = FALLBACK_CATEGORY if con_comodin else None
    if config_file is None:
        return Ruleset.from_mapping(DEFAULT_RULES, comodin)

    path = Path(config_file)
    if not path.is_file():
        logger.info("No hay configuración en %s; se usan las reglas por defecto.", path)
        return Ruleset.from_mapping(DEFAULT_RULES, comodin)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("No se pudo leer %s (%s); se usan las reglas por defecto.", path, exc)
        return Ruleset.from_mapping(DEFAULT_RULES, comodin)

    if not isinstance(raw, dict) or not raw:
        logger.warning("%s no contiene un objeto de reglas; se usan las de por defecto.", path)
        return Ruleset.from_mapping(DEFAULT_RULES, comodin)

    logger.info("Reglas cargadas desde %s (%d categorías).", path, len(raw))
    return Ruleset.from_mapping(raw, comodin)


def write_default_config(path: Path, *, overwrite: bool = False) -> bool:
    """Escribe las reglas por defecto. False si el archivo ya existía."""
    path = Path(path)
    if path.exists() and not overwrite:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(DEFAULT_RULES, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return True

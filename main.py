#!/usr/bin/env python3
"""Punto de entrada del Organizador Automático de Carpetas.

    python main.py organize --path "C:/ruta" --dry-run
    python main.py move-projects --path "C:/ruta" --destination "C:/Github repository"
"""

from organizador.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

"""Organizador automático de carpetas.

Ordena archivos por tipo y reúne los proyectos de código en una sola carpeta.
Sin dependencias externas: sólo la biblioteca estándar de Python.

Estructura del paquete, de dentro hacia fuera:

* `models`, `rules`, `paths` — datos y utilidades, sin efectos secundarios.
* `scanner`, `classifier`, `duplicates` — leen el disco y deciden qué es qué.
* `planner` — convierte una carpeta en una lista de movimientos propuestos.
* `executor` — el único módulo que escribe.
* `projects` — detecta y reubica carpetas de proyecto.
* `settings`, `logging_setup`, `reporting`, `cli` — entrada y salida.
"""

__version__ = "2.0.0"
__all__ = ["__version__"]

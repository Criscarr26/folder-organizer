# Instrucciones para asistentes de código

Organizador automático de carpetas: CLI en Python que ordena archivos por tipo y
reúne proyectos de código en una sola carpeta.

## Reglas del proyecto

- **Sin dependencias.** Sólo biblioteca estándar (`argparse`, `logging`,
  `hashlib`, `shutil`, `pathlib`), Python 3.9+. No añadas paquetes de terceros:
  en el equipo de origen `pip` está detrás de un proxy que rompe TLS, y "clonar
  y ejecutar" es un requisito, no una preferencia.
- **Nada se borra.** Los duplicados van a `_Duplicados`. No existe una política
  de borrado y no hay que añadirla.
- **Sólo `executor.py` escribe en disco.** Si una función nueva necesita mover o
  borrar algo, va ahí.
- **Decidir y ejecutar están separados.** `planner` construye un `OrganizePlan`;
  `executor` lo aplica. `--dry-run` construye el mismo plan y no lo ejecuta, así
  que la simulación no puede desviarse de la ejecución real. No añadas ramas
  `if dry_run` en la lógica de decisión.
- **Los comandos de `cli.py` son finos:** ensamblan e imprimen. Cualquier
  decisión nueva va a `planner` o `projects`.

## Estilo

- Código y comentarios en español, igual que el resto del repositorio.
- Los comentarios explican *por qué*, no *qué*. Si documentan un caso real que
  falló, menciónalo.
- Anotaciones de tipo en las firmas públicas. `from __future__ import annotations`
  en todos los módulos.
- Dataclasses inmutables (`frozen=True`) para los datos de dominio.

## Pruebas

```bash
python -m pytest tests -q
```

- Las pruebas afirman sobre el árbol de archivos resultante (`helpers.tree`), no
  sobre el log.
- `helpers.write` usa el nombre del archivo como contenido por defecto, para que
  dos archivos distintos no resulten duplicados por accidente.
- Todo va en `tmp_path`. Sin red y sin tocar carpetas reales.
- Cualquier cambio de comportamiento en el movimiento de archivos necesita una
  prueba que falle antes del cambio.

## Antes de dar algo por terminado

- `python -m pytest tests -q` en verde.
- `python main.py --help` funciona con el Python del sistema, sin entorno virtual.
- Si cambia el comportamiento de la CLI: actualiza `README.md`, `CHANGELOG.md` y
  `docs/`. La documentación que describe módulos que ya no existen es peor que no
  tener documentación.

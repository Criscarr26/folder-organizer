# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/).

## [2.2.0]

Ordenar una carpeta de apuntes reveló que el organizador sólo sabía funcionar
en carpetas homogéneas. En una carpeta de universidad conviven los PDF de clase
con un tema de iconos, dos programas instalados y varios proyectos de código, y
la versión anterior se llevaba por delante los tres últimos.

### Added

- `--solo-clasificados`: los archivos cuya extensión no aparece en las reglas se
  quedan donde están, en vez de acabar en `Otros/`. Sin esto, ordenar los
  apuntes de una carpeta arrastraba también los 3.582 PNG de un tema de iconos,
  los `.dll` de un paquete y el código de los proyectos.
- `--exclude-path RUTA` (repetible): excluye una carpeta concreta por su ruta.
  `--exclude` compara por nombre, y eso no distingue una instalación en `dia/`
  de una asignatura llamada `DIA/`.
- `config/rules-apuntes.json`: reglas sólo para documentos de clase. Deja fuera
  `.txt` y `.csv` a propósito, porque mover un `requirements.txt` rompe el
  proyecto que lo contiene.

### Fixed

- **La cuarentena de duplicados ya no toca archivos que las reglas no cubren.**
  La detección de duplicados corría antes de clasificar, así que con
  `--solo-clasificados` seguía moviendo a `_Duplicados/` cosas que se había
  prometido no tocar: en una prueba real, 2.240 archivos de un programa
  instalado, cuyos `.dll` e iconos repetidos son copias legítimas. Clasificar va
  primero: lo que no se va a ordenar no se mira siquiera.

## [2.1.0]

### Added

- `undo` — reverses an organization, moving files out of the category folders
  back into their parent and removing the folders it empties. Written to repair
  what 1.0 did: run over a folder tree, it had buried an icon theme's PNGs in
  `apps/Imágenes/`, a Visual Studio `.sln` in `Otros/`, and several projects'
  source files away from the code that imported them.
  - Knows every folder name this tool has used, including `Archivos` and
    `Ejecutables` from 1.0 and the `_Duplicados` quarantine.
  - `--solo-seguras` restricts it to category folders that are the sole entry
    in their parent, the clearest signature of a previous run.
  - Moves hidden and protected files too. `organize` leaves them alone, but
    anything *inside* a category folder was put there by this tool, and 1.0 did
    not spare dotfiles — skipping them would strand a `.env.example` for good.

### Fixed

- **Emptied folders are removed even when marked read-only.** `rmdir` answers
  "Access is denied" on a read-only directory even when it is empty, and folders
  inside OneDrive carry that attribute routinely. 147 folders survived a repair
  run before this was fixed.
- **The path-length guard no longer blocks moves that shorten the path.** It
  compared the destination against the limit without looking at the source, so
  a file already living at a 267-character path could not be moved up to a
  256-character one — trapping it in the very folder being emptied.

## [2.0.0]

Rewrite around a plan/execute split. The CLI keeps its command names, so
existing invocations of `organize`, `analyze` and `init-config` still work.

### Fixed

- **`organize` no longer flattens folder trees.** It classified files
  recursively and then moved every one of them into category folders at the
  root, destroying the existing hierarchy. Traversal is now an explicit choice:
  `--mode loose` (default) only touches files sitting directly in the target
  folder, `--mode per-folder` sorts each folder's files inside that same folder.
- **Duplicates are no longer deleted.** The hierarchical organizer called
  `unlink()` on any file whose hash it had already seen. Copies now move to
  `_Duplicados`; there is no delete policy at all.
- **Two files can no longer be assigned the same destination.** Name-conflict
  resolution checked only the disk, so a file renamed to sidestep an existing
  one could take the name a second file had already been given, and the second
  move overwrote the first.
- **Read-only files no longer break a project move.** `shutil.rmtree` fails
  outright on the read-only objects inside `.git`, which left the source folder
  half-deleted after a successful copy. The attribute is now cleared and the
  delete retried.
- **A copy that leaves residue is no longer reported as a failure.** When the
  files arrive but the source can't be fully removed, the result is
  `COPIED_NOT_REMOVED` with the path to clean up, instead of an `error` that
  sends the user looking for data that is already safe.
- **Log lines are no longer duplicated.** Loading configuration called
  `logger.add()` as a side effect, so a second config object added a second sink.
- Empty files are no longer treated as duplicates of each other.
- Dead code removed: `classify()` could never return `None`, so every caller's
  `if not classification` guard was unreachable.

### Added

- `find-projects` — lists folders that look like code projects, with the
  evidence for each. Marker files or own source at the top level only, so a
  folder that merely contains a project isn't mistaken for one. Sibling projects
  under a non-project parent are reported as a monorepo.
- `move-projects` — moves project folders into one destination. Refuses to
  overwrite: a name collision is reported and skipped. `--project` moves an
  explicit folder and skips detection.
- `--dry-run` on every destructive command, and a confirmation prompt before
  applying. Non-interactive shells refuse without `--yes`.
- `--report FILE` writes a full Markdown report; console output stays truncated.
- `--duplicates quarantine|report|ignore`, `--exclude NAME` (repeatable),
  `--log-file`.
- Nested category folders: `"folder": "Sorted/Documentos"` is valid, for when a
  category name collides with an existing folder. `config/rules-contenedor.json`
  ships that setup for OneDrive roots.
- Cloud-only OneDrive files are moved but never read, so organizing a folder
  cannot trigger a large download. They're skipped by the duplicate check.
- New categories: spreadsheets, presentations, code, installers.
- Protected from any move: `desktop.ini`, `Thumbs.db`, dotfiles, `.lnk`/`.url`
  shortcuts, partial downloads. Never traversed: `.git`, virtualenvs,
  `node_modules`, build output, editor metadata, and `Github repository`.
- Path-length guard: a destination over 255 characters is reported per file
  instead of crashing the run.
- Tests covering idempotency, conflicts, quarantine, exclusions, both scan
  modes, project detection, and dry-run/real-run equivalence.
- `pyproject.toml` with an `organizador` console script.

### Changed

- **No third-party dependencies.** `click` → `argparse`, `loguru` → `logging`,
  `python-dotenv` → a small `.env` reader. `pathlib2` was declared but unused,
  and is dead on Python 3. This also retires the SSL/pip installation problem
  listed as a known issue in 1.0.0: there is nothing left to install.
- Minimum Python lowered from 3.11 to 3.9.
- Package moved from `src/` to `organizador/`, split into modules with one
  responsibility each. Only `executor.py` writes to disk.
- Duplicate detection groups by size before hashing, so most files are never
  read.
- `init-config` refuses to overwrite an existing file without `--force`.
- An unreadable rules file or an invalid `DUPLICATE_POLICY` falls back to the
  safe default with a warning instead of failing.
- Docs rewritten to match the code: `docs/ARCHITECTURE.md` replaces
  `DEVELOPMENT.md`, `FEATURES.md` and `PROJECT_SUMMARY.md`, which described
  modules that no longer exist.

### Removed

- `src/organizer.py`, `src/hierarchical_organizer.py`, `src/config.py`,
  `src/classifier.py`, `src/cli.py` — replaced by the `organizador` package.
- `demo.py`, which duplicated what `analyze --path ./test_organize` shows.
- The duplicate-deletion code path.

## [1.0.0] - 2026-06-03

### Added

- Automatic file classification by type.
- CLI built on Click, with `organize`, `analyze` and `init-config`.
- `--dry-run` mode to preview changes.
- Automatic name-conflict handling.
- Logging via Loguru, and JSON-configurable rules with environment-variable
  support.
- Documentation and a unit test suite.

### Known issues

- Requires Python 3.11+.
- Installing the dependencies can fail with SSL certificate errors on Windows;
  `pip install --trusted-host pypi.org ...` was the workaround. Resolved in
  2.0.0 by removing the dependencies.

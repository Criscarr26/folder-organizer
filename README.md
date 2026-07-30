# Automatic Folder Organizer

A Python CLI that sorts files into folders by type and gathers scattered code
projects into a single directory.

**No dependencies.** Standard library only, Python 3.9+. Clone it and run it —
there is nothing to install.

## Quick start

```bash
python main.py analyze --path "C:/Users/me/Downloads"
```

```bash
python main.py organize --path "C:/Users/me/Downloads" --dry-run
```

```bash
python main.py organize --path "C:/Users/me/Downloads" --yes
```

`analyze` and `--dry-run` never touch a file. Without `--dry-run` the command
shows the plan and asks for confirmation before moving anything; `--yes` skips
the prompt for use in scripts.

## What it does

Given a folder like this:

```
Downloads/
├── invoice.pdf
├── holiday.jpg
├── budget.xlsx
├── invoice-copy.pdf      <- byte-identical to invoice.pdf
└── setup.exe
```

`organize` turns it into:

```
Downloads/
├── Documentos/invoice.pdf
├── Imágenes/holiday.jpg
├── Hojas de cálculo/budget.xlsx
├── Instaladores/setup.exe
└── _Duplicados/invoice-copy.pdf
```

Duplicates are detected by content (SHA-256), not by name. They are **moved to
`_Duplicados`, never deleted** — deciding which copy matters is your call, not
the script's.

## Commands

### `organize`

Moves files into folders by type.

| Option | Meaning |
| --- | --- |
| `--path PATH` | Folder to organize (default: current directory). |
| `--mode loose\|per-folder` | `loose` (default) only touches files sitting directly in `PATH`. `per-folder` walks the whole tree and sorts each folder's files inside that same folder. |
| `--duplicates quarantine\|report\|ignore` | `quarantine` (default) moves copies to `_Duplicados`; `report` only lists them; `ignore` skips the check entirely (no file contents are read). |
| `--config FILE` | JSON rules file. |
| `--exclude NAME` | Folder name to never touch. Repeatable. |
| `--report FILE` | Write a full Markdown report. |
| `--dry-run` | Show the plan, change nothing. |
| `--yes` | Don't ask for confirmation. |
| `--verbose` / `--log-file FILE` | More detail / write a log. |

The two modes exist because they solve different problems:

```bash
# Clean up a download folder: only the loose files, subfolders untouched.
python main.py organize --path ~/Downloads --yes

# Tidy coursework: each subject folder gets its own Documentos/, Imágenes/...
python main.py organize --path "D:/University" --mode per-folder --yes
```

### `analyze`

Shows how files would be grouped, with counts and sizes. Moves nothing.

### `find-projects`

Lists folders that look like code projects, with the evidence for each.

```bash
python main.py find-projects --path "C:/Users/me" --path "D:/work"
```

A folder counts as a project when it has a marker file at its top level
(`package.json`, `pyproject.toml`, `.git`, `project.godot`, `*.sln`, `*.ino`…)
or its own source files. A folder that merely *contains* a project is not a
project, so a directory holding recordings plus one game folder reports the game
— not the directory. When several sibling projects share a parent that isn't one
itself, the parent is reported as a monorepo, because moving the pieces apart
would break the paths between them.

### `move-projects`

Moves project folders into one destination, without overwriting anything.

```bash
python main.py move-projects \
  --path "C:/Users/me" \
  --destination "D:/Github repository" --dry-run
```

| Option | Meaning |
| --- | --- |
| `--path PATH` | Where to look for projects. Repeatable. |
| `--project PATH` | Move exactly this folder, skipping detection. Repeatable. |
| `--destination PATH` | Target folder (or the `PROJECTS_DESTINATION` env var). |
| `--dry-run` / `--yes` | As in `organize`. |

If the destination already has a folder with that name, the move is **reported
and skipped**. Two folders with the same name are usually two versions of the
same project, and merging them blindly is exactly what you don't want.

### `init-config`

Writes the default rules to a JSON file you can edit. `--force` overwrites.

## Configuration

### Rules

```json
{
  "images": {
    "folder": "Imágenes",
    "extensions": [".jpg", ".jpeg", ".png"]
  },
  "documents": {
    "folder": "Documentos",
    "extensions": [".pdf", ".docx", ".txt"]
  }
}
```

Anything whose extension isn't listed goes to `Otros`. If an extension appears
in two categories the first one wins, and a warning says so.

`folder` may be a nested path. That matters when a category name collides with a
folder that already exists — for example at a OneDrive root, where `Documentos`
is your real Documents folder:

```json
{ "documents": { "folder": "Sorted files/Documentos", "extensions": [".pdf"] } }
```

`config/rules-contenedor.json` is a ready-made ruleset that groups every
category under `Archivos ordenados/` for exactly that case.

### Environment variables

Optional, read from the environment or a `.env` file:

```bash
CONFIG_FILE=config/rules.json
LOG_LEVEL=INFO
LOG_FILE=organizer.log
DUPLICATE_POLICY=quarantine
PROJECTS_DESTINATION=D:/Github repository
```

Values already set in the environment win over the `.env` file. An unreadable
rules file or an invalid `DUPLICATE_POLICY` falls back to the safe default and
logs a warning instead of failing.

## What it will not touch

- `desktop.ini`, `Thumbs.db`, `.DS_Store`, dotfiles.
- `.lnk` and `.url` shortcuts, and partial downloads (`.tmp`, `.crdownload`,
  `.part`). A shortcut points elsewhere from where it sits, so moving it breaks
  the reference without organizing anything.
- Tool and dependency folders: `.git`, `.venv`, `venv`, `node_modules`,
  `__pycache__`, `dist`, `build`, `.vscode`, `.idea` and friends.
- Any folder named `Github repository`, and the category folders themselves —
  which is what makes running the command twice a no-op.
- Files OneDrive keeps in the cloud are moved but never read, so organizing a
  folder can't trigger a multi-gigabyte download. They're skipped by the
  duplicate check for the same reason.

## Architecture

Decisions and disk writes are deliberately separated:

```
organizador/
├── models.py         Immutable data: FileInfo, PlannedMove, OrganizePlan
├── rules.py          Extension -> category index
├── paths.py          Case-insensitive containment, unique names, length limit
├── scanner.py        Walks the disk, applies exclusions (loose / per-folder)
├── classifier.py     File -> category. Pure function
├── duplicates.py     Size buckets, then SHA-256. Cloud-aware
├── planner.py        Folder -> list of proposed moves. Writes nothing
├── executor.py       The only module that writes
├── projects.py       Project detection and relocation
├── settings.py       Env vars and JSON rules
├── logging_setup.py  Standard-library logging, configured once
├── reporting.py      Console output and Markdown reports
└── cli.py            argparse commands, thin
```

The planner produces an `OrganizePlan`; the executor applies it. `--dry-run`
builds the same plan and skips execution, so the simulation cannot disagree with
the real run. Everything up to the plan is testable without touching a disk.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the reasoning behind each
boundary.

## Tests

```bash
python -m pytest tests -q
```

77 tests, no network and no fixtures outside `tmp_path`. They cover the cases
that matter for a tool that moves files: idempotency, name conflicts, refusing
to flatten a tree, quarantine instead of deletion, read-only files inside
`.git`, and a dry run planning exactly what the real run does.

## License

MIT — see [LICENSE](LICENSE).

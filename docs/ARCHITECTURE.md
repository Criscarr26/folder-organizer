# Architecture

Why the code is split the way it is. The short version: **deciding what to do is
separated from doing it**, because this program moves people's files and a
simulation that can disagree with the real run is worse than no simulation.

## The central split

```
scanner ──> classifier ──> planner ──> OrganizePlan ──> executor ──> disk
                              │
                          duplicates
```

`OrganizePlanner.plan()` returns an `OrganizePlan`: a list of `PlannedMove`
objects plus the files it decided to leave alone and why. It writes nothing.
`PlanExecutor.execute()` takes that plan and applies it.

`--dry-run` is not a second code path. It builds the same plan and the executor
skips the `shutil.move` call. There is no branch where the simulation computes a
destination differently from the real run, which is the bug class this layout
exists to prevent. `test_dry_run_plans_exactly_what_the_real_run_does` asserts it
directly by comparing the two plans.

## Module boundaries

| Module | Responsibility | Touches disk |
| --- | --- | --- |
| `models` | Immutable dataclasses | no |
| `rules` | Extension → `Category` index | no |
| `paths` | Containment, unique names, path length | reads only |
| `classifier` | `FileInfo` → `Category` | no |
| `scanner` | Walk, prune excluded folders, stat files | reads |
| `duplicates` | Content identity | reads |
| `planner` | Build the plan | reads |
| `executor` | Apply the plan | **writes** |
| `projects` | Detect and relocate projects | reads, delegates writes |
| `settings`, `logging_setup` | Startup wiring | reads |
| `reporting` | Text out | writes reports only |
| `cli` | Parse arguments, wire, print | no |

Only `executor` moves or deletes anything. To audit what this tool can do to a
filesystem, that is the one file to read.

## Decisions worth explaining

### Two scan modes, not one recursive walk

`ScanMode.LOOSE` collects only files sitting directly in the root.
`ScanMode.PER_FOLDER` walks the tree and anchors each file's destination to its
*own* folder.

The previous version classified recursively but moved everything into folders at
the root, which flattened the user's hierarchy — the worst possible outcome for
an "organizer". Making the traversal an explicit choice removes the footgun;
`test_loose_mode_never_descends_into_subfolders` locks it in.

`PER_FOLDER` also collects the whole tree *before* returning anything, so
creating folders during execution cannot alter what is still being walked.

### Exclusions live in one object

`ScanFilter` answers `allows_dir` / `allows_file`, comparing case-insensitively
because Windows does. Category folder names are added to the exclusion set at
call time, which is what makes a second run a no-op rather than a reshuffle.

### Duplicates: size buckets before hashing

Files are grouped by size first; only a size collision triggers SHA-256. Most
files are never read.

Files that OneDrive keeps in the cloud are detected through the Windows file
attributes (`OFFLINE`, `RECALL_ON_OPEN`, `RECALL_ON_DATA_ACCESS`) and skipped by
the duplicate check. Hashing them would force a download, and tidying a folder
should not consume someone's disk or data plan.

Empty files are never duplicates of each other. They are identical by
definition, and treating them as copies would quarantine intentional markers.

There is deliberately **no delete policy**. `DuplicatePolicy` offers
`QUARANTINE`, `REPORT` and `IGNORE`. Quarantine keeps the decision reversible.

### Destinations are reserved as the plan is built

`unique_path` checks both the disk and a `claimed` set of destinations already
assigned in the current plan. Without the set, two files can be assigned the
same destination and the second move overwrites the first — for example when
`informe.pdf` sidesteps an existing file by becoming `informe_1.pdf`, which is
the name a second file already wanted. See
`test_conflict_resolution_cannot_assign_the_same_destination_twice`.

### Project detection looks only at the top level

`ProjectDetector.inspect` examines a folder's own first level: marker files, or
its own source files. Looking deeper would make any folder that *contains* a
project look like one, and the mover would take too much.

Two rules follow from that:

* A folder that isn't a project is searched one level deeper, so a container of
  recordings and spreadsheets with one game folder inside reports the game.
* If that search finds several sibling projects, the parent is reported as a
  monorepo, because separating the pieces would break the paths between them.

### Moves prefer a rename, and report residue honestly

`move_directory` tries `os.rename` first — instantaneous on the same volume, no
bytes copied. Only if that fails does it fall back to copy-then-delete.

The delete step clears the read-only attribute and retries, because
`shutil.rmtree` fails outright on the read-only files inside `.git/objects` and
many dependency trees. If something still holds a lock, the function returns
`False` and the mover reports `COPIED_NOT_REMOVED` rather than `ERROR`: the files
did arrive, and calling that a failure would send the user looking for data that
is already safe.

### Configuration has no side effects

Loading settings used to call `logger.add()`, so constructing two config objects
duplicated every log line. `settings` now only reads; `logging_setup.setup_logging`
is called once by `cli.main`.

### No third-party dependencies

The tool previously required `click`, `loguru`, `python-dotenv` and `pathlib2`
(the last unused, and dead on Python 3). It now uses `argparse`, `logging` and a
ten-line `.env` reader.

This is not minimalism for its own sake: on the machine this tool was written
for, `pip` sits behind a TLS-intercepting proxy and fails without
`--trusted-host`. "Clone and run" is the difference between a working utility and
one that needs debugging before first use.

## Adding a category

Edit the rules JSON, or `DEFAULT_RULES` in `rules.py`:

```json
{ "cad": { "folder": "CAD", "extensions": [".dwg", ".dxf"] } }
```

Nothing else changes. `Ruleset` builds the index, `folders` automatically covers
the new name for exclusion, and idempotency follows.

## Adding a command

1. Write a `cmd_*(args, settings) -> int` function in `cli.py`.
2. Register a subparser in `build_parser` and `set_defaults(handler=...)`.
3. Put real logic in a domain module, not in the command.

Commands should assemble and print. If a command grows a decision, that decision
belongs in `planner` or `projects`, where it can be tested without a filesystem.

## Testing

```bash
python -m pytest tests -q
```

`tests/helpers.py` writes files whose content defaults to their own filename, so
two different files are never accidentally byte-identical — with a fixed content
every fixture became a duplicate and the duplicate logic silently ate half of
each test's files.

Tests assert on the resulting file tree (`helpers.tree`) rather than on log
output, so a refactor that keeps behaviour keeps the tests green.

# Quickstart

Nothing to install. Python 3.9+ and the repository are enough.

```bash
git clone https://github.com/Criscarr26/folder-organizer.git
cd folder-organizer
python main.py --help
```

## 1. Look before you touch

```bash
python main.py analyze --path "C:/Users/me/Downloads"
```

Groups the files by category with counts and sizes. Moves nothing, ever.

## 2. Simulate

```bash
python main.py organize --path "C:/Users/me/Downloads" --dry-run
```

Prints the exact plan: which file goes to which folder, which are duplicates,
which are already in place. Still moves nothing.

## 3. Apply

```bash
python main.py organize --path "C:/Users/me/Downloads"
```

Shows the plan and asks for confirmation. Add `--yes` to skip the prompt in a
script. In a non-interactive shell without `--yes` the command refuses and exits
without moving anything.

Add `--report run.md` to get the full list in a file — the console output is
truncated for readability, the report is not.

## Common tasks

### Tidy coursework by subject

Each subject folder gets its own `Documentos/`, `Imágenes/`… and the semester
hierarchy stays intact:

```bash
python main.py organize --path "D:/University" --mode per-folder --dry-run
```

### Find duplicates without moving them

```bash
python main.py organize --path "D:/Photos" --duplicates report --dry-run
```

### Skip the duplicate check entirely

Fastest option, and it reads no file contents at all:

```bash
python main.py organize --path "D:/Photos" --duplicates ignore --yes
```

### Gather scattered projects

Check what would be detected first:

```bash
python main.py find-projects --path "C:/Users/me" --path "D:/work"
```

Then move them:

```bash
python main.py move-projects --path "C:/Users/me" --destination "D:/Github repository" --dry-run
```

To move specific folders and let detection add nothing:

```bash
python main.py move-projects --project "C:/Users/me/my-api" --project "D:/games/my-game" --destination "D:/Github repository" --yes
```

### Custom rules

```bash
python main.py init-config --config config/rules.json
```

Edit `config/rules.json`, then:

```bash
python main.py organize --path "D:/data" --config config/rules.json --dry-run
```

### When a category name already exists as a folder

At a OneDrive root, `Documentos` and `Imágenes` are real folders. Use the ruleset
that nests every category under one container so nothing collides:

```bash
python main.py organize --path "C:/Users/me/OneDrive" --config config/rules-contenedor.json --dry-run
```

## Result

```
Downloads/
├── Documentos/
│   ├── invoice.pdf
│   └── notes.txt
├── Imágenes/
│   └── holiday.jpg
├── Hojas de cálculo/
│   └── budget.xlsx
├── Instaladores/
│   └── setup.exe
├── Otros/
│   └── unknown.xyz
└── _Duplicados/
    └── invoice-copy.pdf
```

## Safety notes

- Duplicates are moved to `_Duplicados`, never deleted.
- Running the same command twice does nothing the second time.
- `loose` mode (the default) never enters subfolders, so it cannot flatten a
  hierarchy.
- `desktop.ini`, shortcuts, dotfiles, `.git`, `node_modules`, virtualenvs and any
  folder named `Github repository` are left alone.
- Cloud-only OneDrive files are moved but never read, so nothing gets downloaded.

## Troubleshooting

**"Hay que confirmar para continuar, pero la entrada no es interactiva."**
You're running from a script or a non-TTY shell. Add `--yes`, or use `--dry-run`
to inspect the plan first.

**"la ruta destino supera 255 caracteres"**
Windows path limit. Organize a folder closer to the drive root, or shorten the
category name in your rules file.

**A file didn't move.** Run with `--verbose`. Protected files (`desktop.ini`,
`.lnk`, `.url`, dotfiles) and excluded folders are skipped by design; the log
says which.

## Next

- [README.md](../README.md) — full command reference.
- [ARCHITECTURE.md](./ARCHITECTURE.md) — how the code is split, and why.

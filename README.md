# 📁 Automatic Folder Organizer

A smart, automated folder organizer written in Python that classifies and organizes files automatically based on their type, extension and other properties.

## ✨ Features

- 🎯 **Automatic classification**: Sorts files by type (images, documents, videos, audio, etc.)
- 📊 **File analysis**: Analyzes folders without moving anything (`--dry-run` mode)
- ⚙️ **Customizable**: Create your own organization rules in JSON
- 🔍 **Smart detection**: Detects name conflicts and resolves them automatically
- 📝 **Detailed logging**: Full record of every operation
- 🖥️ **Intuitive CLI**: Easy-to-use command-line interface

## 🚀 Installation

### Requirements
- Python 3.11+
- pip

### Installation steps

1. **Clone the repository**
```bash
git clone <repository-url>
cd FolderOrganizer
```

2. **Create a virtual environment**
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create configuration (optional)**
```bash
python main.py init-config
```

## 💡 Quick usage

### Organize the current folder
```bash
python main.py organize
```

### Organize a specific folder
```bash
python main.py organize --path /path/to/folder
```

### Simulation mode (without moving files)
```bash
python main.py organize --path /path --dry-run
```

### Analyze files without moving
```bash
python main.py analyze --path /path
```

## 📋 Available commands

### `organize`
Organizes files into folders by type.

**Options:**
- `--path PATH`: Path to organize (default: current folder)
- `--config CONFIG`: Custom JSON configuration file
- `--dry-run`: Simulate without moving files
- `--verbose`: Verbose mode for more detail

**Example:**
```bash
python main.py organize --path ~/Downloads --dry-run
```

### `analyze`
Analyzes a folder and shows how the files would be organized.

**Options:**
- `--path PATH`: Folder to analyze (default: current folder)
- `--config CONFIG`: Configuration file to use

**Example:**
```bash
python main.py analyze --path ~/Downloads
```

### `init-config`
Creates a default configuration file.

**Options:**
- `--config PATH`: Output path for the configuration file

**Example:**
```bash
python main.py init-config --config ./config/my-rules.json
```

## 🔧 Custom configuration

### Configuration file structure

Create a `config/rules.json` file:

```json
{
  "images": {
    "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "folder": "Images"
  },
  "documents": {
    "extensions": [".pdf", ".doc", ".docx", ".txt", ".xlsx"],
    "folder": "Documents"
  },
  "videos": {
    "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "folder": "Videos"
  }
}
```

### Environment variables

Copy `.env.example` to `.env` and customize:

```bash
LOG_LEVEL=INFO
LOG_FILE=organizer.log
CONFIG_FILE=config/rules.json
WATCH_FOLDER=./downloads
AUTO_ORGANIZE=false
```

## 📚 Module documentation

### `config.py`
Manages the application configuration from environment variables and JSON files.

**Main classes:**
- `ConfigManager`: Loads and manages the configuration

### `classifier.py`
Classifies files by type and extension.

**Main classes:**
- `FileClassifier`: Classifies files individually and in batches

### `organizer.py`
Orchestrates the organization of files into folders.

**Main classes:**
- `FolderOrganizer`: Organizes files and keeps statistics

### `cli.py`
Provides the command-line interface.

**Main functions:**
- `organize()`: Main organization command
- `analyze()`: Analyzes files without moving them
- `init_config()`: Initializes the configuration file

## 🧪 Tests

Run the unit tests:

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=src
```

## 📝 Project structure

```
.
├── src/
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── classifier.py    # File classification
│   ├── organizer.py     # Orchestration
│   └── cli.py           # Command-line interface
├── tests/
│   ├── __init__.py
│   ├── test_classifier.py
│   └── test_config.py
├── config/
│   └── rules.json.example
├── docs/
├── main.py              # Entry point
├── requirements.txt
├── .env.example
└── README.md
```

## 🔄 How it works

```
User runs a CLI command
         ↓
ConfigManager loads configuration
         ↓
FileClassifier classifies files
         ↓
FolderOrganizer organizes files
         ↓
Logs and statistics
```

## 🐛 Usage examples

### Case 1: Organize the downloads folder
```bash
python main.py organize --path ~/Downloads
```

### Case 2: Preview before organizing
```bash
python main.py analyze --path ~/Downloads
python main.py organize --path ~/Downloads --dry-run
python main.py organize --path ~/Downloads
```

### Case 3: Use a custom configuration
```bash
python main.py init-config --config config/custom-rules.json
# Edit config/custom-rules.json
python main.py organize --path ~/Downloads --config config/custom-rules.json
```

## 🔐 Safety

- Duplicate files are renamed automatically
- `--dry-run` mode to preview changes
- Detailed logging of every operation
- Nothing is deleted, only reorganized

## 📦 Dependencies

- **click**: CLI framework
- **loguru**: Logging system
- **python-dotenv**: Environment-variable management
- **pathlib2**: Path manipulation

## 📄 License

This project is under the MIT license.

## 👤 Author

Built as a Python automation tool.

## 🤝 Contributing

Contributions are welcome. Please:

1. Fork the project
2. Create a branch for your feature (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📧 Support

To report issues or suggestions, open an issue in the repository.

---

⭐ If it was useful, don't forget to give it a star! ⭐

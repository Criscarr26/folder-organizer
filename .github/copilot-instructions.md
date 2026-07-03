<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Automatización con Python - Organizador Automático de Carpetas

- [x] Verify that the copilot-instructions.md file in the .github directory is created.

- [x] Clarify Project Requirements
  - Project Type: Python Application ✅
  - Language: Python 3.11+ ✅
  - Frameworks: click, pathlib, python-dotenv, loguru ✅
  - Purpose: Automatic folder organization system ✅

- [x] Scaffold the Project
  - Create project structure with main modules ✅
  - Initialize Python virtual environment (Python 3.11 disponible)
  - Create requirements.txt for dependencies ✅
  - Set up configuration system ✅

- [x] Customize the Project
  - Implement core folder organizer module ✅
  - Add file classification system ✅
  - Create rule engine for organization ✅
  - Add configuration management ✅

- [x] Install Required Extensions
  - Python extension (ms-python.python) ✅
  - Pylance extension (ms-python.vscode-pylance) ✅

- [x] Compile the Project
  - Install dependencies (ver nota de SSL abajo)
  - Validate Python syntax ✅
  - Run linting checks

- [x] Create and Run Task
  - Set up run task for main application ✅
  - Set up test task ✅

- [x] Launch the Project
  - Demo basic functionality

- [x] Ensure Documentation is Complete
  - Update README.md with usage instructions ✅
  - Document API and configuration ✅

**Nota sobre SSL:** Existe un problema de certificado SSL con PyPI en este sistema. Para instalar las dependencias, ejecuta:
```
python -m pip install click python-dotenv loguru pytest
```

Usuarios alternativos pueden necesitar configurar certificados SSL en Windows o usar un espejo de PyPI alternativo.

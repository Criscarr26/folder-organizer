# Guía de Contribución - Organizador Automático de Carpetas

¡Gracias por tu interés en contribuir a este proyecto! Este documento te proporciona todo lo necesario para comenzar a contribuir de forma efectiva.

---

## 🎯 Bienvenida a Contribuidores

Somos una comunidad abierta e inclusiva que valora las contribuciones de todos los niveles de experiencia. Ya sea que desees:
- 🐛 Reportar bugs
- ✨ Proponer nuevas características
- 📚 Mejorar documentación
- 🧪 Escribir tests
- 🔧 Refactorizar código
- 🌍 Traducir contenido

**¡Tu contribución es bienvenida!** Antes de comenzar, por favor revisa nuestro [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para entender nuestros estándares comunitarios.

---

## 🚀 Configuración del Ambiente de Desarrollo

### Requisitos Previos
- Python 3.11 o superior
- Git
- Acceso a una terminal/cmd

### Paso 1: Fork y Clone del Repositorio

```bash
# Fork el repositorio en GitHub
# Luego clona tu fork
git clone https://github.com/TU_USUARIO/Organizador-Automatico-Carpetas.git
cd "Organizador automático de carpetas"

# Agrega el upstream original
git remote add upstream https://github.com/USUARIO_ORIGINAL/Organizador-Automatico-Carpetas.git
```

### Paso 2: Crear Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar Dependencias

```bash
# Instalar dependencias del proyecto
pip install --upgrade pip
pip install -r requirements.txt

# Instalar dependencias de desarrollo (incluye pytest para tests)
pip install -e .
```

### Paso 4: Verificar la Instalación

```bash
# Ejecutar tests
pytest tests/ -v

# Ejecutar demo
python demo.py

# Verificar CLI
python main.py --help
```

---

## 📁 Estructura del Proyecto

Para entender mejor dónde trabajar, consulta [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md). Resumen rápido:

```
src/
├── config.py         # Gestión de configuración
├── classifier.py     # Clasificador de archivos
├── organizer.py      # Orquestador principal
└── cli.py            # Interfaz de línea de comandos

tests/
├── test_config.py       # Tests de configuración
└── test_classifier.py   # Tests de clasificación

docs/
├── FEATURES.md       # Características principales
├── QUICKSTART.md     # Inicio rápido
└── DEVELOPMENT.md    # Detalles técnicos
```

**Módulos principales:**
- **config.py**: Carga y gestiona reglas de organización desde JSON
- **classifier.py**: Clasifica archivos según extensión y reglas
- **organizer.py**: Orquesta la organización de carpetas
- **cli.py**: Proporciona comandos como `analyze`, `organize`, `init-config`

---

## 🎨 Guía de Estilo - PEP 8

Seguimos [PEP 8](https://www.python.org/dev/peps/pep-0008/) con estas convenciones:

### Nombres y Formato
```python
# ✅ Correcto
class FileClassifier:
    def classify_file(self, file_path: str) -> str:
        """Clasifica un archivo según su extensión."""
        pass

# ❌ Incorrecto
class file_classifier:
    def classifyFile(self, filePath):
        pass
```

### Type Hints
```python
# ✅ Usar type hints
def organize(
    folder_path: str,
    config: dict,
    dry_run: bool = False
) -> dict:
    pass

# ❌ Sin type hints
def organize(folder_path, config, dry_run=False):
    pass
```

### Docstrings
```python
def classify_file(self, file_path: str) -> str:
    """Clasifica un archivo según su extensión.
    
    Args:
        file_path: Ruta completa del archivo
        
    Returns:
        Categoría del archivo como string
        
    Raises:
        ValueError: Si el archivo no existe
    """
    pass
```

### Límite de Línea
- Máximo 88 caracteres por línea
- Usa f-strings para interpolación: `f"Path: {path}"`

### Imports
```python
# ✅ Orden correcto
import os
import sys
from pathlib import Path
from typing import Dict, List

import click
from loguru import logger
```

---

## 🧪 Escribir y Correr Tests

### Estructura de Tests

```bash
pytest tests/ -v              # Correr todos los tests con verbose
pytest tests/test_config.py   # Correr test específico
pytest -k "test_classify"     # Correr tests que coincidan
pytest --cov=src              # Ver cobertura de código
```

### Escribir un Nuevo Test

```python
# tests/test_classifier.py
import pytest
from src.classifier import FileClassifier

@pytest.fixture
def classifier():
    """Fixture para crear instancia del clasificador."""
    return FileClassifier()

def test_classify_image_file(classifier):
    """Test: clasifica correctamente archivos de imagen."""
    result = classifier.classify("photo.jpg")
    assert result == "Imágenes"

def test_classify_unknown_extension(classifier):
    """Test: devuelve 'Otros' para extensiones desconocidas."""
    result = classifier.classify("document.xyz")
    assert result == "Otros"

@pytest.mark.parametrize("ext,expected", [
    (".pdf", "Documentos"),
    (".xlsx", "Documentos"),
    (".mp3", "Audio"),
])
def test_classify_multiple_files(classifier, ext, expected):
    """Test: clasifica correctamente múltiples extensiones."""
    result = classifier.classify(f"file{ext}")
    assert result == expected
```

### Ejecutar con Cobertura

```bash
pytest --cov=src --cov-report=html
# Abre htmlcov/index.html para ver resultados
```

---

## 🔄 Proceso de Pull Requests

### 1. Crear una Rama

```bash
# Actualiza main primero
git fetch upstream
git rebase upstream/main

# Crea rama con nombre descriptivo
git checkout -b feature/add-cloud-storage
# o
git checkout -b fix/config-parsing-bug
# o
git checkout -b docs/update-readme
```

**Naming conventions:**
- `feature/descripcion` - Nueva funcionalidad
- `fix/descripcion` - Corrección de bug
- `docs/descripcion` - Cambios en documentación
- `refactor/descripcion` - Refactorización
- `test/descripcion` - Nuevos tests

### 2. Hacer Cambios

```bash
# Edita archivos
# Prueba localmente
pytest tests/ -v
python main.py --help

# Commit cuando esté listo
git add .
git commit -m "Fix: resolver issue de clasificación de PDFs"
```

### 3. Push y Crear PR

```bash
# Push a tu fork
git push origin feature/add-cloud-storage

# Ve a GitHub y crea un Pull Request
# Completa el template del PR
```

### 4. Revisión del Código

- Al menos una aprobación requerida
- CI checks deben pasar
- Discussiones constructivas

### 5. Merge

Una vez aprobado, el mantenedor mergeará el PR.

```bash
# Sincronizar tu rama local
git fetch upstream
git rebase upstream/main
```

---

## 💬 Commits y Mensajes

### Formato de Mensajes

Usa el formato: `<tipo>: <descripción>`

```bash
# ✅ Correcto
git commit -m "feat: agregar soporte para archivos .zip"
git commit -m "fix: resolver error de permisos en Windows"
git commit -m "docs: actualizar guía de instalación"
git commit -m "test: agregar tests para clasificador de audio"
git commit -m "refactor: simplificar lógica de organización"

# ❌ Incorrecto
git commit -m "fixed bug"
git commit -m "update"
git commit -m "WIP"
```

### Tipos de Commits

| Tipo | Descripción |
|------|-------------|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `test` | Agregar o mejorar tests |
| `refactor` | Cambios sin afectar funcionalidad |
| `perf` | Mejoras de rendimiento |
| `style` | Formato, espacios en blanco |
| `ci` | Cambios en CI/CD |

### Buen Mensaje de Commit

```
feat: agregar soporte para monitoreo automático de carpetas

- Implementa watcher de carpetas con watchdog
- Agrega configuración de intervalo de escaneo
- Incluye tests para watcher
- Actualiza documentación

Resuelve #123
```

---

## ✅ Checklist Antes de PR

Antes de enviar un Pull Request, asegúrate de:

- [ ] **Tests**: Todos los tests pasan `pytest tests/ -v`
- [ ] **Cobertura**: Nuevo código tiene tests (>80% cobertura)
- [ ] **Estilo**: Código sigue PEP 8 `pylint src/`
- [ ] **Type Hints**: Todas las funciones tienen type hints
- [ ] **Docstrings**: Funciones públicas tienen docstrings
- [ ] **Imports**: Imports están organizados y no hay unused
- [ ] **Compatibilidad**: Funciona en Windows, macOS y Linux
- [ ] **Dependencias**: No agrega dependencias innecesarias
- [ ] **Changelog**: Actualiza `CHANGELOG.md` si es necesario
- [ ] **Documentación**: Actualiza docs si cambia comportamiento
- [ ] **Log**: Usa `logger` en lugar de `print()` para mensajes
- [ ] **Errores**: Maneja excepciones apropiadamente
- [ ] **Performance**: No introduce regresiones de rendimiento

### Script de Validación Rápida

```bash
#!/bin/bash
# Ejecuta esto antes de hacer push

echo "🧪 Ejecutando tests..."
pytest tests/ -v --cov=src || exit 1

echo "🎨 Verificando estilo..."
pylint src/ || exit 1

echo "📝 Verificando type hints..."
mypy src/ || exit 1

echo "✅ ¡Todo listo!"
```

---

## 💡 Ideas para Contribuciones

### 🎯 Características Solicitadas

- [ ] **Monitoreo automático** - Watch mode para carpetas
- [ ] **Sincronización en la nube** - Integración con Google Drive/OneDrive
- [ ] **Interfaz gráfica** - Dashboard web con FastAPI
- [ ] **Estadísticas avanzadas** - Gráficos de organización
- [ ] **Copias de seguridad** - Backup antes de reorganizar
- [ ] **Perfiles de usuario** - Múltiples configuraciones

### 🔧 Mejoras Técnicas

- [ ] Optimizar rendimiento para carpetas grandes
- [ ] Agregar logging estructurado
- [ ] Mejorar manejo de caracteres especiales
- [ ] Soporte para archivos duplicados
- [ ] Undo/Redo de operaciones
- [ ] Dry-run mejorado

### 📚 Documentación

- [ ] Traducir a otros idiomas
- [ ] Video tutoriales
- [ ] Más ejemplos en `docs/`
- [ ] FAQ
- [ ] Troubleshooting guide

### 🐛 Bugs Conocidos

Revisa los [Issues](https://github.com/USUARIO/Organizador-Automatico-Carpetas/issues) con etiqueta `bug`.

---

## 🤝 Normas de Comunidad

- **Sé respetuoso**: Trata a todos con consideración
- **Sé constructivo**: Crítica con soluciones
- **Sé inclusivo**: Bienvenido a todos
- **Sé responsable**: Revisa tu código antes de PR

Consulta [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) para más detalles.

---

## ❓ Preguntas?

- 📖 Lee la [Documentación](docs/)
- 🔍 Busca en [Issues existentes](https://github.com/USUARIO/Organizador-Automatico-Carpetas/issues)
- 💬 Abre una [Discusión](https://github.com/USUARIO/Organizador-Automatico-Carpetas/discussions)
- 📧 Contacta al mantenedor

---

## 📋 Recursos Útiles

- [PEP 8 - Python Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [pytest Documentation](https://docs.pytest.org/)
- [Git Workflow](https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Estructura del proyecto

---

**¡Gracias por contribuir!** 🚀

Cada contribución, sin importar su tamaño, ayuda a mejorar el proyecto. Estamos emocionados de ver tu código.

**Happy coding!** 💻

# Flujo de Trabajo de Desarrollo

## Configuración del Entorno de Desarrollo

### 1. Clonar repositorio
```bash
git clone <url-del-repo>
cd FolderOrganizer
```

### 2. Crear entorno virtual
```bash
python -m venv venv

# Activar en Windows:
venv\Scripts\activate

# Activar en Linux/Mac:
source venv/bin/activate
```

### 3. Instalar dependencias de desarrollo
```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

## Estructura de Carpetas

```
FolderOrganizer/
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   └── tasks.json
├── src/
│   ├── __init__.py
│   ├── config.py              # Gestión de configuración
│   ├── classifier.py          # Clasificación de archivos
│   ├── organizer.py           # Orquestación
│   └── cli.py                 # Interfaz CLI
├── tests/
│   ├── __init__.py
│   ├── test_config.py         # Tests de configuración
│   └── test_classifier.py     # Tests de clasificación
├── config/
│   └── rules.json.example     # Ejemplo de reglas
├── docs/
│   ├── FEATURES.md            # Características
│   ├── QUICKSTART.md          # Inicio rápido
│   └── DEVELOPMENT.md         # Este archivo
├── main.py                    # Punto de entrada
├── demo.py                    # Script de demostración
├── requirements.txt           # Dependencias
├── .env.example               # Variables de entorno
├── .gitignore                 # Git ignore
└── README.md                  # Documentación principal
```

## Comandos Útiles

### Ejecutar tests
```bash
pytest tests/
pytest tests/ -v          # Verbose
pytest tests/ --cov=src   # Con cobertura
```

### Validar código
```bash
flake8 src/ main.py demo.py
black src/ main.py demo.py
```

### Ejecutar aplicación
```bash
python main.py organize --help
python main.py analyze --path .
python demo.py
```

### Limpiar archivos generados
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf build/ dist/ *.egg-info/
```

## Estándares de Código

### Estilo PEP 8
- Usar 4 espacios de indentación
- Líneas máximo 88 caracteres
- Nombres en snake_case para variables y funciones
- Nombres en PascalCase para clases

### Docstrings
```python
def mi_funcion(param1: str, param2: int) -> str:
    """
    Descripción breve de la función.
    
    Descripción más larga si es necesario.
    
    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2
        
    Returns:
        Descripción del retorno
        
    Raises:
        ValueError: Cuándo se lanza esta excepción
    """
    pass
```

### Type Hints
```python
from typing import Dict, List, Optional

def procesar(items: List[str]) -> Dict[str, int]:
    """Procesa una lista de items"""
    pass
```

## Flujo de Git

### Rama main
- Rama principal, estable
- Solo cambios aprobados mediante PR

### Rama develop
- Rama de desarrollo
- Base para nuevas features

### Crear nueva feature
```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-de-feature

# Desarrollar...

git add .
git commit -m "feat: descripción del cambio"
git push origin feature/nombre-de-feature

# Crear Pull Request en GitHub
```

### Convención de Commits
```
feat: nueva característica
fix: corrección de bug
docs: cambios de documentación
style: cambios de formato
refactor: refactorización de código
test: agregación de tests
chore: cambios de configuración
```

## Testing

### Ejecutar tests
```bash
pytest tests/
```

### Tests con cobertura
```bash
pytest tests/ --cov=src --cov-report=html
```

### Tests específicos
```bash
pytest tests/test_classifier.py -v
pytest tests/test_config.py::test_default_rules -v
```

### Escribir nuevos tests
```python
import pytest
from src.classifier import FileClassifier

@pytest.fixture
def classifier():
    rules = {...}
    return FileClassifier(rules)

def test_mi_funcion(classifier):
    result = classifier.classify_batch(Path('.'))
    assert len(result) > 0
```

## Documentación

### Actualizar README
- Cambios significativos
- Nuevas características
- Cambios de API

### Actualizar FEATURES.md
- Nueva funcionalidad
- Casos de uso nuevos

### Actualizar QUICKSTART.md
- Cambios en comandos
- Nuevas opciones

## Release

### Versioning (Semantic Versioning)
- MAJOR.MINOR.PATCH
- MAJOR: Cambios incompatibles
- MINOR: Nueva funcionalidad compatible
- PATCH: Correcciones de bugs

### Crear release
```bash
# Actualizar versión en src/__init__.py
# Actualizar CHANGELOG

git tag -a v1.0.0 -m "Versión 1.0.0"
git push origin v1.0.0
```

## Troubleshooting

### Tests fallan
1. Verificar instalación de dependencias
2. Verificar versión de Python (3.11+)
3. Limpiar __pycache__

### Importes no funcionan
1. Verificar ruta PYTHONPATH
2. Verificar __init__.py en carpetas
3. Ejecutar desde directorio raíz

### Problemas de SSL
Ver [README.md](../README.md#ssl)

## Contacto y Contribuciones

Para contribuir:
1. Fork el proyecto
2. Crea una rama
3. Realiza cambios
4. Tests deben pasar
5. Envía PR

¡Gracias por contribuir! 🙏

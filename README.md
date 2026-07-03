# 📁 Organizador Automático de Carpetas

Un organizador de carpetas inteligente y automatizado escrito en Python que clasifica y organiza archivos automáticamente según su tipo, extensión y otras propiedades.

## ✨ Características

- 🎯 **Clasificación Automática**: Clasifica archivos por tipo (imágenes, documentos, videos, audio, etc.)
- 📊 **Análisis de Archivos**: Analiza carpetas sin mover nada (modo `--dry-run`)
- ⚙️ **Personalizable**: Crea tus propias reglas de organización en JSON
- 🔍 **Detección Inteligente**: Detecta conflictos de nombres y los resuelve automáticamente
- 📝 **Logging Detallado**: Registro completo de todas las operaciones
- 🖥️ **CLI Intuitiva**: Interfaz de línea de comandos fácil de usar

## 🚀 Instalación

### Requisitos
- Python 3.11+
- pip

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone <url-del-repositorio>
cd FolderOrganizer
```

2. **Crear entorno virtual**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Crear configuración (opcional)**
```bash
python main.py init-config
```

## 💡 Uso Rápido

### Organizar carpeta actual
```bash
python main.py organize
```

### Organizar carpeta específica
```bash
python main.py organize --path /ruta/a/carpeta
```

### Modo simulación (sin mover archivos)
```bash
python main.py organize --path /ruta --dry-run
```

### Analizar archivos sin mover
```bash
python main.py analyze --path /ruta
```

## 📋 Comandos Disponibles

### `organize`
Organiza los archivos en carpetas según su tipo.

**Opciones:**
- `--path PATH`: Ruta a organizar (por defecto: carpeta actual)
- `--config CONFIG`: Archivo de configuración JSON personalizado
- `--dry-run`: Simular sin mover archivos
- `--verbose`: Modo verbose para más detalles

**Ejemplo:**
```bash
python main.py organize --path ~/Downloads --dry-run
```

### `analyze`
Analiza una carpeta y muestra cómo se organizarían los archivos.

**Opciones:**
- `--path PATH`: Carpeta a analizar (por defecto: carpeta actual)
- `--config CONFIG`: Archivo de configuración a usar

**Ejemplo:**
```bash
python main.py analyze --path ~/Downloads
```

### `init-config`
Crea un archivo de configuración predeterminado.

**Opciones:**
- `--config PATH`: Ruta de salida para el archivo de configuración

**Ejemplo:**
```bash
python main.py init-config --config ./config/my-rules.json
```

## 🔧 Configuración Personalizada

### Estructura del archivo de configuración

Crea un archivo `config/rules.json`:

```json
{
  "images": {
    "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
    "folder": "Imágenes"
  },
  "documents": {
    "extensions": [".pdf", ".doc", ".docx", ".txt", ".xlsx"],
    "folder": "Documentos"
  },
  "videos": {
    "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
    "folder": "Videos"
  }
}
```

### Variables de entorno

Copia `.env.example` a `.env` y personaliza:

```bash
LOG_LEVEL=INFO
LOG_FILE=organizer.log
CONFIG_FILE=config/rules.json
WATCH_FOLDER=./downloads
AUTO_ORGANIZE=false
```

## 📚 Documentación de Módulos

### `config.py`
Gestiona la configuración del aplicativo desde variables de entorno y archivos JSON.

**Clases principales:**
- `ConfigManager`: Carga y gestiona la configuración

### `classifier.py`
Clasifica archivos según su tipo y extensión.

**Clases principales:**
- `FileClassifier`: Clasifica archivos individuales y en lotes

### `organizer.py`
Orquesta la organización de archivos en carpetas.

**Clases principales:**
- `FolderOrganizer`: Organiza archivos y mantiene estadísticas

### `cli.py`
Proporciona la interfaz de línea de comandos.

**Funciones principales:**
- `organize()`: Comando principal de organización
- `analyze()`: Analiza archivos sin moverlos
- `init_config()`: Inicializa archivo de configuración

## 🧪 Pruebas

Ejecutar pruebas unitarias:

```bash
pytest tests/
```

Con cobertura:

```bash
pytest tests/ --cov=src
```

## 📝 Estructura del Proyecto

```
.
├── src/
│   ├── __init__.py
│   ├── config.py        # Gestión de configuración
│   ├── classifier.py    # Clasificación de archivos
│   ├── organizer.py     # Orquestación
│   └── cli.py           # Interfaz de línea de comandos
├── tests/
│   ├── __init__.py
│   ├── test_classifier.py
│   └── test_config.py
├── config/
│   └── rules.json.example
├── docs/
├── main.py              # Punto de entrada
├── requirements.txt
├── .env.example
└── README.md
```

## 🔄 Flujo de Funcionamiento

```
Usuario ejecuta comando CLI
         ↓
ConfigManager carga configuración
         ↓
FileClassifier clasifica archivos
         ↓
FolderOrganizer organiza archivos
         ↓
Logs y estadísticas
```

## 🐛 Ejemplos de Uso

### Caso 1: Organizar carpeta de descargas
```bash
python main.py organize --path ~/Downloads
```

### Caso 2: Vista previa antes de organizar
```bash
python main.py analyze --path ~/Downloads
python main.py organize --path ~/Downloads --dry-run
python main.py organize --path ~/Downloads
```

### Caso 3: Usar configuración personalizada
```bash
python main.py init-config --config config/custom-rules.json
# Editar config/custom-rules.json
python main.py organize --path ~/Downloads --config config/custom-rules.json
```

## 🔐 Seguridad

- Los archivos duplicados se renombran automáticamente
- Modo `--dry-run` para previsualizar cambios
- Logging detallado de todas las operaciones
- No se elimina nada, solo se reorganiza

## 📦 Dependencias

- **click**: CLI framework
- **loguru**: Sistema de logging
- **python-dotenv**: Gestión de variables de entorno
- **pathlib2**: Manipulación de rutas

## 📄 Licencia

Este proyecto está bajo licencia MIT.

## 👤 Autor

Creado como herramienta de automatización con Python.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Soporte

Para reportar issues o sugerencias, abre un issue en el repositorio.

---

⭐ Si te fue útil, ¡no olvides darle una estrella! ⭐

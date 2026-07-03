# 🎯 Guía de Características

## Características Principales

### 1. **Clasificación Automática de Archivos**
El sistema clasifica automáticamente archivos basándose en su extensión:
- 📷 Imágenes (`.jpg`, `.png`, `.gif`, `.bmp`, `.webp`, `.svg`)
- 📄 Documentos (`.pdf`, `.doc`, `.docx`, `.txt`, `.xlsx`, `.pptx`)
- 🎬 Videos (`.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`)
- 🎵 Audio (`.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`)
- 📦 Archivos comprimidos (`.zip`, `.rar`, `.7z`, `.tar`)
- 💻 Código (`.py`, `.js`, `.ts`, `.java`, `.cpp`)
- ⚙️ Ejecutables (`.exe`, `.msi`, `.app`, `.dmg`)

### 2. **Modo Simulación (Dry-Run)**
Previsualiza qué haría el organizador sin mover nada:
```bash
python main.py organize --path ~/Downloads --dry-run
```

### 3. **Análisis de Carpetas**
Analiza una carpeta y muestra un resumen de cómo se organizarían los archivos:
```bash
python main.py analyze --path ~/Downloads
```

### 4. **Configuración Personalizable**
Crea tus propias reglas de organización en JSON:
```json
{
  "tu_categoria": {
    "extensions": [".ext1", ".ext2"],
    "folder": "Tu Carpeta"
  }
}
```

### 5. **Manejo Inteligente de Conflictos**
Detecta automáticamente cuando un archivo ya existe y lo renombra:
- `documento.pdf` → `documento_1.pdf` → `documento_2.pdf`

### 6. **Sistema de Logging Completo**
Registra todas las operaciones en un archivo de log:
```
organizer.log: Contiene el historial completo de operaciones
```

### 7. **Interfaz CLI Intuitiva**
Interfaz fácil de usar basada en Click:
```bash
python main.py --help
```

## Módulos Principales

### `config.py` - Gestión de Configuración
```python
from src.config import ConfigManager

config = ConfigManager()
rules = config.load_rules()
```

**Responsabilidades:**
- Carga configuración desde variables de entorno
- Carga reglas desde archivos JSON
- Proporciona reglas por defecto

### `classifier.py` - Clasificador de Archivos
```python
from src.classifier import FileClassifier

classifier = FileClassifier(rules)
classification = classifier.classify(file_path)
```

**Responsabilidades:**
- Clasifica archivos individuales
- Clasifica lotes de archivos
- Construye mapa de extensiones

### `organizer.py` - Orquestador Principal
```python
from src.organizer import FolderOrganizer

organizer = FolderOrganizer(classifier, base_path)
stats = organizer.organize(dry_run=False)
```

**Responsabilidades:**
- Organiza archivos en carpetas
- Maneja conflictos de nombres
- Proporciona estadísticas

### `cli.py` - Interfaz de Línea de Comandos
**Comandos disponibles:**
- `organize`: Organiza archivos
- `analyze`: Analiza sin mover
- `init-config`: Crea configuración

## Flujo de Ejecución

```
Usuario ejecuta comando
    ↓
CLI (cli.py) parse argumentos
    ↓
ConfigManager carga configuración
    ↓
FileClassifier clasifica archivos
    ↓
FolderOrganizer ejecuta organización
    ↓
Logging y estadísticas
    ↓
Resultado para el usuario
```

## Casos de Uso

### Caso 1: Carpeta de Descargas Desordenada
```bash
# Primero ver qué haría
python main.py analyze --path ~/Downloads

# Luego hacer dry-run
python main.py organize --path ~/Downloads --dry-run

# Finalmente organizar
python main.py organize --path ~/Downloads
```

### Caso 2: Carpeta Compartida de Proyecto
```bash
# Crear reglas personalizadas para el proyecto
python main.py init-config --config config/proyecto-rules.json

# Editar config/proyecto-rules.json con tus reglas

# Organizar con reglas personalizadas
python main.py organize --path ./proyecto --config config/proyecto-rules.json
```

### Caso 3: Automatización Programática
```python
from pathlib import Path
from src.config import ConfigManager
from src.classifier import FileClassifier
from src.organizer import FolderOrganizer

config = ConfigManager()
rules = config.load_rules()
classifier = FileClassifier(rules)
organizer = FolderOrganizer(classifier, Path('./downloads'))
stats = organizer.organize()
print(f"Organizados: {stats['organized']} archivos")
```

## Variables de Entorno

```env
LOG_LEVEL=INFO              # Nivel de logging: DEBUG, INFO, WARNING, ERROR
LOG_FILE=organizer.log      # Archivo donde se guardan los logs
CONFIG_FILE=config/rules.json # Archivo de configuración por defecto
WATCH_FOLDER=./downloads    # Carpeta a observar por defecto
AUTO_ORGANIZE=false         # Auto-organizar al iniciar (futuro)
```

## Mejoras Futuras

- [ ] Modo watch: Observar carpeta y organizar automáticamente
- [ ] API REST: Integración con aplicaciones externas
- [ ] Interfaz GUI: Aplicación gráfica
- [ ] Programación de tareas: Ejecutar en horarios específicos
- [ ] Sincronización en nube: Organizar archivos en Google Drive, OneDrive, etc.
- [ ] Inteligencia artificial: Clasificar por contenido, no solo extensión

## Contribución

¿Tienes ideas para mejorar el proyecto? ¡Contribuye!

1. Fork el proyecto
2. Crea una rama para tu feature
3. Implementa tu mejora
4. Envía un Pull Request

## Licencia

MIT License - Úsalo libremente

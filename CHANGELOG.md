# Registro de Cambios

Todos los cambios notables en este proyecto se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [1.0.0] - 2026-06-03

### Agregado
- Clasificación automática de archivos por tipo
- Interfaz CLI con Click para fácil uso
- Modo dry-run para previsualizar cambios
- Comando analyze para ver cómo se organizarían los archivos
- Gestión de conflictos de nombres automática
- Sistema de logging con Loguru
- Configuración personalizable mediante JSON
- Variables de entorno soportadas
- Documentación completa (README, FEATURES, QUICKSTART)
- Suite de pruebas unitarias
- Demo.py para demostración
- .vscode/tasks.json para ejecución desde VS Code

### Características Principales
- Organiza archivos en carpetas según su tipo
- Soporta 7 categorías predefinidas (imágenes, documentos, videos, audio, archivos, código, ejecutables)
- Interfaz de línea de comandos intuitiva
- Registro completo de todas las operaciones
- Manejo seguro de conflictos de nombres

### Notas de Instalación
- Requiere Python 3.11+
- Problema conocido con certificados SSL en Windows (ver README)
- Se puede instalar manualmente: `pip install click python-dotenv loguru`

---

## Planes Futuros

### v1.1.0
- [ ] Modo watch: Observar carpeta y organizar automáticamente
- [ ] Soporte para más tipos de archivos
- [ ] Organización por fecha de modificación
- [ ] Organización por tamaño de archivo

### v2.0.0
- [ ] API REST para integración con otras aplicaciones
- [ ] Interfaz GUI (Tkinter o PyQt)
- [ ] Sincronización en la nube
- [ ] Clasificación basada en contenido (IA)

### v3.0.0
- [ ] Aplicación web
- [ ] Soporte para múltiples usuarios
- [ ] Almacenamiento en base de datos

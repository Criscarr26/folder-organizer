# ⚡ Inicio Rápido

## 30 segundos para empezar

### Paso 1: Instala dependencias
```bash
pip install click python-dotenv loguru
```

### Paso 2: Ejecuta una demostración
```bash
python demo.py
```

### Paso 3: Usa el organizador
```bash
# Ver ayuda
python main.py --help

# Analizar una carpeta
python main.py analyze --path ./descargas

# Organizar (simulación)
python main.py organize --path ./descargas --dry-run

# Organizar (real)
python main.py organize --path ./descargas
```

## Ejemplos Comunes

### Organizar carpeta de descargas
```bash
python main.py organize --path ~/Downloads
```

### Analizar sin mover nada
```bash
python main.py analyze --path ~/Downloads
```

### Ver qué haría exactamente
```bash
python main.py organize --path ~/Downloads --dry-run
```

### Usar configuración personalizada
```bash
# Crear configuración personalizada
python main.py init-config --config config/mis-reglas.json

# Editar config/mis-reglas.json según tus necesidades

# Usar la configuración personalizada
python main.py organize --path ~/Downloads --config config/mis-reglas.json
```

### Verbose/Debug
```bash
python main.py organize --path ~/Downloads --verbose
```

## Estructura de Carpetas Después

```
./descargas/
├── Imágenes/
│   ├── foto1.jpg
│   └── screenshot.png
├── Documentos/
│   ├── resumen.pdf
│   └── lista.txt
├── Videos/
│   └── tutorial.mp4
├── Audio/
│   └── cancion.mp3
└── Otros/
    └── archivo_desconocido.xyz
```

## Próximos Pasos

1. **Personalizar reglas**: Edita `config/rules.json.example`
2. **Crear carpetas de prueba**: Pon archivos en una carpeta de prueba
3. **Hacer dry-run**: Verifica qué haría sin mover nada
4. **Organizar**: ¡Ejecuta el organizador!

## Variables de Entorno (Opcional)

Crea un archivo `.env`:
```env
LOG_LEVEL=INFO
LOG_FILE=mis-logs.log
CONFIG_FILE=config/mis-reglas.json
```

## Solución de Problemas

### Error de SSL
Si obtienes errores de SSL al instalar con pip:
```bash
pip install --trusted-host pypi.python.org click python-dotenv loguru
```

### Permiso denegado
Asegúrate de tener permisos de escritura en la carpeta que deseas organizar.

### Archivo no encontrado
Verifica que la ruta que pasas es correcta:
```bash
python main.py organize --path /ruta/correcta
```

## Soporte

¿Problemas? Revisa:
- [README.md](../README.md) - Documentación completa
- [FEATURES.md](./FEATURES.md) - Lista de características
- `organizer.log` - Archivo de logs

---

¡Listo para organizar tus carpetas! 🎉

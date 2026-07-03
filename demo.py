"""
Script de demostración del Organizador Automático de Carpetas
Muestra cómo usar el organizador programáticamente
"""

from pathlib import Path
from src.config import ConfigManager
from src.classifier import FileClassifier
from src.organizer import FolderOrganizer

def demo():
    """Ejecuta una demostración del organizador"""
    
    print("\n" + "="*60)
    print("🎬 Demostración: Organizador Automático de Carpetas")
    print("="*60 + "\n")
    
    # 1. Cargar configuración
    print("1️⃣  Cargando configuración...")
    config = ConfigManager()
    rules = config.load_rules()
    print(f"   ✅ Reglas cargadas: {len(rules)} categorías")
    print(f"   Categorías: {', '.join(rules.keys())}\n")
    
    # 2. Crear clasificador
    print("2️⃣  Inicializando clasificador...")
    classifier = FileClassifier(rules)
    print(f"   ✅ Mapa de extensiones creado")
    print(f"   Total extensiones: {len(classifier.extension_map)}\n")
    
    # 3. Crear organizador
    print("3️⃣  Creando organizador...")
    test_dir = Path("./test_organize")
    organizer = FolderOrganizer(classifier, test_dir)
    print(f"   ✅ Organizador listo para: {test_dir}\n")
    
    # 4. Demostración con dry-run
    print("4️⃣  Analizando carpeta (dry-run)...")
    if test_dir.exists() and any(test_dir.iterdir()):
        stats = organizer.organize(dry_run=True)
        print(f"   ✅ Análisis completado:")
        print(f"      - Archivos encontrados: {stats['total_files']}")
        print(f"      - Serían organizados: {stats['organized']}")
        print(f"      - Serían omitidos: {stats['skipped']}")
        print(f"      - Errores: {stats['errors']}\n")
    else:
        print(f"   ⚠️  Carpeta '{test_dir}' no existe o está vacía")
        print(f"   Crea archivos de prueba en '{test_dir}' para ver la demo\n")
    
    # 5. Mostrar reglas
    print("5️⃣  Reglas de clasificación:")
    for category, config in rules.items():
        exts = config['extensions']
        folder = config['folder']
        print(f"   📂 {category:12} → {folder:15} ({len(exts)} extensiones)")
        print(f"      Extensiones: {', '.join(exts[:3])}{'...' if len(exts) > 3 else ''}")
    
    print("\n" + "="*60)
    print("✨ Demostración completada!")
    print("="*60 + "\n")
    
    print("📖 Próximos pasos:")
    print("   1. Crea archivos de prueba en './test_organize/'")
    print("   2. Ejecuta: python main.py analyze --path ./test_organize")
    print("   3. Ejecuta: python main.py organize --path ./test_organize --dry-run")
    print("   4. Si todo se ve bien, ejecuta sin --dry-run\n")

if __name__ == "__main__":
    demo()

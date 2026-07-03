"""
Interfaz de línea de comandos (CLI) del organizador
"""

import click
from pathlib import Path
from .config import ConfigManager
from .classifier import FileClassifier
from .organizer import FolderOrganizer
from .hierarchical_organizer import HierarchicalOrganizer
from loguru import logger

@click.group()
def cli():
    """Organizador Automático de Carpetas"""
    pass

@cli.command()
@click.option('--path', type=click.Path(exists=True), default=".", help='Ruta a organizar')
@click.option('--config', type=click.Path(exists=True), help='Archivo de configuración JSON')
@click.option('--dry-run', is_flag=True, help='Simular sin mover archivos')
@click.option('--verbose', is_flag=True, help='Modo verbose')
def organize(path: str, config: str, dry_run: bool, verbose: bool):
    """Organiza archivos en una carpeta"""
    
    # Configurar logging
    if verbose:
        logger.enable("loguru")
    
    # Cargar configuración
    config_manager = ConfigManager(config)
    rules = config_manager.load_rules()
    
    # Crear clasificador y organizador
    classifier = FileClassifier(rules)
    organizer = FolderOrganizer(classifier, Path(path))
    
    # Ejecutar organización
    click.echo(f"📁 Organizando: {path}")
    click.echo(f"🔧 Modo: {'Simulación' if dry_run else 'Ejecución real'}")
    
    stats = organizer.organize(dry_run=dry_run)
    
    # Mostrar resultados
    click.echo("\n" + "=" * 50)
    click.echo("📊 Resultados:")
    click.echo(f"  Total archivos: {stats['total_files']}")
    click.echo(f"  Organizados: {stats['organized']}")
    click.echo(f"  Omitidos: {stats['skipped']}")
    click.echo(f"  Errores: {stats['errors']}")
    click.echo("=" * 50)

@cli.command()
@click.option('--config', type=click.Path(), default="config/rules.json", help='Ruta de salida')
def init_config(config: str):
    """Crea un archivo de configuración predeterminado"""
    
    config_path = Path(config)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_rules = ConfigManager._get_default_rules()
    
    import json
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_rules, f, indent=2, ensure_ascii=False)
    
    click.echo(f"✅ Configuración creada: {config_path}")

@cli.command()
@click.option('--path', type=click.Path(exists=True), default=".", help='Carpeta a analizar')
@click.option('--config', type=click.Path(exists=True), help='Archivo de configuración')
def analyze(path: str, config: str):
    """Analiza archivos sin mover nada"""
    
    config_manager = ConfigManager(config)
    rules = config_manager.load_rules()
    
    classifier = FileClassifier(rules)
    classifications = classifier.classify_batch(Path(path))
    
    click.echo(f"\n📊 Análisis de: {path}\n")
    
    # Agrupar por categoría
    by_category = {}
    for item in classifications:
        category = item["category"]
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(item)
    
    for category, files in sorted(by_category.items()):
        click.echo(f"📂 {category.upper()} ({len(files)} archivos)")
        for file_info in files[:5]:  # Mostrar primeros 5
            size_kb = file_info["size"] / 1024
            click.echo(f"    • {file_info['file']} ({size_kb:.1f} KB)")
        if len(files) > 5:
            click.echo(f"    ... y {len(files) - 5} más")
        click.echo()

@cli.command()
@click.option('--path', type=click.Path(exists=True), default=".", help='Ruta a organizar')
@click.option('--config', type=click.Path(exists=True), help='Archivo de configuración JSON')
@click.option('--dry-run', is_flag=True, help='Simular sin mover archivos')
@click.option('--verbose', is_flag=True, help='Modo verbose')
def organize_hierarchy(path: str, config: str, dry_run: bool, verbose: bool):
    """Organiza archivos preservando jerarquía y eliminando duplicados"""
    
    # Configurar logging
    if verbose:
        logger.enable("loguru")
    
    # Cargar configuración
    config_manager = ConfigManager(config)
    rules = config_manager.load_rules()
    
    # Crear clasificador y organizador jerárquico
    classifier = FileClassifier(rules)
    organizer = HierarchicalOrganizer(classifier, Path(path))
    
    # Ejecutar organización
    click.echo(f"📁 Organizando (preservando jerarquía): {path}")
    click.echo(f"🔧 Modo: {'Simulación' if dry_run else 'Ejecución real'}")
    
    stats = organizer.organize(dry_run=dry_run)
    
    # Mostrar resultados
    click.echo("\n" + "=" * 50)
    click.echo("📊 Resultados:")
    click.echo(f"  Total archivos: {stats['total_files']}")
    click.echo(f"  Organizados: {stats['organized']}")
    click.echo(f"  Duplicados removidos: {stats['duplicates_removed']}")
    click.echo(f"  Omitidos: {stats['skipped']}")
    click.echo(f"  Errores: {stats['errors']}")
    click.echo("=" * 50)

if __name__ == "__main__":
    cli()

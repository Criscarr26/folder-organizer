"""
Módulo de clasificación de archivos
Clasifica archivos según su tipo y extensión
"""

from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from loguru import logger

class FileClassifier:
    """Clasificador de archivos por tipo"""
    
    def __init__(self, rules: Dict):
        """
        Inicializa el clasificador
        
        Args:
            rules: Diccionario con las reglas de clasificación
        """
        self.rules = rules
        self._build_extension_map()
    
    def _build_extension_map(self) -> None:
        """Construye un mapa de extensiones a categorías"""
        self.extension_map = {}
        for category, config in self.rules.items():
            for ext in config.get("extensions", []):
                self.extension_map[ext.lower()] = {
                    "category": category,
                    "folder": config.get("folder", category)
                }
    
    def classify(self, file_path: Path) -> Optional[Dict]:
        """
        Clasifica un archivo
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Diccionario con información de clasificación
        """
        if not file_path.is_file():
            return None
        
        ext = file_path.suffix.lower()
        classification = self.extension_map.get(ext)
        
        if classification:
            return {
                "file": file_path.name,
                "path": file_path,
                "extension": ext,
                "category": classification["category"],
                "target_folder": classification["folder"],
                "size": file_path.stat().st_size,
                "created": datetime.fromtimestamp(file_path.stat().st_ctime),
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
            }
        
        return {
            "file": file_path.name,
            "path": file_path,
            "extension": ext,
            "category": "otros",
            "target_folder": "Otros",
            "size": file_path.stat().st_size,
            "created": datetime.fromtimestamp(file_path.stat().st_ctime),
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
        }
    
    def classify_batch(self, directory: Path) -> List[Dict]:
        """
        Clasifica todos los archivos en un directorio de forma recursiva
        
        Args:
            directory: Ruta del directorio
            
        Returns:
            Lista de clasificaciones
        """
        classifications = []
        for item in directory.rglob("*"):
            if item.is_file():
                classification = self.classify(item)
                if classification:
                    classifications.append(classification)
                    logger.debug(f"Clasificado: {item.name} -> {classification['category']}")
        
        logger.info(f"Total archivos clasificados: {len(classifications)}")
        return classifications

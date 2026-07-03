"""
Módulo principal del organizador
Orquesta la organización de archivos
"""

import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from loguru import logger
from .classifier import FileClassifier

class FolderOrganizer:
    """Organizador principal de carpetas"""
    
    def __init__(self, classifier: FileClassifier, base_path: Path):
        """
        Inicializa el organizador
        
        Args:
            classifier: Instancia del clasificador
            base_path: Ruta base donde organizar archivos
        """
        self.classifier = classifier
        self.base_path = Path(base_path)
        self.stats = {
            "total_files": 0,
            "organized": 0,
            "skipped": 0,
            "errors": 0
        }
    
    def organize(self, dry_run: bool = False) -> Dict:
        """
        Organiza los archivos en el directorio
        
        Args:
            dry_run: Si es True, solo muestra qué haría sin mover archivos
            
        Returns:
            Estadísticas de la operación
        """
        logger.info(f"Iniciando organización de: {self.base_path}")
        
        if not self.base_path.exists():
            logger.error(f"Directorio no existe: {self.base_path}")
            return self.stats
        
        classifications = self.classifier.classify_batch(self.base_path)
        self.stats["total_files"] = len(classifications)
        
        for file_info in classifications:
            try:
                if self._organize_file(file_info, dry_run):
                    self.stats["organized"] += 1
                else:
                    self.stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error organizando {file_info['file']}: {e}")
                self.stats["errors"] += 1
        
        logger.info(f"Organización completada: {self.stats}")
        return self.stats
    
    def _organize_file(self, file_info: Dict, dry_run: bool = False) -> bool:
        """
        Organiza un archivo individual
        
        Args:
            file_info: Información del archivo
            dry_run: Si es True, solo simula
            
        Returns:
            True si fue exitoso, False si fue omitido
        """
        target_folder = self.base_path / file_info["target_folder"]
        target_path = target_folder / file_info["file"]
        
        # Si el archivo ya está en el lugar correcto
        if file_info["path"].parent == target_folder:
            logger.debug(f"Archivo ya está en lugar correcto: {file_info['file']}")
            return False
        
        # Crear carpeta si no existe
        if not dry_run:
            target_folder.mkdir(parents=True, exist_ok=True)
            
            # Manejar conflictos de nombres
            target_path = self._handle_name_conflict(target_path)
            
            # Mover archivo
            shutil.move(str(file_info["path"]), str(target_path))
            logger.info(f"Movido: {file_info['file']} -> {file_info['target_folder']}/")
        else:
            logger.info(f"[DRY RUN] Movería: {file_info['file']} -> {file_info['target_folder']}/")
        
        return True
    
    @staticmethod
    def _handle_name_conflict(target_path: Path) -> Path:
        """
        Maneja conflictos de nombres de archivo
        
        Args:
            target_path: Ruta del archivo objetivo
            
        Returns:
            Ruta válida sin conflictos
        """
        counter = 1
        original_name = target_path.name
        name_parts = original_name.rsplit(".", 1)
        
        while target_path.exists():
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{counter}.{name_parts[1]}"
            else:
                new_name = f"{original_name}_{counter}"
            
            target_path = target_path.parent / new_name
            counter += 1
        
        return target_path
    
    def get_stats(self) -> Dict:
        """Retorna las estadísticas de la última operación"""
        return self.stats

"""
Organizador jerárquico con deduplicación
Organiza archivos preservando estructura de carpetas y eliminando duplicados
"""

import shutil
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from .classifier import FileClassifier


class HierarchicalOrganizer:
    """Organizador que preserva jerarquía y elimina duplicados"""
    
    def __init__(self, classifier: FileClassifier, base_path: Path):
        """
        Inicializa el organizador jerárquico
        
        Args:
            classifier: Instancia del clasificador
            base_path: Ruta base donde organizar archivos
        """
        self.classifier = classifier
        self.base_path = Path(base_path)
        self.stats = {
            "total_files": 0,
            "organized": 0,
            "duplicates_removed": 0,
            "skipped": 0,
            "errors": 0
        }
        self.file_hashes = {}  # hash -> path mapping para detectar duplicados
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 de un archivo para detectar duplicados"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculando hash de {file_path}: {e}")
            return ""
    
    def organize(self, dry_run: bool = False) -> Dict:
        """
        Organiza archivos preservando la jerarquía y eliminando duplicados
        
        Args:
            dry_run: Si es True, solo muestra qué haría sin mover archivos
            
        Returns:
            Estadísticas de la operación
        """
        logger.info(f"Iniciando organización jerárquica de: {self.base_path}")
        
        if not self.base_path.exists():
            logger.error(f"Directorio no existe: {self.base_path}")
            return self.stats
        
        # Obtener todas las carpetas hoja (subject folders)
        leaf_folders = self._get_leaf_folders()
        logger.info(f"Encontradas {len(leaf_folders)} carpetas de asignatura")
        
        # Procesar cada carpeta hoja
        for subject_folder in leaf_folders:
            self._organize_subject_folder(subject_folder, dry_run)
        
        logger.info(f"Organización completada: {self.stats}")
        return self.stats
    
    def _get_leaf_folders(self) -> List[Path]:
        """Obtiene todas las carpetas que contienen archivos (sin subcarpetas)"""
        leaf_folders = []
        
        for folder in self.base_path.rglob("*"):
            if not folder.is_dir():
                continue
            
            # Contar archivos directos en esta carpeta
            direct_files = list(folder.glob("*.*"))
            
            if direct_files:
                leaf_folders.append(folder)
        
        return sorted(set(leaf_folders))
    
    def _organize_subject_folder(self, subject_folder: Path, dry_run: bool) -> None:
        """Organiza todos los archivos dentro de una carpeta de asignatura"""
        logger.info(f"Organizando carpeta: {subject_folder.name}")
        
        # Obtener archivos directos (no en subcarpetas)
        files = [f for f in subject_folder.glob("*.*") if f.is_file()]
        
        for file_path in files:
            try:
                # Clasificar archivo
                classification = self.classifier.classify(file_path)
                if not classification:
                    continue
                
                self.stats["total_files"] += 1
                
                # Detectar duplicados
                file_hash = self._calculate_file_hash(file_path)
                
                if file_hash in self.file_hashes:
                    # Es un duplicado
                    if not dry_run:
                        file_path.unlink()
                        logger.info(f"Duplicado eliminado: {file_path.name} (igual a {self.file_hashes[file_hash].name})")
                    else:
                        logger.info(f"[DRY RUN] Eliminaría duplicado: {file_path.name}")
                    
                    self.stats["duplicates_removed"] += 1
                    continue
                else:
                    self.file_hashes[file_hash] = file_path
                
                # Crear subcarpeta para el tipo de archivo dentro de la carpeta de asignatura
                target_folder = subject_folder / classification["target_folder"]
                
                # Si el archivo ya está en el lugar correcto
                if file_path.parent == target_folder:
                    logger.debug(f"Archivo ya está en lugar correcto: {file_path.name}")
                    self.stats["skipped"] += 1
                    continue
                
                # Mover archivo
                if not dry_run:
                    target_folder.mkdir(parents=True, exist_ok=True)
                    target_path = self._handle_name_conflict(target_folder / file_path.name)
                    shutil.move(str(file_path), str(target_path))
                    logger.info(f"Movido: {file_path.name} → {classification['target_folder']}/")
                else:
                    logger.info(f"[DRY RUN] Movería: {file_path.name} → {classification['target_folder']}/")
                
                self.stats["organized"] += 1
                
            except Exception as e:
                logger.error(f"Error organizando {file_path}: {e}")
                self.stats["errors"] += 1
    
    @staticmethod
    def _handle_name_conflict(target_path: Path) -> Path:
        """Maneja conflictos de nombres de archivo"""
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

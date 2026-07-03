"""
Módulo de configuración del organizador
Carga configuración desde variables de entorno y archivo JSON
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger

class ConfigManager:
    """Gestor de configuración del organizador"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_file: Ruta del archivo de configuración JSON
        """
        self.config_file = config_file or os.getenv("CONFIG_FILE", "config/rules.json")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "organizer.log")
        self.watch_folder = Path(os.getenv("WATCH_FOLDER", "./downloads"))
        self.auto_organize = os.getenv("AUTO_ORGANIZE", "false").lower() == "true"
        
        logger.add(self.log_file, level=self.log_level)
        logger.info(f"Configuración cargada desde: {self.config_file}")
    
    def load_rules(self) -> Dict[str, Any]:
        """
        Carga las reglas de organización desde el archivo JSON
        
        Returns:
            Diccionario con las reglas de organización
        """
        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    rules = json.load(f)
                logger.info(f"Reglas cargadas: {len(rules)} categorías")
                return rules
            else:
                logger.warning(f"Archivo de configuración no encontrado: {self.config_file}")
                return self._get_default_rules()
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            return self._get_default_rules()
    
    @staticmethod
    def _get_default_rules() -> Dict[str, Any]:
        """Retorna las reglas por defecto"""
        return {
            "images": {
                "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
                "folder": "Imágenes"
            },
            "documents": {
                "extensions": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".pptx"],
                "folder": "Documentos"
            },
            "videos": {
                "extensions": [".mp4", ".avi", ".mkv", ".mov", ".wmv"],
                "folder": "Videos"
            },
            "audio": {
                "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
                "folder": "Audio"
            },
            "archives": {
                "extensions": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "folder": "Archivos"
            }
        }

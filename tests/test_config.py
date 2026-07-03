"""
Pruebas para el módulo de configuración
"""

import pytest
import json
from pathlib import Path
from src.config import ConfigManager

def test_default_rules():
    """Prueba que se cargan las reglas por defecto"""
    rules = ConfigManager._get_default_rules()
    
    assert "images" in rules
    assert "documents" in rules
    assert "videos" in rules
    assert "audio" in rules
    assert "archives" in rules

def test_image_extensions():
    """Prueba las extensiones de imagen"""
    rules = ConfigManager._get_default_rules()
    image_exts = rules["images"]["extensions"]
    
    assert ".jpg" in image_exts
    assert ".png" in image_exts
    assert ".gif" in image_exts

def test_document_extensions():
    """Prueba las extensiones de documento"""
    rules = ConfigManager._get_default_rules()
    doc_exts = rules["documents"]["extensions"]
    
    assert ".pdf" in doc_exts
    assert ".doc" in doc_exts or ".docx" in doc_exts

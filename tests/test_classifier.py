"""
Pruebas para el módulo de clasificación
"""

import pytest
from pathlib import Path
from src.classifier import FileClassifier

@pytest.fixture
def sample_rules():
    """Fixture con reglas de prueba"""
    return {
        "images": {
            "extensions": [".jpg", ".png"],
            "folder": "Images"
        },
        "documents": {
            "extensions": [".txt", ".pdf"],
            "folder": "Documents"
        }
    }

@pytest.fixture
def classifier(sample_rules):
    """Fixture con clasificador"""
    return FileClassifier(sample_rules)

def test_classify_image(classifier):
    """Prueba clasificación de imagen"""
    # Nota: Esta es una prueba básica
    assert classifier.extension_map[".jpg"]["category"] == "images"
    assert classifier.extension_map[".jpg"]["folder"] == "Images"

def test_classify_document(classifier):
    """Prueba clasificación de documento"""
    assert classifier.extension_map[".txt"]["category"] == "documents"
    assert classifier.extension_map[".txt"]["folder"] == "Documents"

def test_extension_map_built(classifier):
    """Verifica que el mapa de extensiones se construyó correctamente"""
    assert len(classifier.extension_map) == 4
    assert ".jpg" in classifier.extension_map
    assert ".png" in classifier.extension_map
    assert ".txt" in classifier.extension_map
    assert ".pdf" in classifier.extension_map

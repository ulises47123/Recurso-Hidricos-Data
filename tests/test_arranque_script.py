import os
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"

def test_existencia_scripts_arranque():
    registrar_bat = SCRIPTS_DIR / "registrar_arranque.bat"
    desregistrar_bat = SCRIPTS_DIR / "desregistrar_arranque.bat"
    
    assert registrar_bat.exists(), f"No existe {registrar_bat}"
    assert desregistrar_bat.exists(), f"No existe {desregistrar_bat}"

def test_sintaxis_contenido_registrar_bat():
    registrar_bat = SCRIPTS_DIR / "registrar_arranque.bat"
    content = registrar_bat.read_text(encoding="utf-8")
    
    assert "schtasks /Create" in content
    assert "/SC ONLOGON" in content
    assert "/RL HIGHEST" in content
    assert "iniciar_sistema.bat" in content
    assert "DPRH_Jujuy_ArranqueAutomatico" in content
    assert "schtasks /Delete" in content  # Idempotencia / borrado previo

def test_sintaxis_contenido_desregistrar_bat():
    desregistrar_bat = SCRIPTS_DIR / "desregistrar_arranque.bat"
    content = desregistrar_bat.read_text(encoding="utf-8")
    
    assert "schtasks /Delete" in content
    assert "DPRH_Jujuy_ArranqueAutomatico" in content

def test_verificacion_cadena_iniciar_sistema():
    iniciar_bat = BASE_DIR / "iniciar_sistema.bat"
    assert iniciar_bat.exists(), "iniciar_sistema.bat debe existir en la raiz del proyecto"
    content = iniciar_bat.read_text(encoding="utf-8")
    assert "npm start" in content or "electron" in content

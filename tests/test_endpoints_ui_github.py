import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app
from backend.database import init_db, get_db_connection
from backend.security import hash_password

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE usuarios SET password_hash = ? WHERE username = 'admin'", (hash_password("adminpassword"),))
    conn.commit()
    conn.close()

def get_auth_headers():
    response = client.post("/api/auth/login", json={"username": "admin", "password": "adminpassword"})
    assert response.status_code == 200
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}

def test_github_llave_publica():
    headers = get_auth_headers()
    with patch("backend.services.auto_readme_sync.obtener_llave_publica", return_value="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test@dprh"):
        with patch("backend.services.auto_readme_sync.tiene_senal_verde", return_value=False):
            res = client.get("/api/sistema/github/llave-publica", headers=headers)
            assert res.status_code == 200
            data = res.json()
            assert data["llave_publica"] == "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test@dprh"
            assert data["senal_verde"] is False

def test_github_probar_exito():
    headers = get_auth_headers()
    mock_res = {
        "success": True,
        "autenticado": True,
        "mensaje": "Conexión SSH exitosa. Señal verde activada."
    }
    with patch("backend.services.auto_readme_sync.probar_conexion", return_value=mock_res):
        res = client.post("/api/sistema/github/probar", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is True
        assert "Conexión SSH exitosa" in data["mensaje"]

def test_github_probar_fallo():
    headers = get_auth_headers()
    mock_res = {
        "success": False,
        "autenticado": False,
        "mensaje": "Permission denied (publickey)."
    }
    with patch("backend.services.auto_readme_sync.probar_conexion", return_value=mock_res):
        res = client.post("/api/sistema/github/probar", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["ok"] is False
        assert "Permission denied" in data["mensaje"]

def test_github_estado():
    headers = get_auth_headers()
    mock_status = {
        "github_signal_ok": True,
        "tunnel_url": "https://test-tunnel.trycloudflare.com",
        "ultimo_error": None,
        "ultimo_sync": "2026-10-06 20:30:00",
        "llave_publica": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestKey test@dprh"
    }
    with patch("backend.services.auto_readme_sync.obtener_estado_sync", return_value=mock_status):
        res = client.get("/api/sistema/github/estado", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["senal_verde"] is True
        assert data["tunnel_url"] == "https://test-tunnel.trycloudflare.com"
        assert data["ultimo_sync"] == "2026-10-06 20:30:00"

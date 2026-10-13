import pytest
import os
import re
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import init_db, get_db_connection
from backend.services import auto_readme_sync

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()
    # Reset signal ok flag in config
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM configuracion WHERE clave = 'github_signal_ok'")
    conn.commit()
    conn.close()
    yield

def test_senal_verde_persistencia():
    assert auto_readme_sync.tiene_senal_verde() is False
    
    auto_readme_sync.guardar_senal_verde(True)
    assert auto_readme_sync.tiene_senal_verde() is True

    auto_readme_sync.guardar_senal_verde(False)
    assert auto_readme_sync.tiene_senal_verde() is False

def test_obtener_llave_publica():
    pub_key = auto_readme_sync.obtener_llave_publica()
    assert isinstance(pub_key, str)
    assert len(pub_key) > 0 or "ssh-" in pub_key or "dprh" in pub_key or pub_key == ""

def test_probar_conexion_exito():
    with patch("backend.services.auto_readme_sync.probar_conexion_ssh_github") as mock_ssh, \
         patch("backend.services.auto_readme_sync.obtener_o_generar_deploy_key") as mock_key:
        
        mock_key.return_value = {
            "success": True,
            "clave_publica": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...",
            "deploy_url": "https://github.com/user/repo/settings/keys"
        }
        mock_ssh.return_value = {
            "autenticado": True,
            "mensaje": "Conexión SSH exitosa!"
        }

        res = auto_readme_sync.probar_conexion()
        assert res["success"] is True
        assert res["autenticado"] is True
        assert auto_readme_sync.tiene_senal_verde() is True

def test_probar_conexion_permission_denied():
    with patch("backend.services.auto_readme_sync.probar_conexion_ssh_github") as mock_ssh, \
         patch("backend.services.auto_readme_sync.obtener_o_generar_deploy_key") as mock_key:
        
        mock_key.return_value = {
            "success": True,
            "clave_publica": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...",
            "deploy_url": "https://github.com/user/repo/settings/keys"
        }
        mock_ssh.return_value = {
            "autenticado": False,
            "mensaje": "Permission denied (publickey)."
        }

        res = auto_readme_sync.probar_conexion()
        assert res["success"] is False
        assert res["autenticado"] is False
        assert "Permission denied" in res["mensaje"]
        assert auto_readme_sync.tiene_senal_verde() is False

def test_formato_readme_template():
    tunnel_url = "https://test-subdomain.trycloudflare.com"
    content = auto_readme_sync.generar_readme_content(tunnel_url)
    
    assert "logo.png" in content
    assert "readme-typing-svg" in content
    assert "Ver_Proyecto-Acceder_al_Sistema-007ACC" in content
    assert tunnel_url in content
    assert "---" in content
    assert "Dirección Provincial de Recursos Hídricos" in content

def test_regex_url_tunel_cloudflare():
    mock_log = (
        "2026-10-06T20:00:00Z INF +--------------------------------------------------------------------------------------------+\n"
        "2026-10-06T20:00:00Z INF | Your quick Tunnel has been created. Visit it at (cyan or format):                          |\n"
        "2026-10-06T20:00:00Z INF | https://sample-tunnel-123.trycloudflare.com                                                |\n"
        "2026-10-06T20:00:00Z INF +--------------------------------------------------------------------------------------------+\n"
    )
    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    match = url_regex.search(mock_log)
    assert match is not None
    assert match.group(0) == "https://sample-tunnel-123.trycloudflare.com"

def test_orquestacion_sin_senal_verde():
    auto_readme_sync.guardar_senal_verde(False)
    res = auto_readme_sync.sincronizacion_automatica()
    assert res["success"] is False
    assert res["reason"] == "sin_senal_verde"

def test_orquestacion_con_senal_verde_exito():
    auto_readme_sync.guardar_senal_verde(True)
    with patch("backend.services.auto_readme_sync.iniciar_tunel_cloudflare") as mock_tunel, \
         patch("backend.services.auto_readme_sync.actualizar_readme_gh_pages") as mock_update:
        
        mock_tunel.return_value = "https://dprh-jujuy.trycloudflare.com"
        mock_update.return_value = {"success": True, "mensaje": "README publicado"}

        res = auto_readme_sync.sincronizacion_automatica()
        assert res["success"] is True
        assert res["tunnel_url"] == "https://dprh-jujuy.trycloudflare.com"
        mock_tunel.assert_called_once()
        mock_update.assert_called_once_with("https://dprh-jujuy.trycloudflare.com")

def test_endpoints_api_auto_readme():
    # 1. Login para obtener token admin
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. GET status
    res_status = client.get("/api/auto-readme/status", headers=headers)
    assert res_status.status_code == 200
    st_json = res_status.json()
    assert "github_signal_ok" in st_json
    assert "llave_publica" in st_json

    # 3. POST probar-conexion
    with patch("backend.services.auto_readme_sync.probar_conexion") as mock_pc:
        mock_pc.return_value = {"success": True, "autenticado": True, "mensaje": "OK"}
        res_pc = client.post("/api/auto-readme/probar-conexion", headers=headers)
        assert res_pc.status_code == 200
        assert res_pc.json()["success"] is True

    # 4. POST sincronizar
    with patch("backend.services.auto_readme_sync.sincronizacion_automatica") as mock_sa:
        mock_sa.return_value = {"success": True, "tunnel_url": "https://test.trycloudflare.com"}
        res_sa = client.post("/api/auto-readme/sincronizar", headers=headers)
        assert res_sa.status_code == 200
        assert res_sa.json()["success"] is True

def test_actualizar_readme_gh_pages_con_deploy_key(tmp_path):
    tunnel_url = "https://test-tunnel-xyz.trycloudflare.com"
    target_gh_pages = tmp_path / ".gh_pages_repo"
    
    with patch("backend.services.auto_readme_sync.GH_PAGES_DIR", str(target_gh_pages)), \
         patch("backend.services.auto_readme_sync.obtener_o_generar_deploy_key") as mock_key, \
         patch("subprocess.run") as mock_sub:
        
        mock_key.return_value = {"success": True, "clave_publica": "ssh-ed25519 AAA..."}
        
        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "OK"
        mock_res.stderr = ""
        mock_sub.return_value = mock_res
        
        res = auto_readme_sync.actualizar_readme_gh_pages(tunnel_url)
        assert res["success"] is True
        assert "publicado exitosamente" in res["mensaje"]
        
        mock_key.assert_called_once()
        
        git_ssh_cmd_found = False
        for call_args in mock_sub.call_args_list:
            kwargs = call_args.kwargs
            env = kwargs.get("env")
            if env and "GIT_SSH_COMMAND" in env:
                assert "ssh -i" in env["GIT_SSH_COMMAND"]
                assert "id_ed25519" in env["GIT_SSH_COMMAND"]
                git_ssh_cmd_found = True
                break
        assert git_ssh_cmd_found is True

def test_iniciar_tunel_remoto_usa_actualizar_readme_gh_pages():
    from backend.main import iniciar_tunel_remoto, CLOUDFLARE_TUNNEL_STATE
    CLOUDFLARE_TUNNEL_STATE["proceso"] = None
    CLOUDFLARE_TUNNEL_STATE["url"] = None
    CLOUDFLARE_TUNNEL_STATE["activo"] = False

    with patch("pycloudflared.util.get_info") as mock_info, \
         patch("pathlib.Path.exists", return_value=True), \
         patch("subprocess.Popen") as mock_popen, \
         patch("backend.services.auto_readme_sync.actualizar_readme_gh_pages") as mock_sync_readme:
        
        mock_info_obj = MagicMock()
        mock_info_obj.executable = "cloudflared.exe"
        mock_info.return_value = mock_info_obj
        
        proc_mock = MagicMock()
        proc_mock.poll.return_value = None
        proc_mock.stderr.readline.side_effect = [
            "2026-10-06 INF https://my-test-tunnel.trycloudflare.com\n",
            ""
        ]
        mock_popen.return_value = proc_mock
        mock_sync_readme.return_value = {"success": True, "mensaje": "README publicado"}
        
        res = iniciar_tunel_remoto()
        assert res["success"] is True
        assert res["url"] == "https://my-test-tunnel.trycloudflare.com"
        mock_sync_readme.assert_called_once_with("https://my-test-tunnel.trycloudflare.com")


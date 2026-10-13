import os
import sys
import unittest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.main import app
from backend.database import init_db, get_db_connection
from backend.security import hash_password, verify_password

class TestSeguridad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_migracion_transparente_hash_viejo_a_pbkdf2(self):
        """Verifica que un usuario con hash en texto plano al loguearse migra su contraseña a pbkdf2$."""
        conn = get_db_connection()
        cursor = conn.cursor()
        username = "user_hash_viejo"
        plain_password = "password123_viejo"
        
        # Eliminar si ya existe y crear con hash plano
        cursor.execute("DELETE FROM usuarios WHERE username = ?", (username,))
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, rol, permisos, activo)
            VALUES (?, ?, 'Usuario Test Viejo', 'admin', '["*"]', 1)
        """, (username, plain_password))
        conn.commit()

        # Login con contraseña plana
        response = self.client.post("/api/auth/login", json={
            "username": username,
            "password": plain_password
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertIn("token", data)
        self.assertTrue(len(data["token"]) > 10)

        # Verificar en DB que la contraseña se migró a pbkdf2$
        cursor.execute("SELECT password_hash FROM usuarios WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        nuevo_hash = row[0]
        self.assertTrue(nuevo_hash.startswith("pbkdf2$600000$"))
        self.assertTrue(verify_password(plain_password, nuevo_hash))

    def test_token_bearer_requerido_y_validacion(self):
        """Verifica que peticiones a la API sin header Bearer devuelven 401 y con token válido responden OK."""
        # Petición sin token a /api/dashboard debe devolver 401
        res_no_token = self.client.get("/api/dashboard")
        self.assertEqual(res_no_token.status_code, 401)

        # Petición con token inválido a /api/dashboard debe devolver 401
        res_bad_token = self.client.get("/api/dashboard", headers={"Authorization": "Bearer token_invalido_xyz"})
        self.assertEqual(res_bad_token.status_code, 401)

        # Login para obtener un token válido
        login_res = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["token"]

        # Petición con token válido debe devolver 200
        res_ok = self.client.get("/api/dashboard", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res_ok.status_code, 200)

    def test_tunel_trycloudflare_bloquea_escritura(self):
        """Verifica que el origen *.trycloudflare.com bloquea POST/PUT/DELETE/PATCH excepto /api/auth/login."""
        host_tunel = "mi-tunel-prueba.trycloudflare.com"
        headers_tunel = {"Host": host_tunel}

        # Login mediante el túnel debe estar permitido (POST /api/auth/login)
        login_res = self.client.post("/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        }, headers=headers_tunel)
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["token"]

        headers_auth_tunel = {
            "Host": host_tunel,
            "Authorization": f"Bearer {token}"
        }

        # GET a /api/dashboard a través del túnel debe estar permitido (200)
        get_res = self.client.get("/api/dashboard", headers=headers_auth_tunel)
        self.assertEqual(get_res.status_code, 200)

        # POST mutante a la API a través del túnel debe ser bloqueado con 403
        post_res = self.client.post("/api/usuarios", json={
            "username": "test_tunel_user",
            "password": "pass",
            "nombre_completo": "Test",
            "rol": "admin"
        }, headers=headers_auth_tunel)
        self.assertEqual(post_res.status_code, 403)

        # PUT mutante a la API a través del túnel debe ser bloqueado con 403
        put_res = self.client.put("/api/usuarios/admin", json={
            "nombre_completo": "Admin Modificado"
        }, headers=headers_auth_tunel)
        self.assertEqual(put_res.status_code, 403)

        # DELETE mutante a la API a través del túnel debe ser bloqueado con 403
        del_res = self.client.delete("/api/areas/9999", headers=headers_auth_tunel)
        self.assertEqual(del_res.status_code, 403)

    def test_health_endpoint_publico_y_dashboard_protegido(self):
        """Verifica que /api/health es público (200 sin token, {"ok": True}) y /api/dashboard exige token (401 sin token)."""
        # /api/health sin token debe responder HTTP 200 y {"ok": True}
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json(), {"ok": True})

        # /api/dashboard sin token debe responder HTTP 401
        res_dashboard = self.client.get("/api/dashboard")
        self.assertEqual(res_dashboard.status_code, 401)

    def test_seguridad_auto_readme_ssh_command_y_sanitizacion(self):
        """Verifica que el comando GIT_SSH_COMMAND en auto_readme_sync impida diálogos interactivos y use BatchMode."""
        from backend.services import auto_readme_sync
        from unittest.mock import patch, MagicMock
        with patch("subprocess.run") as mock_sub, \
             patch("backend.services.auto_readme_sync.obtener_o_generar_deploy_key"):
            mock_res = MagicMock()
            mock_res.returncode = 0
            mock_sub.return_value = mock_res
            
            auto_readme_sync.actualizar_readme_gh_pages("https://sec-test.trycloudflare.com")
            
            ssh_cmds = []
            for call in mock_sub.call_args_list:
                env = call.kwargs.get("env")
                if env and "GIT_SSH_COMMAND" in env:
                    ssh_cmds.append(env["GIT_SSH_COMMAND"])
            
            self.assertTrue(len(ssh_cmds) > 0)
            for cmd in ssh_cmds:
                self.assertIn("BatchMode=yes", cmd)
                self.assertIn("StrictHostKeyChecking=no", cmd)



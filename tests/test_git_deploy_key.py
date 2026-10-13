import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db
from backend.services import git_manager_service
from backend.main import get_git_estado, post_git_generar_deploy_key, post_git_probar_conexion

class TestGitDeployKey(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_verificar_git_instalado(self):
        """Verifica que el detector de Git identifique la instalación y arquitectura."""
        estado = git_manager_service.verificar_git_instalado()
        self.assertIn("instalado", estado)
        self.assertIn("arquitectura", estado)
        self.assertIn(estado["arquitectura"], ["64-bit", "32-bit"])
        # En la máquina actual de desarrollo Git está instalado
        self.assertTrue(estado["instalado"])
        self.assertIn("git version", estado["version"].lower())

    def test_generar_y_obtener_deploy_key(self):
        """Verifica la generación automática de la Deploy Key SSH (ed25519)."""
        key_info = git_manager_service.obtener_o_generar_deploy_key()
        self.assertTrue(key_info["success"])
        self.assertTrue(key_info["clave_publica"].startswith("ssh-"))
        self.assertIn("recursos-hidricos-deploy-key", key_info["clave_publica"])
        self.assertTrue(os.path.exists(key_info["ruta_privada"]))
        self.assertIn("settings/keys", key_info["deploy_url"])
        self.assertTrue(key_info["ssh_url"].startswith("git@github.com:"))

    def test_convertir_urls_ssh(self):
        """Verifica la conversión de URLs HTTPS a SSH para Deploy Keys."""
        url_https = "https://github.com/ulises47123/Recursos-H-dricos.git"
        url_ssh = git_manager_service.convertir_a_ssh_url(url_https)
        self.assertEqual(url_ssh, "git@github.com:ulises47123/Recursos-H-dricos.git")

        deploy_keys_url = git_manager_service.obtener_deploy_keys_url(url_https)
        self.assertEqual(deploy_keys_url, "https://github.com/ulises47123/Recursos-H-dricos/settings/keys")

    def test_endpoints_api_git(self):
        """Prueba los endpoints de FastAPI para el estado de Git y Deploy Keys."""
        estado_api = get_git_estado()
        self.assertIn("git", estado_api)
        self.assertIn("deploy_key", estado_api)
        self.assertTrue(estado_api["deploy_key"]["success"])

        key_api = post_git_generar_deploy_key()
        self.assertTrue(key_api["success"])
        self.assertIn("ssh-", key_api["clave_publica"])

if __name__ == '__main__':
    unittest.main()

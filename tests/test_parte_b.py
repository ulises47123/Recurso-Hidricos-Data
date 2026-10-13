import os
import sys
import unittest
import tempfile
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db
from backend.services import gdrive_service, github_sync_service
from backend.main import (
    obtener_config_tunel_rapido,
    guardar_config_tunel_rapido,
    obtener_config_github_sync,
    guardar_config_github_sync,
    reintentar_git_push_endpoint,
    get_gdrive_config,
    conectar_gdrive,
    listar_backups_gdrive_endpoint
)

class TestParteBRequerimientos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_gdrive_rotacion_tres_copias(self):
        """
        [B4] Prueba de rotación estricta de máximo 3 copias de seguridad.
        """
        temp_dir = tempfile.mkdtemp(prefix="test_backups_")
        try:
            # Configurar carpeta temporal para la prueba
            gdrive_service.guardar_config_gdrive({
                "gdrive_connected": "1",
                "gdrive_folder_path": temp_dir
            })

            # Generar 5 backups
            import time
            backups_creados = []
            for i in range(5):
                res = gdrive_service.realizar_backup_gdrive(usuario=f"TestUser_{i}")
                self.assertTrue(res["success"])
                backups_creados.append(res["backup_creado"])
                time.sleep(0.02)

            # Comprobar que en la carpeta y en la lista sólo quedan exactamente 3
            archivos_reales = [f for f in os.listdir(temp_dir) if f.endswith(".db")]
            self.assertEqual(len(archivos_reales), 3, f"Deben quedar exactamente 3 copias y hay {len(archivos_reales)}")

            lista = gdrive_service.listar_backups_gdrive()
            self.assertEqual(len(lista), 3)

            # Las 3 copias restantes deben ser las últimas generadas
            nombres_en_lista = [b["nombre"] for b in lista]
            self.assertIn(backups_creados[-1], nombres_en_lista)
            self.assertIn(backups_creados[-2], nombres_en_lista)
            self.assertIn(backups_creados[-3], nombres_en_lista)
            self.assertNotIn(backups_creados[0], nombres_en_lista)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_gdrive_restauracion_backup(self):
        """
        [B4] Prueba de restauración de copia de seguridad.
        """
        temp_dir = tempfile.mkdtemp(prefix="test_restore_")
        try:
            gdrive_service.guardar_config_gdrive({
                "gdrive_connected": "1",
                "gdrive_folder_path": temp_dir
            })
            res_crear = gdrive_service.realizar_backup_gdrive(usuario="TestRestore")
            backup_nombre = res_crear["backup_creado"]

            # Restaurar el backup creado
            res_restaurar = gdrive_service.restaurar_backup_gdrive(backup_nombre, usuario="TestRestore")
            self.assertTrue(res_restaurar["success"])
            self.assertIn("restaurada exitosamente", res_restaurar["mensaje"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_github_generacion_html_acceso(self):
        """
        [B3] Prueba de generación de página HTML de acceso remoto.
        """
        url_prueba = "https://prueba-temporal-cloudflare.trycloudflare.com"
        html = github_sync_service.generar_html_acceso(url_prueba)
        
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(url_prueba, html)
        self.assertIn("Iniciar Sesión en Recursos Hídricos", html)
        self.assertIn("Dirección de Recursos Hídricos", html)

    def test_github_sincronizar_en_directorio(self):
        """
        [B3] Prueba de sincronización en carpeta de destino.
        """
        temp_dir = tempfile.mkdtemp(prefix="test_git_sync_")
        try:
            url_prueba = "https://enlace-demo-sync.trycloudflare.com"
            res = github_sync_service.sincronizar_link_en_repo(url_prueba, git_repo_dir=temp_dir)
            self.assertTrue(res["success"])
            
            index_path = os.path.join(temp_dir, "index.html")
            self.assertTrue(os.path.exists(index_path))
            with open(index_path, "r", encoding="utf-8") as f:
                contenido = f.read()
            self.assertIn(url_prueba, contenido)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_api_configuracion_tunel_rapido(self):
        """
        [B2] Prueba de endpoints para configuración del túnel temporal de Cloudflare.
        """
        res_post = guardar_config_tunel_rapido(autostart=True)
        self.assertTrue(res_post["success"])
        self.assertTrue(res_post["autostart"])

        res_get = obtener_config_tunel_rapido()
        self.assertTrue(res_get["autostart"])

    def test_api_configuracion_github_sync(self):
        """
        [B3] Prueba de endpoints de configuración de sincronización con GitHub Pages.
        """
        res_post = guardar_config_github_sync(repo_dir="C:\\Ruta\\TestRepo", enabled=True)
        self.assertTrue(res_post["success"])
        self.assertEqual(res_post["repo_dir"], "C:\\Ruta\\TestRepo")
        self.assertTrue(res_post["enabled"])

        res_get = obtener_config_github_sync()
        self.assertEqual(res_get["repo_dir"], "C:\\Ruta\\TestRepo")
        self.assertTrue(res_get["enabled"])

        # Probar endpoint de reintento
        res_retry = reintentar_git_push_endpoint()
        self.assertTrue(res_retry["success"])

    def test_api_gdrive_config_y_endpoints(self):
        """
        [B4] Prueba de endpoints de conexión y listado de backups de Google Drive.
        """
        # Conectar cuenta
        res_conn = conectar_gdrive(email="personal.rrhh@gmail.com", credentials_json="", folder_path="")
        self.assertTrue(res_conn["success"])
        self.assertEqual(res_conn["email"], "personal.rrhh@gmail.com")

        # Consultar config
        res_cfg = get_gdrive_config()
        self.assertTrue(res_cfg["conectado"])
        self.assertEqual(res_cfg["email"], "personal.rrhh@gmail.com")

        # Listar backups
        res_backups = listar_backups_gdrive_endpoint()
        self.assertIsInstance(res_backups, list)

if __name__ == "__main__":
    unittest.main()

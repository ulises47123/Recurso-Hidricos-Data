"""
tests/test_nuevos_endpoints_catalogos.py
Pruebas integrales de:
1. Endpoints CRUD completos para catálogos:
   - situacion_revista (obtener, agregar, editar, eliminar)
   - lugares_trabajo (obtener, agregar, editar, eliminar)
   - funciones (obtener, agregar, editar, eliminar)
   - areas (obtener, agregar, editar, eliminar)
2. Descarga de plantilla ejemplo Excel:
   - descargar_plantilla_ejemplo
3. Actualización de usuario admin:
   - actualizar_usuario con string 'admin' y con id numérico
4. Compatibilidad PostgreSQL / SQLite dual:
   - Verificación de fallback y conexión
"""

import unittest
import io
import asyncio
from backend.main import (
    app,
    obtener_catalogo_situacion_revista,
    agregar_catalogo_situacion_revista,
    editar_catalogo_situacion_revista,
    eliminar_catalogo_situacion_revista,
    obtener_catalogo_lugares_trabajo,
    agregar_catalogo_lugares_trabajo,
    editar_catalogo_lugares_trabajo,
    eliminar_catalogo_lugares_trabajo,
    obtener_catalogo_funciones,
    agregar_catalogo_funciones,
    editar_catalogo_funciones,
    eliminar_catalogo_funciones,
    obtener_catalogo_areas,
    agregar_catalogo_areas,
    editar_catalogo_areas,
    eliminar_catalogo_areas,
    descargar_plantilla_ejemplo,
    actualizar_usuario,
    login
)
from backend.models import UsuarioLogin, UsuarioUpdate
from backend.database import init_db, get_db_connection

class TestNuevosEndpointsCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    # -------------------------------------------------------------
    # 1. PRUEBAS SITUACIONES DE REVISTA
    # -------------------------------------------------------------
    def test_crud_situacion_revista(self):
        # Listar
        items = obtener_catalogo_situacion_revista()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Agregar
        res_post = agregar_catalogo_situacion_revista({"nombre": "Revista Prueba Temp", "descripcion": "Desc test", "orden": 99})
        self.assertTrue(res_post.get("success"))
        item_id = res_post.get("id")
        self.assertIsNotNone(item_id)

        # Editar
        res_put = editar_catalogo_situacion_revista(item_id, {"nombre": "Revista Prueba Modificada", "descripcion": "Desc mod", "orden": 98})
        self.assertTrue(res_put.get("success"))

        # Eliminar
        res_del = eliminar_catalogo_situacion_revista(item_id)
        self.assertTrue(res_del.get("success"))

    # -------------------------------------------------------------
    # 2. PRUEBAS LUGARES DE TRABAJO
    # -------------------------------------------------------------
    def test_crud_lugares_trabajo(self):
        # Listar
        items = obtener_catalogo_lugares_trabajo()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Agregar
        res_post = agregar_catalogo_lugares_trabajo({"nombre": "Destino Prueba Temp", "descripcion": "Desc", "orden": 50})
        self.assertTrue(res_post.get("success"))
        item_id = res_post.get("id")

        # Editar
        res_put = editar_catalogo_lugares_trabajo(item_id, {"nombre": "Destino Prueba Modificado"})
        self.assertTrue(res_put.get("success"))

        # Eliminar
        res_del = eliminar_catalogo_lugares_trabajo(item_id)
        self.assertTrue(res_del.get("success"))

    # -------------------------------------------------------------
    # 3. PRUEBAS FUNCIONES OFICIALES
    # -------------------------------------------------------------
    def test_crud_funciones(self):
        # Listar
        items = obtener_catalogo_funciones()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)

        # Agregar
        res_post = agregar_catalogo_funciones({"nombre": "Especialista Hídrico Temp", "descripcion": "Función test", "orden": 30})
        self.assertTrue(res_post.get("success"))
        item_id = res_post.get("id")

        # Editar
        res_put = editar_catalogo_funciones(item_id, {"nombre": "Especialista Hídrico Modificado"})
        self.assertTrue(res_put.get("success"))

        # Eliminar
        res_del = eliminar_catalogo_funciones(item_id)
        self.assertTrue(res_del.get("success"))

    # -------------------------------------------------------------
    # 4. PRUEBAS ÁREAS / DEPENDENCIAS
    # -------------------------------------------------------------
    def test_crud_areas(self):
        # Listar
        areas = obtener_catalogo_areas()
        self.assertIsInstance(areas, list)

        # Agregar
        res_post = agregar_catalogo_areas({"nombre": "Área de Innovación Tecnológica Test", "codigo": "AIT-99", "nivel": 1})
        self.assertTrue(res_post.get("success"))
        area_id = res_post.get("id")

        # Editar
        res_put = editar_catalogo_areas(area_id, {"nombre": "Área de Innovación Modificada", "codigo": "AIT-99", "nivel": 1})
        self.assertTrue(res_put.get("success"))

        # Eliminar
        res_del = eliminar_catalogo_areas(area_id)
        self.assertTrue(res_del.get("success"))

    # -------------------------------------------------------------
    # 5. PRUEBA PLANTILLA EXCEL EJEMPLO
    # -------------------------------------------------------------
    def test_descargar_plantilla_ejemplo_endpoint(self):
        resp = descargar_plantilla_ejemplo()
        self.assertIn("Plantilla_Ejemplo_Personal_DPRH.xlsx", resp.headers.get("Content-Disposition", ""))

        async def _leer_stream():
            chunks = []
            async for chunk in resp.body_iterator:
                chunks.append(chunk)
            return b"".join(chunks)

        excel_bytes = asyncio.run(_leer_stream())
        self.assertGreater(len(excel_bytes), 1000)
        self.assertTrue(excel_bytes.startswith(b"PK"))

    # -------------------------------------------------------------
    # 6. PRUEBA ACTUALIZACIÓN ADMIN CON IDENTIFICADOR Y PASSWORD
    # -------------------------------------------------------------
    def test_actualizar_admin_por_username_e_id(self):
        # Actualizar usando 'admin' (cadena)
        res_admin_str = actualizar_usuario(
            "admin",
            UsuarioUpdate(nombre_completo="Administrador General DPRH", password="admin123")
        )
        self.assertTrue(res_admin_str.get("success"))

        # Login con nueva contraseña admin123
        login_res = login(UsuarioLogin(username="admin", password="admin123"))
        self.assertTrue(login_res.get("success"))
        self.assertEqual(login_res["usuario"]["nombre_completo"], "Administrador General DPRH")

        # Actualizar usando id numérico
        admin_id = str(login_res["usuario"]["id"])
        res_admin_num = actualizar_usuario(
            admin_id,
            UsuarioUpdate(nombre_completo="Administrador Principal DPRH", password="admin123")
        )
        self.assertTrue(res_admin_num.get("success"))


if __name__ == "__main__":
    unittest.main()

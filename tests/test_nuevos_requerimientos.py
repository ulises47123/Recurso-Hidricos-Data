import os
import sys
import unittest
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.database import init_db, get_db_connection
from backend.services import compensatorios_service, personal_service, excel_service, pdf_service

class TestRequerimientosIngeniera(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        todos = personal_service.listar_personal()
        if not todos:
            personal_service.crear_personal({
                "apellido": "TEST",
                "nombre": "Agente Prueba",
                "dni": "99999999",
                "legajo": "TEST-001",
                "situacion_revista": "Planta Permanente",
                "cargo": "Administrativo"
            })

    def test_compensatorios_caso_ejemplo_cliente(self):
        """
        Validación del caso de la cliente:
        Desde 09/10/2026 hasta 13/10/2026.
        - 09/10/2026: Viernes (Día hábil 1)
        - 10/10/2026: Sábado (Fin de semana)
        - 11/10/2026: Domingo (Fin de semana)
        - 12/10/2026: Lunes (Feriado: Día del Respeto a la Diversidad Cultural)
        - 13/10/2026: Martes (Día hábil 2)
        Total esperado: 2 días hábiles.
        """
        resultado = compensatorios_service.calcular_dias_habiles_detalle("2026-10-09", "2026-10-13")
        
        self.assertEqual(resultado["dias_habiles"], 2, f"Se esperaban 2 días hábiles y dio {resultado['dias_habiles']}")
        self.assertEqual(resultado["fines_semana"], 2, "Se esperaban 2 días de fin de semana")
        self.assertEqual(len(resultado["feriados"]), 1, "Se esperaba 1 feriado en el rango")
        self.assertEqual(resultado["feriados"][0]["fecha"], "2026-10-12")
        self.assertIn("Diversidad Cultural", resultado["feriados"][0]["descripcion"])

        # Verificar la función simple calcular_dias_habiles
        dias_simples = compensatorios_service.calcular_dias_habiles("2026-10-09", "2026-10-13")
        self.assertEqual(dias_simples, 2)

    def test_personal_filtrado_por_ids_seleccionados(self):
        """
        Validación de la selección por checkboxes:
        Permite filtrar personal por lista de IDs seleccionados para reportes.
        """
        todos = personal_service.listar_personal()
        self.assertGreater(len(todos), 0, "Debe haber al menos un agente en la base de datos")

        primer_id = todos[0]["id"]
        filtrados = personal_service.listar_personal(ids=[primer_id])
        self.assertEqual(len(filtrados), 1)
        self.assertEqual(filtrados[0]["id"], primer_id)

    def test_personal_pdf_nomina_seleccion(self):
        """
        Validación de la generación de PDF de nómina con agentes seleccionados.
        """
        todos = personal_service.listar_personal()
        if todos:
            primer_id = todos[0]["id"]
            seleccionados = personal_service.listar_personal(ids=[primer_id])
            pdf_bytes = pdf_service.generar_pdf_nomina_personal(seleccionados)
            self.assertTrue(len(pdf_bytes) > 0)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_personal_excel_seleccion(self):
        """
        Validación de la exportación a Excel (.xlsx) con agentes seleccionados.
        """
        todos = personal_service.listar_personal()
        if todos:
            primer_id = todos[0]["id"]
            excel_bytes = excel_service.exportar_personal_seleccion_excel([primer_id])
            self.assertTrue(len(excel_bytes) > 0)
            # Los archivos .xlsx son archivos ZIP (PK..)
            self.assertTrue(excel_bytes.startswith(b"PK"))

if __name__ == "__main__":
    unittest.main()

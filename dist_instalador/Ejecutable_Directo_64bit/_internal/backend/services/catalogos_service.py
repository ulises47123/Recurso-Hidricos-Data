"""
backend/services/catalogos_service.py
Catálogos institucionales oficiales de la Dirección Provincial de Recursos Hídricos (DPRH Jujuy)
Relevados y provistos oficialmente por el organismo.
Incluye CRUD dinámico de catálogos y persistencia dual en PostgreSQL / SQLite.
"""

from typing import List, Dict, Any, Optional
from backend.database import get_db_connection
from backend.services.auditoria_service import registrar_auditoria
from backend.services import organigrama_service

# Valores oficiales estáticos de respaldo
LUGARES_TRABAJO = [
    "Oficina Central",
    "Lote",
    "COREBE",
    "Maimará",
    "Unidad Operativa El Carmen",
    "Catamontaña",
    "Las Maderas",
    "La Ciénaga",
    "Derivador El Tipal",
    "Los Alisos",
    "Derivador Los Molinos",
    "Otro"
]

FUNCIONES = [
    "Jefe",
    "Electricista",
    "Compartidor de Riego",
    "Soldador",
    "Limpieza",
    "Maestranza",
    "Mecánico",
    "Maquinista",
    "Encargado de Combustible",
    "Administrativo",
    "Inspector",
    "Observador Meteorológico",
    "Cajero",
    "Electromecánico",
    "Fotógrafo",
    "Guardadique",
    "Telefonista",
    "Profesional"
]

DIRECCIONES_ORGANISMO = [
    "Dirección Provincial de Recursos Hídricos",
    "Dirección General de Gestión de Recursos Hídricos",
    "Dirección General del Sistema Integrado de Diques"
]

AREAS_TRABAJO = [
    "Área de Recursos Humanos",
    "Área de Administración General",
    "Área de Gestión e Ingresos Generales"
]

DEPARTAMENTOS = [
    "Departamento Manejo Integrado de Diques",
    "Departamento de Ingeniería Hidráulica",
    "Departamento de Secretaría General"
]

DIVISIONES = [
    "División de Planificación Hídrica",
    "División de Obras",
    "División de Mantenimiento de Equipos",
    "División de Regulación Hídrica",
    "División de Despacho",
    "División de Asesoría Jurídica",
    "División de Registro de Datos",
    "División de Personal",
    "División de Compras",
    "División de Tesorería",
    "División de Stock e Inventario",
    "División de Presupuesto y Contabilidad",
    "División de Remuneraciones",
    "División de Concesiones de Uso",
    "División de Relaciones Institucionales y Adción de Consorcios",
    "División de Áridos, Minas, Pozos y Otros",
    "División de Cobranzas",
    "División de Planificación Estratégica y Auditoría Interna",
    "Mesa del Agua",
    "División de Inspección y Mantenimiento"
]

SECTORES = [
    "Sector de Logística",
    "Sector de Mesa de Entrada",
    "Sector de Archivo",
    "Sector de Higiene y Seguridad",
    "Sector de Certificaciones Laborales",
    "Sector de Maestranza y Vigilancia",
    "Sector de Intimaciones y Asuntos Legales",
    "Sector de Planificación y Proyectos",
    "Sector de Sistema de Información de Embalse",
    "Sector de Sistema de Riego Regulado"
]

SITUACIONES_REVISTA = [
    "Planta Permanente",
    "Contrato de Locación de Servicios",
    "Decreto",
    "Contrato de Obra",
    "Adscrito",
    "Gabinete"
]

TIPOS_ASISTENCIA = [
    "Reloj",
    "Planilla",
    "Resolución"
]

SEXOS = [
    "Mujer",
    "Varón",
    "Otro"
]

GREMIOS = [
    "UPCN",
    "ATE",
    "ATSA",
    "Otro / Sin Gremio"
]

# -------------------------------------------------------------------
# 1. SITUACIONES DE REVISTA (CRUD)
# -------------------------------------------------------------------

def listar_situaciones_revista() -> List[Dict[str, Any]]:
    """Obtiene el listado dinámico de situaciones de revista."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM situaciones_revista_catalogo ORDER BY orden ASC, id ASC")
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[CATALOGOS] Error al listar situaciones_revista_catalogo: {e}")
    finally:
        conn.close()

    return [{"id": idx + 1, "nombre": nom, "descripcion": "", "activo": 1, "orden": idx + 1} for idx, nom in enumerate(SITUACIONES_REVISTA)]

def agregar_situacion_revista(data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Agrega una nueva situación de revista al catálogo."""
    if isinstance(data, str):
        data = {"nombre": data}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        raise ValueError("El nombre de la situación de revista es obligatorio.")
    descripcion = data.get("descripcion", "")
    activo = int(data.get("activo", 1))
    orden = int(data.get("orden", 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO situaciones_revista_catalogo (nombre, descripcion, activo, orden)
        VALUES (?, ?, ?, ?)
    """, (nombre, descripcion, activo, orden))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "situaciones_revista_catalogo", nuevo_id, f"Situación de revista creada: '{nombre}'", usuario)
    return {"success": True, "id": nuevo_id, "nombre": nombre}

def editar_situacion_revista(item_id: int, data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Edita una situación de revista existente."""
    if isinstance(data, str):
        data = {"nombre": data}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM situaciones_revista_catalogo WHERE id = ?", (item_id,))
    actual = cursor.fetchone()
    if not actual:
        conn.close()
        raise ValueError(f"Situación de revista ID {item_id} no encontrada.")

    nombre = data.get("nombre", actual["nombre"]).strip()
    descripcion = data.get("descripcion", actual["descripcion"])
    activo = int(data.get("activo", actual["activo"]))
    orden = int(data.get("orden", actual["orden"]))

    cursor.execute("""
        UPDATE situaciones_revista_catalogo
        SET nombre = ?, descripcion = ?, activo = ?, orden = ?
        WHERE id = ?
    """, (nombre, descripcion, activo, orden, item_id))
    conn.commit()
    conn.close()

    registrar_auditoria("EDITAR", "situaciones_revista_catalogo", item_id, f"Situación de revista actualizada: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

def eliminar_situacion_revista(item_id: int, usuario: str = "Admin") -> Dict[str, Any]:
    """Elimina una situación de revista del catálogo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM situaciones_revista_catalogo WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Situación de revista ID {item_id} no encontrada.")
    nombre = row["nombre"]

    cursor.execute("DELETE FROM situaciones_revista_catalogo WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    registrar_auditoria("ELIMINAR_DEFINITIVO", "situaciones_revista_catalogo", item_id, f"Situación de revista eliminada: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

# -------------------------------------------------------------------
# 2. LUGARES DE TRABAJO (CRUD)
# -------------------------------------------------------------------

def listar_lugares_trabajo() -> List[Dict[str, Any]]:
    """Obtiene el listado dinámico de lugares de trabajo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM lugares_trabajo_catalogo ORDER BY orden ASC, id ASC")
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[CATALOGOS] Error al listar lugares_trabajo_catalogo: {e}")
    finally:
        conn.close()

    return [{"id": idx + 1, "nombre": nom, "descripcion": "", "activo": 1, "orden": idx + 1} for idx, nom in enumerate(LUGARES_TRABAJO)]

def agregar_lugar_trabajo(data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Agrega un nuevo lugar de trabajo al catálogo."""
    if isinstance(data, str):
        data = {"nombre": data}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        raise ValueError("El nombre del lugar de trabajo es obligatorio.")
    descripcion = data.get("descripcion", "")
    activo = int(data.get("activo", 1))
    orden = int(data.get("orden", 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO lugares_trabajo_catalogo (nombre, descripcion, activo, orden)
        VALUES (?, ?, ?, ?)
    """, (nombre, descripcion, activo, orden))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "lugares_trabajo_catalogo", nuevo_id, f"Lugar de trabajo creado: '{nombre}'", usuario)
    return {"success": True, "id": nuevo_id, "nombre": nombre}

def editar_lugar_trabajo(item_id: int, data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Edita un lugar de trabajo existente."""
    if isinstance(data, str):
        data = {"nombre": data}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM lugares_trabajo_catalogo WHERE id = ?", (item_id,))
    actual = cursor.fetchone()
    if not actual:
        conn.close()
        raise ValueError(f"Lugar de trabajo ID {item_id} no encontrado.")

    nombre = data.get("nombre", actual["nombre"]).strip()
    descripcion = data.get("descripcion", actual["descripcion"])
    activo = int(data.get("activo", actual["activo"]))
    orden = int(data.get("orden", actual["orden"]))

    cursor.execute("""
        UPDATE lugares_trabajo_catalogo
        SET nombre = ?, descripcion = ?, activo = ?, orden = ?
        WHERE id = ?
    """, (nombre, descripcion, activo, orden, item_id))
    conn.commit()
    conn.close()

    registrar_auditoria("EDITAR", "lugares_trabajo_catalogo", item_id, f"Lugar de trabajo actualizado: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

def eliminar_lugar_trabajo(item_id: int, usuario: str = "Admin") -> Dict[str, Any]:
    """Elimina un lugar de trabajo del catálogo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM lugares_trabajo_catalogo WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Lugar de trabajo ID {item_id} no encontrado.")
    nombre = row["nombre"]

    cursor.execute("DELETE FROM lugares_trabajo_catalogo WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    registrar_auditoria("ELIMINAR_DEFINITIVO", "lugares_trabajo_catalogo", item_id, f"Lugar de trabajo eliminado: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

# -------------------------------------------------------------------
# 3. FUNCIONES OFICIALES (CRUD)
# -------------------------------------------------------------------

def listar_funciones() -> List[Dict[str, Any]]:
    """Obtiene el listado dinámico de funciones del catálogo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM funciones_catalogo ORDER BY orden ASC, id ASC")
        rows = cursor.fetchall()
        if rows:
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"[CATALOGOS] Error al listar funciones_catalogo: {e}")
    finally:
        conn.close()

    return [{"id": idx + 1, "nombre": nom, "descripcion": "", "activo": 1, "orden": idx + 1} for idx, nom in enumerate(FUNCIONES)]

def agregar_funcion(data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Agrega una nueva función al catálogo."""
    if isinstance(data, str):
        data = {"nombre": data}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        raise ValueError("El nombre de la función es obligatorio.")
    descripcion = data.get("descripcion", "")
    activo = int(data.get("activo", 1))
    orden = int(data.get("orden", 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO funciones_catalogo (nombre, descripcion, activo, orden)
        VALUES (?, ?, ?, ?)
    """, (nombre, descripcion, activo, orden))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "funciones_catalogo", nuevo_id, f"Función creada: '{nombre}'", usuario)
    return {"success": True, "id": nuevo_id, "nombre": nombre}

def editar_funcion(item_id: int, data: Any, usuario: str = "Admin") -> Dict[str, Any]:
    """Edita una función oficial existente."""
    if isinstance(data, str):
        data = {"nombre": data}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, descripcion, activo, orden FROM funciones_catalogo WHERE id = ?", (item_id,))
    actual = cursor.fetchone()
    if not actual:
        conn.close()
        raise ValueError(f"Función ID {item_id} no encontrada.")

    nombre = data.get("nombre", actual["nombre"]).strip()
    descripcion = data.get("descripcion", actual["descripcion"])
    activo = int(data.get("activo", actual["activo"]))
    orden = int(data.get("orden", actual["orden"]))

    cursor.execute("""
        UPDATE funciones_catalogo
        SET nombre = ?, descripcion = ?, activo = ?, orden = ?
        WHERE id = ?
    """, (nombre, descripcion, activo, orden, item_id))
    conn.commit()
    conn.close()

    registrar_auditoria("EDITAR", "funciones_catalogo", item_id, f"Función actualizada: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

def eliminar_funcion(item_id: int, usuario: str = "Admin") -> Dict[str, Any]:
    """Elimina una función del catálogo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM funciones_catalogo WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Función ID {item_id} no encontrada.")
    nombre = row["nombre"]

    cursor.execute("DELETE FROM funciones_catalogo WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

    registrar_auditoria("ELIMINAR_DEFINITIVO", "funciones_catalogo", item_id, f"Función eliminada: '{nombre}'", usuario)
    return {"success": True, "id": item_id, "nombre": nombre}

# -------------------------------------------------------------------
# 4. ÁREAS / DEPENDENCIAS (Integrado con organigrama_service)
# -------------------------------------------------------------------

def listar_areas() -> List[Dict[str, Any]]:
    """Obtiene el listado de áreas de la DPRH integrado con organigrama."""
    return organigrama_service.listar_areas()

def agregar_area(data: dict, usuario: str = "Admin") -> Dict[str, Any]:
    """Agrega una nueva área delegando a organigrama_service."""
    nuevo_id = organigrama_service.crear_area(data, usuario=usuario)
    return {"success": True, "id": nuevo_id, "nombre": data.get("nombre")}

def editar_area(area_id: int, data: dict, usuario: str = "Admin") -> Dict[str, Any]:
    """Edita un área existente delegando a organigrama_service."""
    res = organigrama_service.actualizar_area(area_id, data, usuario=usuario)
    return {"success": True, "id": area_id, **res}

def eliminar_area(area_id: int, usuario: str = "Admin") -> Dict[str, Any]:
    """Elimina un área delegando a organigrama_service."""
    res = organigrama_service.eliminar_area(area_id, usuario=usuario)
    return {"success": True, "id": area_id, **res}

# -------------------------------------------------------------------
# 5. CATÁLOGOS CONSOLIDADOS
# -------------------------------------------------------------------

def obtener_todos_catalogos() -> Dict[str, Any]:
    """Retorna todos los catálogos institucionales con datos dinámicos."""
    try:
        revistas = [r["nombre"] for r in listar_situaciones_revista()]
    except Exception:
        revistas = SITUACIONES_REVISTA

    try:
        lugares = [l["nombre"] for l in listar_lugares_trabajo()]
    except Exception:
        lugares = LUGARES_TRABAJO

    try:
        funcs = [f["nombre"] for f in listar_funciones()]
    except Exception:
        funcs = FUNCIONES

    return {
        "lugares_trabajo": lugares or LUGARES_TRABAJO,
        "funciones": funcs or FUNCIONES,
        "direcciones_organismo": DIRECCIONES_ORGANISMO,
        "areas_trabajo": AREAS_TRABAJO,
        "departamentos": DEPARTAMENTOS,
        "divisiones": DIVISIONES,
        "sectores": SECTORES,
        "situaciones_revista": revistas or SITUACIONES_REVISTA,
        "tipos_asistencia": TIPOS_ASISTENCIA,
        "sexos": SEXOS,
        "gremios": GREMIOS
    }

import sqlite3
from backend.database import get_db_connection
from backend.services.auditoria_service import registrar_auditoria

def listar_areas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, 
               (SELECT COUNT(*) FROM personal p WHERE p.area_id = a.id AND p.deleted_at IS NULL) AS total_personal
        FROM areas a 
        ORDER BY a.nivel ASC, a.orden ASC, a.nombre ASC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obtener_arbol_organigrama():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.*, 
               (SELECT COUNT(*) FROM personal p WHERE p.area_id = a.id AND p.deleted_at IS NULL) AS total_personal
        FROM areas a 
        ORDER BY a.nivel ASC, a.orden ASC
    """)
    areas = [dict(row) for row in cursor.fetchall()]
    
    # Obtener el personal asignado a cada área
    cursor.execute("""
        SELECT id, nombre, apellido, cargo, funcion, dni, situacion_revista, estado, area_id
        FROM personal
        WHERE deleted_at IS NULL
    """)
    personal_list = [dict(row) for row in cursor.fetchall()]
    conn.close()

    area_map = {}
    for a in areas:
        a["personal"] = [p for p in personal_list if p["area_id"] == a["id"]]
        a["subareas"] = []
        area_map[a["id"]] = a

    tree = []
    for a in areas:
        parent_id = a.get("parent_id")
        if parent_id and parent_id in area_map:
            area_map[parent_id]["subareas"].append(a)
        else:
            tree.append(a)

    return tree

def crear_area(data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO areas (nombre, codigo, nivel, parent_id, responsable, descripcion, orden)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("nombre"), data.get("codigo"), data.get("nivel", 1),
        data.get("parent_id"), data.get("responsable"), data.get("descripcion"),
        data.get("orden", 0)
    ))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    registrar_auditoria("CREAR", "areas", nuevo_id, f"Creación de área '{data.get('nombre')}'", usuario)
    return nuevo_id

def actualizar_area(area_id: int, data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE areas SET nombre = ?, codigo = ?, nivel = ?, parent_id = ?, responsable = ?, descripcion = ?, orden = ?
        WHERE id = ?
    """, (
        data.get("nombre"), data.get("codigo"), data.get("nivel", 1),
        data.get("parent_id"), data.get("responsable"), data.get("descripcion"),
        data.get("orden", 0), area_id
    ))
    conn.commit()
    conn.close()
    registrar_auditoria("EDITAR", "areas", area_id, f"Actualización de área '{data.get('nombre')}'", usuario)
    return {"success": True}

def eliminar_area(area_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal SET area_id = NULL WHERE area_id = ?", (area_id,))
    cursor.execute("DELETE FROM areas WHERE id = ?", (area_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR_DEFINITIVO", "areas", area_id, f"Eliminación de área ID {area_id}", usuario)
    return {"success": True}


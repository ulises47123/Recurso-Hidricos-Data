import sqlite3
from datetime import datetime
from backend.database import get_db_connection
from backend.services.auditoria_service import registrar_auditoria

def listar_personal(busqueda: str = "", area_id: int = None, situacion_revista: str = "", estado: str = "", ordenar_por: str = "id", orden: str = "DESC", incluir_eliminados: bool = False, ids: list = None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT p.*, a.nombre AS area_nombre, a.codigo AS area_codigo
        FROM personal p
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE 1=1
    """
    params = []

    if not incluir_eliminados:
        query += " AND p.deleted_at IS NULL"
    else:
        query += " AND p.deleted_at IS NOT NULL"

    if ids:
        placeholders = ",".join(["?"] * len(ids))
        query += f" AND p.id IN ({placeholders})"
        params.extend(ids)

    if busqueda:
        term = f"%{busqueda.strip()}%"
        query += " AND (p.nombre LIKE ? OR p.apellido LIKE ? OR p.dni LIKE ? OR p.legajo LIKE ? OR p.funcion LIKE ? OR p.cargo LIKE ? OR a.nombre LIKE ?)"
        params.extend([term, term, term, term, term, term, term])

    if area_id:
        query += " AND p.area_id = ?"
        params.append(area_id)

    if situacion_revista:
        query += " AND p.situacion_revista = ?"
        params.append(situacion_revista)

    if estado:
        query += " AND p.estado = ?"
        params.append(estado)

    # Validar ordenamiento seguro (prevención SQL Injection)
    columnas_validas = ["id", "nombre", "apellido", "dni", "legajo", "situacion_revista", "cargo", "funcion", "estado", "fecha_ingreso", "area_nombre"]
    col_orden = ordenar_por if ordenar_por in columnas_validas else "id"
    direccion = "ASC" if orden.upper() == "ASC" else "DESC"

    if col_orden == "area_nombre":
        query += f" ORDER BY a.nombre {direccion}"
    else:
        query += f" ORDER BY p.{col_orden} {direccion}"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def calcular_anios_meses(fecha_str: str):
    if not fecha_str:
        return {"anios": 0, "meses": 0, "dias": 0, "texto": "Sin registrar"}
    try:
        f = datetime.strptime(fecha_str.strip(), "%Y-%m-%d").date()
        hoy = datetime.now().date()
        if f > hoy:
            return {"anios": 0, "meses": 0, "dias": 0, "texto": "Fecha futura"}
        
        anios = hoy.year - f.year
        meses = hoy.month - f.month
        dias = hoy.day - f.day
        if dias < 0:
            meses -= 1
            dias += 30
        if meses < 0:
            anios -= 1
            meses += 12
            
        texto = f"{anios} años, {meses} meses" if anios > 0 else f"{meses} meses, {dias} días"
        return {"anios": anios, "meses": meses, "dias": dias, "texto": texto}
    except Exception:
        return {"anios": 0, "meses": 0, "dias": 0, "texto": "Sin registrar"}

def obtener_personal_por_id(personal_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, a.nombre AS area_nombre, a.codigo AS area_codigo
        FROM personal p
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE p.id = ?
    """, (personal_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    
    item = dict(row)

    # Cálculos automáticos de edad y antigüedades según pedido oficial de Geovana (DPRH)
    edad_info = calcular_anios_meses(item.get("fecha_nacimiento"))
    item["edad_calculada"] = edad_info["anios"] if item.get("fecha_nacimiento") else None
    item["antiguedad_admin_pub_calc"] = calcular_anios_meses(item.get("fecha_ingreso_admin_pub"))["texto"]
    item["antiguedad_obra_calc"] = calcular_anios_meses(item.get("fecha_ingreso_recursos_hidricos_obra"))["texto"]
    item["antiguedad_planta_calc"] = calcular_anios_meses(item.get("fecha_ingreso_recursos_hidricos_planta"))["texto"]

    # Familiares y beneficiarios
    cursor.execute("SELECT * FROM familiares WHERE personal_id = ? ORDER BY id ASC", (personal_id,))
    item["familiares"] = [dict(r) for r in cursor.fetchall()]

    # Historial de cargos y funciones
    cursor.execute("""
        SELECT hf.*, a.nombre as area_nombre 
        FROM historial_funciones hf
        LEFT JOIN areas a ON hf.area_id = a.id
        WHERE hf.personal_id = ?
        ORDER BY hf.fecha_desde DESC
    """, (personal_id,))
    item["historial_funciones"] = [dict(r) for r in cursor.fetchall()]

    # Documentos del legajo digital
    cursor.execute("SELECT * FROM documentos_legajo WHERE personal_id = ? ORDER BY fecha_subida DESC", (personal_id,))
    item["documentos_legajo"] = [dict(r) for r in cursor.fetchall()]

    # Adicionales registrados
    cursor.execute("SELECT * FROM adicionales_personal WHERE personal_id = ? ORDER BY fecha_alta DESC", (personal_id,))
    item["adicionales"] = [dict(r) for r in cursor.fetchall()]

    # Historial de categorías
    cursor.execute("SELECT * FROM historial_categorias WHERE personal_id = ? ORDER BY fecha_cambio DESC", (personal_id,))
    item["historial_categorias"] = [dict(r) for r in cursor.fetchall()]

    # Registro Artículo 79 (Cumpleaños y cobros)
    cursor.execute("SELECT * FROM beneficios_articulo_79 WHERE personal_id = ? ORDER BY anio_periodo DESC", (personal_id,))
    item["beneficios_articulo_79"] = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return item


def crear_personal(data: dict, usuario: str = "Admin"):
    dni = data.get("dni")
    legajo = data.get("legajo")

    conn = get_db_connection()
    cursor = conn.cursor()

    if dni:
        cursor.execute("SELECT id FROM personal WHERE dni = ?", (dni,))
        if cursor.fetchone():
            conn.close()
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Ya existe un agente registrado con el DNI N° {dni}.")

    if legajo:
        cursor.execute("SELECT id FROM personal WHERE legajo = ?", (legajo,))
        if cursor.fetchone():
            conn.close()
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Ya existe un agente registrado con el N° de Legajo {legajo}.")

    cursor.execute("""
        INSERT INTO personal (
            dni, cuil, legajo, nombre, apellido, email, telefono, 
            fecha_nacimiento, genero, direccion, fecha_ingreso, 
            fecha_ingreso_admin_pub, fecha_ingreso_recursos_hidricos_obra, fecha_ingreso_recursos_hidricos_planta,
            asistencia, categoria_actual, categoria_fecha_alta,
            situacion_revista, situacion_revista_obs, lugar_trabajo, lugar_trabajo_otro,
            sentencia, actividad, cargo, funcion, profesional_titulo,
            direccion_organismo, area_trabajo, departamento_trabajo, division_trabajo, sector_trabajo,
            area_id, horario, gremio, estado, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
    """, (
        data.get("dni"), data.get("cuil"), data.get("legajo"), data.get("nombre"), data.get("apellido"),
        data.get("email"), data.get("telefono"), data.get("fecha_nacimiento"),
        data.get("genero", "Otro"), data.get("direccion"), data.get("fecha_ingreso"),
        data.get("fecha_ingreso_admin_pub"), data.get("fecha_ingreso_recursos_hidricos_obra"), data.get("fecha_ingreso_recursos_hidricos_planta"),
        data.get("asistencia", "Reloj"), data.get("categoria_actual"), data.get("categoria_fecha_alta"),
        data.get("situacion_revista", "Planta Permanente"), data.get("situacion_revista_obs"),
        data.get("lugar_trabajo", "Oficina Central"), data.get("lugar_trabajo_otro"),
        data.get("sentencia"), data.get("actividad"), data.get("cargo"), data.get("funcion"), data.get("profesional_titulo"),
        data.get("direccion_organismo", "Dirección Provincial de Recursos Hídricos"),
        data.get("area_trabajo"), data.get("departamento_trabajo"), data.get("division_trabajo"), data.get("sector_trabajo"),
        data.get("area_id"), data.get("horario", "07:00 a 13:00"), data.get("gremio"), data.get("estado", "Activo")
    ))

    nuevo_id = cursor.lastrowid

    # Si se cargó categoría inicial, guardar en historial_categorias
    if data.get("categoria_actual"):
        cursor.execute("""
            INSERT INTO historial_categorias (personal_id, categoria, fecha_cambio, resolucion_numero, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """, (nuevo_id, data.get("categoria_actual"), data.get("categoria_fecha_alta") or datetime.now().strftime("%Y-%m-%d"), "Alta Inicial", "Categoría asignada al ingresar"))

    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "personal", nuevo_id, f"Alta de personal DPRH: {data.get('nombre')} {data.get('apellido')} (Legajo: {data.get('legajo')})", usuario)
    return obtener_personal_por_id(nuevo_id)

def actualizar_personal(personal_id: int, data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar si cambió la categoría para registrar en historial
    cursor.execute("SELECT categoria_actual FROM personal WHERE id = ?", (personal_id,))
    prev_cat_row = cursor.fetchone()
    prev_cat = prev_cat_row[0] if prev_cat_row else None
    nueva_cat = data.get("categoria_actual")

    if nueva_cat and nueva_cat != prev_cat:
        cursor.execute("""
            INSERT INTO historial_categorias (personal_id, categoria, fecha_cambio, resolucion_numero, observaciones)
            VALUES (?, ?, ?, ?, ?)
        """, (personal_id, nueva_cat, data.get("categoria_fecha_alta") or datetime.now().strftime("%Y-%m-%d"), "Actualización de Categoría", f"Cambio de {prev_cat} a {nueva_cat}"))

    cursor.execute("""
        UPDATE personal SET
            dni = ?, cuil = ?, legajo = ?, nombre = ?, apellido = ?, email = ?,
            telefono = ?, fecha_nacimiento = ?, genero = ?, direccion = ?,
            fecha_ingreso = ?, fecha_ingreso_admin_pub = ?, fecha_ingreso_recursos_hidricos_obra = ?, fecha_ingreso_recursos_hidricos_planta = ?,
            asistencia = ?, categoria_actual = ?, categoria_fecha_alta = ?,
            situacion_revista = ?, situacion_revista_obs = ?, lugar_trabajo = ?, lugar_trabajo_otro = ?,
            sentencia = ?, actividad = ?, cargo = ?, funcion = ?, profesional_titulo = ?,
            direccion_organismo = ?, area_trabajo = ?, departamento_trabajo = ?, division_trabajo = ?, sector_trabajo = ?,
            area_id = ?, horario = ?, gremio = ?, estado = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        data.get("dni"), data.get("cuil"), data.get("legajo"), data.get("nombre"), data.get("apellido"),
        data.get("email"), data.get("telefono"), data.get("fecha_nacimiento"),
        data.get("genero", "Otro"), data.get("direccion"), data.get("fecha_ingreso"),
        data.get("fecha_ingreso_admin_pub"), data.get("fecha_ingreso_recursos_hidricos_obra"), data.get("fecha_ingreso_recursos_hidricos_planta"),
        data.get("asistencia", "Reloj"), data.get("categoria_actual"), data.get("categoria_fecha_alta"),
        data.get("situacion_revista", "Planta Permanente"), data.get("situacion_revista_obs"),
        data.get("lugar_trabajo", "Oficina Central"), data.get("lugar_trabajo_otro"),
        data.get("sentencia"), data.get("actividad"), data.get("cargo"), data.get("funcion"), data.get("profesional_titulo"),
        data.get("direccion_organismo", "Dirección Provincial de Recursos Hídricos"),
        data.get("area_trabajo"), data.get("departamento_trabajo"), data.get("division_trabajo"), data.get("sector_trabajo"),
        data.get("area_id"), data.get("horario", "07:00 a 13:00"), data.get("gremio"), data.get("estado", "Activo"),
        personal_id
    ))

    conn.commit()
    conn.close()

    registrar_auditoria("EDITAR", "personal", personal_id, f"Edición de personal ID: {personal_id}", usuario)
    return obtener_personal_por_id(personal_id)


def mover_a_papelera(personal_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (personal_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR_PAPELERA", "personal", personal_id, f"Personal ID {personal_id} enviado a papelera", usuario)
    return True

def restaurar_personal(personal_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE personal SET deleted_at = NULL WHERE id = ?", (personal_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("RESTAURAR", "personal", personal_id, f"Personal ID {personal_id} restaurado desde papelera", usuario)
    return True

def eliminar_definitivo(personal_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Eliminar registros asociados en tablas hijas para evitar fallos de clave foránea (FK)
        cursor.execute("DELETE FROM licencias WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM familiares WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM historial_funciones WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM documentos_legajo WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM adicionales_personal WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM historial_categorias WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM beneficios_articulo_79 WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM compensatorios_saldo WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM compensatorios_cargas WHERE personal_id = ?", (personal_id,))
        cursor.execute("DELETE FROM compensatorios_solicitudes WHERE personal_id = ?", (personal_id,))
        
        cursor.execute("DELETE FROM personal WHERE id = ?", (personal_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e
    conn.close()
    registrar_auditoria("ELIMINAR_DEFINITIVO", "personal", personal_id, f"Personal ID {personal_id} eliminado de forma permanente con su historial", usuario)
    return True

def vaciar_papelera(usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM licencias WHERE deleted_at IS NOT NULL")
    cursor.execute("DELETE FROM personal WHERE deleted_at IS NOT NULL")
    conn.commit()
    conn.close()
    registrar_auditoria("VACIAR_PAPELERA", "todos", None, "Papelera de reciclaje vaciada completamente", usuario)
    return True

# -------------------------------------------------------------
# FAMILIARES Y BENEFICIARIOS (Req B2)
# -------------------------------------------------------------
def listar_familiares(personal_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM familiares WHERE personal_id = ? ORDER BY id ASC", (personal_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def agregar_familiar(data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO familiares (personal_id, nombre, apellido, dni, parentesco, fecha_nacimiento, es_beneficiario, observaciones)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("personal_id"), data.get("nombre"), data.get("apellido"),
        data.get("dni"), data.get("parentesco"), data.get("fecha_nacimiento"),
        data.get("es_beneficiario", 1), data.get("observaciones")
    ))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    registrar_auditoria("CREAR", "familiares", nuevo_id, f"Familiar registrado: {data.get('nombre')} {data.get('apellido')} ({data.get('parentesco')}) para Personal ID {data.get('personal_id')}", usuario)
    return {"id": nuevo_id, "success": True}

def eliminar_familiar(familiar_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM familiares WHERE id = ?", (familiar_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR_DEFINITIVO", "familiares", familiar_id, f"Familiar ID {familiar_id} eliminado", usuario)
    return {"success": True}

# -------------------------------------------------------------
# HISTORIAL DE FUNCIONES / CAMBIOS DE CARGO (Req F6)
# -------------------------------------------------------------
def registrar_cambio_funcion(data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Cerrar la función anterior si no tiene fecha_hasta
    cursor.execute("""
        UPDATE historial_funciones 
        SET fecha_hasta = ? 
        WHERE personal_id = ? AND fecha_hasta IS NULL
    """, (data.get("fecha_desde"), data.get("personal_id")))

    cursor.execute("""
        INSERT INTO historial_funciones (personal_id, cargo, funcion, area_id, fecha_desde, fecha_hasta, motivo_cambio, instrumento_legal)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("personal_id"), data.get("cargo"), data.get("funcion"),
        data.get("area_id"), data.get("fecha_desde"), data.get("fecha_hasta"),
        data.get("motivo_cambio"), data.get("instrumento_legal")
    ))
    nuevo_id = cursor.lastrowid

    # Actualizar también los datos actuales en tabla personal
    cursor.execute("""
        UPDATE personal SET cargo = ?, funcion = ?, area_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data.get("cargo"), data.get("funcion"), data.get("area_id"), data.get("personal_id")))

    conn.commit()
    conn.close()
    registrar_auditoria("EDITAR", "historial_funciones", nuevo_id, f"Cambio de función registrado para Personal ID {data.get('personal_id')}: {data.get('cargo')} - {data.get('funcion')}", usuario)
    return {"id": nuevo_id, "success": True}

# -------------------------------------------------------------
# DOCUMENTOS DE LEGAJO DIGITAL (Req B3)
# -------------------------------------------------------------
def registrar_documento_legajo(personal_id: int, tipo_documento: str, titulo: str, nombre_archivo: str, ruta_archivo: str, observaciones: str = "", usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO documentos_legajo (personal_id, tipo_documento, titulo, nombre_archivo, ruta_archivo, observaciones)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (personal_id, tipo_documento, titulo, nombre_archivo, ruta_archivo, observaciones))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    registrar_auditoria("CREAR", "documentos_legajo", nuevo_id, f"Documento '{titulo}' adjuntado al legajo de Personal ID {personal_id}", usuario)
    return {"id": nuevo_id, "success": True}

def eliminar_documento_legajo(documento_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ruta_archivo FROM documentos_legajo WHERE id = ?", (documento_id,))
    row = cursor.fetchone()
    if row and row[0]:
        import os
        if os.path.exists(row[0]):
            try:
                os.remove(row[0])
            except Exception:
                pass
    cursor.execute("DELETE FROM documentos_legajo WHERE id = ?", (documento_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR_DEFINITIVO", "documentos_legajo", documento_id, f"Documento ID {documento_id} eliminado del legajo digital", usuario)
    return {"success": True}


import sqlite3
from datetime import datetime, timedelta
from backend.database import get_db_connection
from backend.services.auditoria_service import registrar_auditoria

def es_dia_habil(fecha_dt, set_feriados):
    """Retorna True si la fecha es de lunes a viernes y no está en la lista de feriados."""
    if fecha_dt.weekday() >= 5: # 5: Sábado, 6: Domingo
        return False
    fecha_str = fecha_dt.strftime("%Y-%m-%d")
    if fecha_str in set_feriados:
        return False
    return True

def obtener_feriados_set():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fecha FROM feriados")
    feriados = {row["fecha"] for row in cursor.fetchall()}
    conn.close()
    return feriados

def obtener_feriados_dict():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, descripcion FROM feriados")
    feriados = {row["fecha"]: row["descripcion"] for row in cursor.fetchall()}
    conn.close()
    return feriados

def calcular_dias_habiles(fecha_inicio_str: str, fecha_fin_str: str) -> int:
    """Calcula la cantidad de días hábiles entre fecha_inicio y fecha_fin inclusivas."""
    detalle = calcular_dias_habiles_detalle(fecha_inicio_str, fecha_fin_str)
    return detalle["dias_habiles"]

def calcular_dias_habiles_detalle(fecha_inicio_str: str, fecha_fin_str: str) -> dict:
    """Calcula los días hábiles y devuelve el desglose de días, fines de semana y feriados."""
    try:
        f_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d")
        f_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d")
    except ValueError:
        return {"dias_habiles": 0, "total_dias": 0, "fines_semana": 0, "feriados": [], "dias_habiles_fechas": []}

    if f_inicio > f_fin:
        return {"dias_habiles": 0, "total_dias": 0, "fines_semana": 0, "feriados": [], "dias_habiles_fechas": []}

    feriados_dict = obtener_feriados_dict()
    dias_habiles = 0
    total_dias = 0
    fines_semana = 0
    feriados_encontrados = []
    dias_habiles_fechas = []

    curr = f_inicio
    while curr <= f_fin:
        total_dias += 1
        curr_str = curr.strftime("%Y-%m-%d")
        if curr.weekday() >= 5:
            fines_semana += 1
        elif curr_str in feriados_dict:
            feriados_encontrados.append({
                "fecha": curr_str,
                "descripcion": feriados_dict[curr_str]
            })
        else:
            dias_habiles += 1
            dias_habiles_fechas.append(curr_str)
        curr += timedelta(days=1)

    return {
        "dias_habiles": dias_habiles,
        "total_dias": total_dias,
        "fines_semana": fines_semana,
        "feriados": feriados_encontrados,
        "dias_habiles_fechas": dias_habiles_fechas
    }

def listar_feriados():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, fecha, descripcion FROM feriados ORDER BY fecha ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def crear_feriado(data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feriados (fecha, descripcion) VALUES (?, ?)", (data["fecha"], data["descripcion"]))
    feriado_id = cursor.lastrowid
    conn.commit()
    conn.close()
    registrar_auditoria("CREAR", "feriados", feriado_id, f"Feriado agregado: {data['fecha']} - {data['descripcion']}", usuario)
    return {"id": feriado_id, "fecha": data["fecha"], "descripcion": data["descripcion"]}

def eliminar_feriado(feriado_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feriados WHERE id = ?", (feriado_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("Feriado no encontrado.")
    cursor.execute("DELETE FROM feriados WHERE id = ?", (feriado_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR", "feriados", feriado_id, f"Feriado eliminado: {row['fecha']} - {row['descripcion']}", usuario)
    return {"success": True}

def obtener_saldo_agente(personal_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM compensatorios_saldo WHERE personal_id = ?", (personal_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"personal_id": personal_id, "dias_disponibles": 0.0, "fecha_ultima_carga": None}

def cargar_dias_compensatorios(data: dict, usuario: str = "Admin"):
    """Carga días a favor de un agente e incrementa su saldo."""
    personal_id = data["personal_id"]
    dias = float(data["dias"])
    fecha_carga = data["fecha_carga"]
    motivo = data.get("motivo", "")
    acta_numero = data.get("acta_numero", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Registrar en historial de cargas
    cursor.execute("""
        INSERT INTO compensatorios_cargas (personal_id, dias, fecha_carga, motivo, acta_numero)
        VALUES (?, ?, ?, ?, ?)
    """, (personal_id, dias, fecha_carga, motivo, acta_numero))
    carga_id = cursor.lastrowid

    # Actualizar o insertar saldo
    cursor.execute("SELECT dias_disponibles FROM compensatorios_saldo WHERE personal_id = ?", (personal_id,))
    row = cursor.fetchone()
    if row:
        nuevo_saldo = row["dias_disponibles"] + dias
        cursor.execute("""
            UPDATE compensatorios_saldo 
            SET dias_disponibles = ?, fecha_ultima_carga = ?, updated_at = CURRENT_TIMESTAMP
            WHERE personal_id = ?
        """, (nuevo_saldo, fecha_carga, personal_id))
    else:
        nuevo_saldo = dias
        cursor.execute("""
            INSERT INTO compensatorios_saldo (personal_id, dias_disponibles, fecha_ultima_carga)
            VALUES (?, ?, ?)
        """, (personal_id, nuevo_saldo, fecha_carga))

    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "compensatorios_cargas", carga_id, f"Carga de {dias} días compensatorios para agente ID {personal_id}", usuario)
    return {"success": True, "carga_id": carga_id, "nuevo_saldo": nuevo_saldo}

def solicitar_compensatorio(data: dict, usuario: str = "Admin"):
    """Registra una solicitud de compensatorio, calcula días hábiles y descuenta automáticamente del saldo."""
    personal_id = data["personal_id"]
    fecha_inicio = data["fecha_inicio"]
    fecha_fin = data["fecha_fin"]
    acta_numero = data.get("acta_numero", "")
    observaciones = data.get("observaciones", "")

    dias_habiles = calcular_dias_habiles(fecha_inicio, fecha_fin)
    if dias_habiles <= 0:
        raise ValueError("El rango de fechas no contiene días hábiles válidos.")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verificar saldo disponible
    cursor.execute("SELECT dias_disponibles FROM compensatorios_saldo WHERE personal_id = ?", (personal_id,))
    row = cursor.fetchone()
    saldo_actual = row["dias_disponibles"] if row else 0.0

    if saldo_actual < dias_habiles:
        conn.close()
        raise ValueError(f"Saldo insuficiente. El agente dispone de {saldo_actual} días y la solicitud requiere {dias_habiles} días hábiles.")

    # Descontar automáticamente del saldo
    nuevo_saldo = saldo_actual - dias_habiles
    cursor.execute("""
        UPDATE compensatorios_saldo 
        SET dias_disponibles = ?, updated_at = CURRENT_TIMESTAMP
        WHERE personal_id = ?
    """, (nuevo_saldo, personal_id))

    # Registrar solicitud
    cursor.execute("""
        INSERT INTO compensatorios_solicitudes (personal_id, fecha_inicio, fecha_fin, dias_descontados, acta_numero, estado, observaciones)
        VALUES (?, ?, ?, ?, ?, 'Pendiente', ?)
    """, (personal_id, fecha_inicio, fecha_fin, dias_habiles, acta_numero, observaciones))
    solicitud_id = cursor.lastrowid

    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "compensatorios_solicitudes", solicitud_id, f"Solicitud de {dias_habiles} días compensatorios para agente ID {personal_id}", usuario)
    return {
        "success": True, 
        "solicitud_id": solicitud_id, 
        "dias_descontados": dias_habiles, 
        "nuevo_saldo": nuevo_saldo
    }

def cambiar_estado_solicitud(solicitud_id: int, nuevo_estado: str, observaciones: str = "", usuario: str = "Admin"):
    """Permite cambiar el estado de la solicitud (Justificada / Aprobada / Autorizada, Pendiente, Observada, Rechazada). Si se rechaza, reembolsa los días al saldo del agente."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM compensatorios_solicitudes WHERE id = ?", (solicitud_id,))
    solicitud = cursor.fetchone()
    if not solicitud:
        conn.close()
        raise ValueError("Solicitud no encontrada")

    estado_anterior = solicitud["estado"]
    dias_descontados = solicitud["dias_descontados"]
    personal_id = solicitud["personal_id"]

    # Si pasa a Rechazada desde otro estado no rechazado, devolver el saldo descontado
    if nuevo_estado == "Rechazada" and estado_anterior != "Rechazada":
        cursor.execute("UPDATE compensatorios_saldo SET dias_disponibles = dias_disponibles + ? WHERE personal_id = ?", (dias_descontados, personal_id))
    # Si estaba Rechazada y pasa a otro estado (Aprobada/Pendiente/Justificada), volver a descontar
    elif estado_anterior == "Rechazada" and nuevo_estado != "Rechazada":
        cursor.execute("SELECT dias_disponibles FROM compensatorios_saldo WHERE personal_id = ?", (personal_id,))
        row = cursor.fetchone()
        saldo_actual = row["dias_disponibles"] if row else 0.0
        if saldo_actual < dias_descontados:
            conn.close()
            raise ValueError(f"No se puede reabrir la solicitud. Saldo actual ({saldo_actual}) insuficiente para descontar {dias_descontados} días.")
        cursor.execute("UPDATE compensatorios_saldo SET dias_disponibles = dias_disponibles - ? WHERE personal_id = ?", (dias_descontados, personal_id))

    cursor.execute("""
        UPDATE compensatorios_solicitudes 
        SET estado = ?, observaciones = COALESCE(?, observaciones), updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (nuevo_estado, observaciones, solicitud_id))

    conn.commit()
    conn.close()

    registrar_auditoria("EDITAR", "compensatorios_solicitudes", solicitud_id, f"Cambio estado compensatorio #{solicitud_id} de '{estado_anterior}' a '{nuevo_estado}'", usuario)
    return {"success": True}

def listar_solicitudes_compensatorios(personal_id: int = None, estado: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        SELECT cs.*, (p.apellido || ', ' || p.nombre) as agente, p.dni, p.legajo, a.nombre as area_nombre
        FROM compensatorios_solicitudes cs
        JOIN personal p ON cs.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE 1=1
    """
    params = []
    if personal_id:
        query += " AND cs.personal_id = ?"
        params.append(personal_id)
    if estado:
        query += " AND cs.estado = ?"
        params.append(estado)
    
    query += " ORDER BY cs.id DESC"
    cursor.execute(query, params)
    solicitudes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return solicitudes

def listar_novedades_diarias(fecha_hoy_str: str = None):
    """Devuelve ausencias de la jornada actual: Licencias Médicas activas, Partes Médicos activos y Compensatorios vigentes."""
    if not fecha_hoy_str:
        fecha_hoy_str = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Licencias Médicas / Partes Médicos activos hoy
    cursor.execute("""
        SELECT l.id, l.tipo_licencia, l.fecha_inicio, l.fecha_fin, l.dias_totales, l.estado_justificacion,
               (p.apellido || ', ' || p.nombre) as agente, p.dni, p.legajo, a.nombre as area_nombre
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE l.deleted_at IS NULL
          AND ? BETWEEN l.fecha_inicio AND l.fecha_fin
        ORDER BY p.apellido ASC
    """, (fecha_hoy_str,))
    licencias_activas = [dict(r) for r in cursor.fetchall()]

    # 2. Compensatorios vigentes hoy
    cursor.execute("""
        SELECT cs.id, cs.fecha_inicio, cs.fecha_fin, cs.dias_descontados, cs.estado, cs.acta_numero,
               (p.apellido || ', ' || p.nombre) as agente, p.dni, p.legajo, a.nombre as area_nombre
        FROM compensatorios_solicitudes cs
        JOIN personal p ON cs.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE ? BETWEEN cs.fecha_inicio AND cs.fecha_fin
        ORDER BY p.apellido ASC
    """, (fecha_hoy_str,))
    compensatorios_vigentes = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "fecha": fecha_hoy_str,
        "licencias_medicas": licencias_activas,
        "compensatorios_vigentes": compensatorios_vigentes
    }

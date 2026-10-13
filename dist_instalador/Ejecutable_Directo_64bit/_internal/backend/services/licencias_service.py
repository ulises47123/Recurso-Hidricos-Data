import sqlite3
from datetime import datetime
from backend.database import get_db_connection
from backend.services.auditoria_service import registrar_auditoria

# Catálogo normativo completo de licencias - Dirección Provincial de Recursos Hídricos (Jujuy)
# Según CCT y requerimientos de Geovana - 2026
CATALOGO_NORMATIVA = [
    # ── LICENCIAS ANUALES ORDINARIAS ──
    {
        "tipo": "Anual Ordinaria – Convenio Colectivo",
        "regimen": "Descanso Anual",
        "limite_planta": "14 a 35 días corridos según antigüedad. Requiere autorización de jefatura.",
        "limite_contratados": "Proporcional a meses trabajados en el período.",
        "requisito": "Período, cantidad de días, fecha de inicio y regreso. Suspensión registrable con días pendientes.",
        "articulo": "Art. 15 - Licencia Anual Ordinaria (CCT)"
    },
    {
        "tipo": "Anual Ordinaria – Planta Permanente",
        "regimen": "Descanso Anual",
        "limite_planta": "Período, cantidad de días, fecha inicio y regreso. Permite suspensión con registro de días disponibles restantes y autorización.",
        "limite_contratados": "No aplica (ver Convenio o Contrato de Obra).",
        "requisito": "Autorización de jefatura. Observaciones sobre días de suspensión. Días pendientes acumulados por año.",
        "articulo": "Art. 15 - Planta Permanente"
    },
    {
        "tipo": "Anual Ordinaria – Contrato de Locación de Obra",
        "regimen": "Descanso Anual",
        "limite_planta": "No aplica.",
        "limite_contratados": "Período: desde cuándo y hasta cuándo según contrato vigente.",
        "requisito": "Verificación de contrato vigente durante el período de la licencia.",
        "articulo": "Art. 15 - Contrato de Obra"
    },
    # ── LICENCIAS MÉDICAS Y SALUD ──
    {
        "tipo": "Médica – Enfermedad del Agente (Corto Tratamiento)",
        "regimen": "Salud",
        "limite_planta": "Hasta 30 días por año calendario con goce de haberes.",
        "limite_contratados": "Hasta 15 días continuos o discontinuos por período.",
        "requisito": "Certificado médico con diagnóstico. Justificado por Reconocimiento Médico Provincial: Sí/No. Contador de días acumulados por año.",
        "articulo": "Art. 23 - Licencias por Enfermedad"
    },
    {
        "tipo": "Médica – Largo Tratamiento (más de 40 días)",
        "regimen": "Salud",
        "limite_planta": "Hasta 2 años (1 año al 100% y 1 año al 50% de haberes). Intervención de Junta Médica.",
        "limite_contratados": "Sujeto a junta médica y vigencia del contrato.",
        "requisito": "Intervención de Junta Médica Oficial de la Provincia. Justificado por Reconocimiento Médico Provincial: Sí/No. Contador de días acumulados.",
        "articulo": "Art. 24 - Afecciones de Largo Tratamiento"
    },
    {
        "tipo": "Por Atención de Familiar Enfermo",
        "regimen": "Familiar / Salud",
        "limite_planta": "Hasta 7 días por año. Registrar nombre y parentesco del familiar.",
        "limite_contratados": "Hasta 7 días proporcionales al contrato.",
        "requisito": "Nombre del familiar. Parentesco. Fecha. Cantidad de días tomados por parentesco. Certificado médico del familiar.",
        "articulo": "Art. 28 - Atención Familiar Enfermo"
    },
    {
        "tipo": "Por Atención de Hijo con Discapacidad",
        "regimen": "Familiar / Salud",
        "limite_planta": "Según acreditación de discapacidad. Nombre, parentesco, fecha y cantidad de días.",
        "limite_contratados": "Sujeto a vigencia del contrato.",
        "requisito": "Nombre del familiar. Parentesco. Fecha. Cantidad de días. Certificado de discapacidad vigente.",
        "articulo": "Art. 29 - Hijo con Discapacidad"
    },
    # ── LICENCIAS FAMILIARES Y PERSONALES ──
    {
        "tipo": "Maternidad / Paternidad / Adopción (Ley 6.249)",
        "regimen": "Familiar",
        "limite_planta": "Maternidad: 180 días corridos. Paternidad: 15 días hábiles. Fecha y cantidad de días tomados por año.",
        "limite_contratados": "Mismo régimen con certificado de nacimiento.",
        "requisito": "Certificado de embarazo / Partida de nacimiento / Resolución de adopción.",
        "articulo": "Art. 31 - Maternidad, Paternidad y Adopción (Ley 6.249)"
    },
    {
        "tipo": "Por Matrimonio",
        "regimen": "Familiar",
        "limite_planta": "10 días corridos a partir de la fecha del matrimonio.",
        "limite_contratados": "10 días corridos.",
        "requisito": "Fecha y cantidad de días tomados. Acta de matrimonio como respaldo.",
        "articulo": "Art. 33 - Licencia por Matrimonio"
    },
    {
        "tipo": "Por Duelo Familiar",
        "regimen": "Familiar",
        "limite_planta": "5 a 10 días según grado de parentesco. Registrar nombre del familiar, parentesco, fecha y días.",
        "limite_contratados": "5 a 10 días según parentesco.",
        "requisito": "Nombre del familiar. Parentesco. Fecha de fallecimiento. Cantidad de días tomados según parentesco. Certificado de defunción.",
        "articulo": "Art. 35 - Duelo Familiar"
    },
    # ── LICENCIAS POR CAPACITACIÓN Y ESTUDIO ──
    {
        "tipo": "Decenales",
        "regimen": "Capacitación",
        "limite_planta": "Fecha, actividad y cantidad de días tomados según la regulación decenal.",
        "limite_contratados": "Sujeto a evaluación de jefatura.",
        "requisito": "Fecha de la actividad. Nombre/tipo de actividad. Cantidad de días tomados.",
        "articulo": "Art. 40 - Licencias Decenales"
    },
    {
        "tipo": "Por Capacitación / Curso",
        "regimen": "Capacitación",
        "limite_planta": "Actividad, fecha desde y hasta. Contador de cantidad de días.",
        "limite_contratados": "Sujeto a autorización y vigencia del contrato.",
        "requisito": "Nombre de la actividad/curso. Fecha desde y hasta. Contador de días acumulados.",
        "articulo": "Art. 41 - Capacitación Profesional"
    },
    {
        "tipo": "Por Estudio / Examen",
        "regimen": "Estudio",
        "limite_planta": "Hasta 20 días hábiles por año. Máx. 4 días por examen. Fecha desde y hasta. Contador de días.",
        "limite_contratados": "Hasta 10 días hábiles por año.",
        "requisito": "Fecha desde y hasta. Contador de cantidad de días acumulados. Constancia de examen rendido.",
        "articulo": "Art. 42 - Licencias por Estudio"
    },
    {
        "tipo": "Por Actividades Culturales",
        "regimen": "Cultural",
        "limite_planta": "Actividad, fecha desde y hasta. Contador de cantidad de días.",
        "limite_contratados": "Sujeto a autorización.",
        "requisito": "Nombre de la actividad cultural. Fecha desde y hasta. Contador de días acumulados.",
        "articulo": "Art. 43 - Actividades Culturales"
    },
    {
        "tipo": "Por Actividades Deportivas",
        "regimen": "Deportivo",
        "limite_planta": "Tipo de actividad, fecha desde y hasta. Contador de cantidad de días.",
        "limite_contratados": "Sujeto a autorización.",
        "requisito": "Tipo de actividad deportiva. Fecha desde y hasta. Contador de días acumulados.",
        "articulo": "Art. 44 - Actividades Deportivas"
    },
    # ── LICENCIAS ESPECIALES ──
    {
        "tipo": "Por Asuntos Particulares",
        "regimen": "Especial",
        "limite_planta": "Hasta 6 días hábiles por año. Máx. 2 días por mes. Registrar cantidad de días/horas mensual.",
        "limite_contratados": "No aplica / Sujeto a compensación horaria.",
        "requisito": "Cantidad de días/horas de forma mensual. Aviso con 48 hs de anticipación.",
        "articulo": "Art. 48 - Asuntos Particulares"
    },
    {
        "tipo": "Por Actividad Gremial",
        "regimen": "Gremial",
        "limite_planta": "Fecha desde y hasta. Contador de cantidad de días acumulados.",
        "limite_contratados": "Según convenio y acreditación gremial.",
        "requisito": "Fecha desde y hasta. Contador de cantidad de días. Acreditación de representación gremial.",
        "articulo": "Art. 50 - Actividad Gremial"
    },
    {
        "tipo": "Por Estudios Ginecológicos y Mamografía",
        "regimen": "Salud Preventiva",
        "limite_planta": "Período, fecha desde y hasta. Contador de cantidad de días.",
        "limite_contratados": "Proporcional a contrato vigente.",
        "requisito": "Período. Fecha desde y hasta. Contador de días. Orden médica o resultado del estudio.",
        "articulo": "Art. 51 - Salud Preventiva Ginecológica"
    },
    {
        "tipo": "Por Citación Judicial",
        "regimen": "Legal",
        "limite_planta": "Fecha desde y hasta según citación.",
        "limite_contratados": "Fecha desde y hasta.",
        "requisito": "Fecha desde y hasta. Copia de la citación judicial.",
        "articulo": "Art. 53 - Citación Judicial"
    },
    {
        "tipo": "Por Citación Policial",
        "regimen": "Legal",
        "limite_planta": "Fecha desde y hasta según citación.",
        "limite_contratados": "Fecha desde y hasta.",
        "requisito": "Fecha desde y hasta. Constancia policial.",
        "articulo": "Art. 54 - Citación Policial"
    },
    {
        "tipo": "Comisión de Servicios / Viaje Oficial",
        "regimen": "Operativo",
        "limite_planta": "Según orden de misión. Días adicionales por distancia fuera de provincia (ej: +1000 km → 6 días extra). Requiere constancia policial o pasaje.",
        "limite_contratados": "Según orden de servicio.",
        "requisito": "Resolución o Memo de Comisión. KM de distancia. Días adicionales proporcionales. Constancia policial o de transporte adjunta.",
        "articulo": "Art. 52 - Comisiones de Servicio"
    },
    # ── COMPENSATORIOS ──
    {
        "tipo": "Compensatorio",
        "regimen": "Compensatorio",
        "limite_planta": "Fecha de últimas horas cargadas. Cantidad de días cargados. Fecha que se toma el compensatorio. Contador donde se van descontando los días.",
        "limite_contratados": "Según función y acuerdo con la jefatura.",
        "requisito": "Registro de horas/días compensatorios acumulados. Fecha de carga. Fecha de toma. Contador de descuento. Acordar según función del agente.",
        "articulo": "Compensatorio - DPRH"
    }
]

import json

def obtener_normativa():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'catalogo_normativa'")
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except:
            pass
    return CATALOGO_NORMATIVA

def obtener_tipos_licencia():
    """Retorna la lista de tipos de licencia para usar en selects/datalists."""
    return [item["tipo"] for item in obtener_normativa()]



def listar_licencias(busqueda: str = "", estado_justificacion: str = "", tipo_licencia: str = "", personal_id: int = None, incluir_eliminados: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT l.*, 
               p.nombre AS personal_nombre, 
               p.apellido AS personal_apellido, 
               p.dni AS personal_dni, 
               p.legajo AS personal_legajo,
               p.situacion_revista,
               a.nombre AS area_nombre
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE 1=1
    """
    params = []

    if not incluir_eliminados:
        query += " AND l.deleted_at IS NULL"
    else:
        query += " AND l.deleted_at IS NOT NULL"

    if personal_id:
        query += " AND l.personal_id = ?"
        params.append(personal_id)

    if estado_justificacion:
        query += " AND l.estado_justificacion = ?"
        params.append(estado_justificacion)

    if tipo_licencia:
        query += " AND l.tipo_licencia = ?"
        params.append(tipo_licencia)

    if busqueda:
        term = f"%{busqueda.strip()}%"
        query += " AND (p.nombre LIKE ? OR p.apellido LIKE ? OR p.dni LIKE ? OR l.diagnostico LIKE ? OR l.certificado_numero LIKE ?)"
        params.extend([term, term, term, term, term])

    query += " ORDER BY l.fecha_inicio DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def obtener_licencia_por_id(licencia_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT l.*, p.nombre AS personal_nombre, p.apellido AS personal_apellido, p.dni AS personal_dni
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        WHERE l.id = ?
    """, (licencia_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def crear_licencia(data: dict, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Cálculo automático de días si no viene
    dias = data.get("dias_totales", 1)
    if not dias or dias <= 0:
        try:
            d1 = datetime.strptime(data.get("fecha_inicio"), "%Y-%m-%d")
            d2 = datetime.strptime(data.get("fecha_fin"), "%Y-%m-%d")
            dias = max(1, (d2 - d1).days + 1)
        except Exception:
            dias = 1

    cursor.execute("""
        INSERT INTO licencias (
            personal_id, tipo_licencia, fecha_inicio, fecha_fin, dias_totales,
            diagnostico, certificado_numero, medico_nombre, medico_matricula,
            estado_justificacion, auditado_salud_provincial, observacion_auditoria,
            observaciones, periodo_anual, familiar_nombre, familiar_parentesco,
            km_distancia, dias_adicionales_viaje,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """, (
        data.get("personal_id"), data.get("tipo_licencia"), data.get("fecha_inicio"),
        data.get("fecha_fin"), dias, data.get("diagnostico"),
        data.get("certificado_numero"), data.get("medico_nombre"),
        data.get("medico_matricula"), data.get("estado_justificacion", "Pendiente"),
        data.get("auditado_salud_provincial", 0), data.get("observacion_auditoria", ""),
        data.get("observaciones"),
        data.get("periodo_anual"),
        data.get("familiar_nombre"),
        data.get("familiar_parentesco"),
        data.get("km_distancia"),
        data.get("dias_adicionales_viaje", 0)
    ))

    nuevo_id = cursor.lastrowid

    # Actualizar estado de personal si la licencia es vigente hoy
    hoy = datetime.now().strftime("%Y-%m-%d")
    if data.get("fecha_inicio") <= hoy <= data.get("fecha_fin"):
        cursor.execute("UPDATE personal SET estado = 'Licencia' WHERE id = ?", (data.get("personal_id"),))

    conn.commit()
    conn.close()

    registrar_auditoria("CREAR", "licencias", nuevo_id, f"Carga de licencia {data.get('tipo_licencia')} para personal ID {data.get('personal_id')}", usuario)
    return obtener_licencia_por_id(nuevo_id)

def cambiar_estado_justificacion(licencia_id: int, nuevo_estado: str, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE licencias SET estado_justificacion = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (nuevo_estado, licencia_id))
    conn.commit()
    conn.close()
    registrar_auditoria("EDITAR", "licencias", licencia_id, f"Cambio de estado de justificación a '{nuevo_estado}'", usuario)
    return obtener_licencia_por_id(licencia_id)

def actualizar_auditoria_medica(licencia_id: int, auditado: int, observacion: str = "", usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE licencias 
        SET auditado_salud_provincial = ?, observacion_auditoria = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (auditado, observacion, licencia_id))
    conn.commit()
    conn.close()
    estado_txt = "Auditado / Validado" if auditado else "Pendiente de Auditoría"
    registrar_auditoria("EDITAR", "licencias", licencia_id, f"Auditoría médica provincial: {estado_txt}", usuario)
    return obtener_licencia_por_id(licencia_id)

def mover_licencia_a_papelera(licencia_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE licencias SET deleted_at = CURRENT_TIMESTAMP WHERE id = ?", (licencia_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("ELIMINAR_PAPELERA", "licencias", licencia_id, f"Licencia ID {licencia_id} enviada a papelera", usuario)
    return True

def restaurar_licencia(licencia_id: int, usuario: str = "Admin"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE licencias SET deleted_at = NULL WHERE id = ?", (licencia_id,))
    conn.commit()
    conn.close()
    registrar_auditoria("RESTAURAR", "licencias", licencia_id, f"Licencia ID {licencia_id} restaurada", usuario)
    return True

# -------------------------------------------------------------
# ALERTAS Y RESUMEN ANUAL (Req C4 y C5)
# -------------------------------------------------------------
def obtener_resumen_anual_licencias(personal_id: int = None, anio: int = None):
    if not anio:
        anio = datetime.now().year
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            p.id as personal_id,
            p.nombre,
            p.apellido,
            p.dni,
            p.situacion_revista,
            a.nombre as area_nombre,
            l.tipo_licencia,
            SUM(l.dias_totales) as total_dias,
            COUNT(l.id) as cantidad_licencias,
            SUM(CASE WHEN l.auditado_salud_provincial = 1 THEN l.dias_totales ELSE 0 END) as dias_auditados
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE l.deleted_at IS NULL AND strftime('%Y', l.fecha_inicio) = ?
    """
    params = [str(anio)]
    
    if personal_id:
        query += " AND p.id = ?"
        params.append(personal_id)
        
    query += " GROUP BY p.id, l.tipo_licencia ORDER BY p.apellido, p.nombre"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def obtener_alertas_licencias(umbral_dias_anuales: int = 30):
    anio_actual = str(datetime.now().year)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Agentes que acumulan más de umbral_dias_anuales en el año en licencias médicas
    cursor.execute("""
        SELECT 
            p.id as personal_id,
            p.nombre,
            p.apellido,
            p.dni,
            p.legajo,
            p.situacion_revista,
            COALESCE(a.nombre, 'Sin Área') as area_nombre,
            SUM(l.dias_totales) as dias_acumulados,
            COUNT(l.id) as cantidad_certificados,
            SUM(CASE WHEN l.auditado_salud_provincial = 0 THEN 1 ELSE 0 END) as certificados_sin_auditar
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE l.deleted_at IS NULL 
          AND strftime('%Y', l.fecha_inicio) = ?
          AND l.tipo_licencia LIKE '%Médica%'
        GROUP BY p.id
        HAVING dias_acumulados >= ?
        ORDER BY dias_acumulados DESC
    """, (anio_actual, umbral_dias_anuales))
    
    alertas_exceso = [dict(r) for r in cursor.fetchall()]

    # Licencias pendientes de auditoría médica provincial con más de 7 días
    cursor.execute("""
        SELECT 
            l.id as licencia_id,
            l.tipo_licencia,
            l.fecha_inicio,
            l.fecha_fin,
            l.dias_totales,
            l.diagnostico,
            l.medico_nombre,
            p.id as personal_id,
            (p.apellido || ', ' || p.nombre) as agente,
            p.dni
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        WHERE l.deleted_at IS NULL
          AND l.tipo_licencia LIKE '%Médica%'
          AND l.auditado_salud_provincial = 0
          AND l.dias_totales >= 7
        ORDER BY l.fecha_inicio DESC
    """)
    pendientes_auditoria = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "alertas_exceso_dias": alertas_exceso,
        "pendientes_auditoria_oficial": pendientes_auditoria,
        "total_alertas": len(alertas_exceso) + len(pendientes_auditoria)
    }


# -------------------------------------------------------------
# SUSPENSIÓN DE LICENCIAS (Req Geovana DPRH)
# Control de días pendientes cuando se interrumpe una licencia
# -------------------------------------------------------------

def registrar_suspension(data: dict, usuario: str = "Admin"):
    """Registra la suspensión de una licencia en curso con cálculo de días pendientes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO suspensiones_licencia (
            licencia_id, personal_id, fecha_suspension,
            dias_tomados_hasta_suspension, dias_pendientes,
            motivo_suspension, autorizado_por, fecha_alta,
            observaciones, estado, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendiente', CURRENT_TIMESTAMP)
    """, (
        data.get("licencia_id"),
        data.get("personal_id"),
        data.get("fecha_suspension"),
        data.get("dias_tomados_hasta_suspension"),
        data.get("dias_pendientes"),
        data.get("motivo_suspension"),
        data.get("autorizado_por"),
        data.get("fecha_alta"),
        data.get("observaciones")
    ))

    nuevo_id = cursor.lastrowid

    # Marcar la licencia como suspendida (observaciones)
    cursor.execute("""
        UPDATE licencias SET 
            observaciones = COALESCE(observaciones, '') || ' [SUSPENDIDA: ' || ? || ' - Días pendientes: ' || ? || ']',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (data.get("fecha_suspension"), data.get("dias_pendientes"), data.get("licencia_id")))

    conn.commit()
    conn.close()

    registrar_auditoria(
        "EDITAR", "suspensiones_licencia", nuevo_id,
        f"Suspensión de licencia ID {data.get('licencia_id')}. Días pendientes: {data.get('dias_pendientes')}. Motivo: {data.get('motivo_suspension')}",
        usuario
    )
    return {"id": nuevo_id, "success": True, "dias_pendientes": data.get("dias_pendientes")}


def obtener_suspensiones_por_personal(personal_id: int):
    """Obtiene todas las suspensiones de un agente con sus días pendientes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*,
               l.tipo_licencia,
               l.fecha_inicio as licencia_inicio,
               l.fecha_fin as licencia_fin,
               l.dias_totales
        FROM suspensiones_licencia s
        JOIN licencias l ON s.licencia_id = l.id
        WHERE s.personal_id = ?
        ORDER BY s.fecha_suspension DESC
    """, (personal_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_suspensiones_por_licencia(licencia_id: int):
    """Obtiene las suspensiones registradas para una licencia específica."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM suspensiones_licencia
        WHERE licencia_id = ?
        ORDER BY fecha_suspension DESC
    """, (licencia_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def retomar_suspension(suspension_id: int, fecha_alta: str, observaciones: str = "", usuario: str = "Admin"):
    """Marca una suspensión como retomada cuando el agente vuelve a tomar los días pendientes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE suspensiones_licencia SET
            estado = 'Retomada',
            fecha_alta = ?,
            observaciones = COALESCE(observaciones, '') || ' [RETOMADA: ' || ? || ']'
        WHERE id = ?
    """, (fecha_alta, observaciones, suspension_id))
    conn.commit()
    conn.close()
    registrar_auditoria(
        "EDITAR", "suspensiones_licencia", suspension_id,
        f"Suspensión ID {suspension_id} retomada el {fecha_alta}",
        usuario
    )
    return {"success": True}


def obtener_resumen_pendientes_personal(personal_id: int = None):
    """
    Retorna un resumen de días de licencia pendientes por suspensión para cada agente,
    agrupado por período anual y tipo de licencia.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            p.id as personal_id,
            p.apellido,
            p.nombre,
            p.dni,
            p.situacion_revista,
            l.tipo_licencia,
            strftime('%Y', l.fecha_inicio) as periodo,
            s.id as suspension_id,
            s.fecha_suspension,
            s.dias_tomados_hasta_suspension,
            s.dias_pendientes,
            s.motivo_suspension,
            s.autorizado_por,
            s.fecha_alta,
            s.estado as estado_suspension,
            s.observaciones
        FROM suspensiones_licencia s
        JOIN licencias l ON s.licencia_id = l.id
        JOIN personal p ON s.personal_id = p.id
        WHERE s.estado = 'Pendiente'
    """
    params = []
    if personal_id:
        query += " AND p.id = ?"
        params.append(personal_id)

    query += " ORDER BY p.apellido, p.nombre, s.fecha_suspension DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

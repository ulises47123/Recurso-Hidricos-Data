import sqlite3
from backend.database import get_db_connection

def registrar_auditoria(accion: str, tabla_afectada: str, registro_id: int = None, detalles: str = "", usuario: str = "Admin", ip: str = "127.0.0.1"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO auditoria_logs (usuario, accion, tabla_afectada, registro_id, detalles, ip)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (usuario, accion, tabla_afectada, registro_id, detalles, ip))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error registrando auditoría: {e}")

def obtener_logs(limite: int = 100, filtro_accion: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if filtro_accion:
        cursor.execute("""
            SELECT * FROM auditoria_logs WHERE accion = ? ORDER BY id DESC LIMIT ?
        """, (filtro_accion, limite))
    else:
        cursor.execute("""
            SELECT * FROM auditoria_logs ORDER BY id DESC LIMIT ?
        """, (limite,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

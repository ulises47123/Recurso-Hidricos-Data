import os
import json
import shutil
import sqlite3
import threading
import time
from datetime import datetime
from backend.database import DB_PATH, get_db_connection
from backend.services.auditoria_service import registrar_auditoria

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKUPS_LOCAL_DIR = os.path.join(ROOT_DIR, "backups_gdrive_sync")
os.makedirs(BACKUPS_LOCAL_DIR, exist_ok=True)

# Guardar estado de Google Drive
GDRIVE_STATE = {
    "timer_thread": None,
    "interval_hours": 5,
    "running": False
}

def obtener_directorio_backups():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT valor FROM configuracion WHERE clave = 'gdrive_folder_path'")
        row = cursor.fetchone()
        conn.close()
        if row and row[0] and row[0].strip():
            target = row[0].strip()
            os.makedirs(target, exist_ok=True)
            return target
    except Exception:
        pass
    os.makedirs(BACKUPS_LOCAL_DIR, exist_ok=True)
    return BACKUPS_LOCAL_DIR

def obtener_directorio_documentos_backup() -> str:
    """Retorna la ruta de la carpeta Backup dentro de Documentos del usuario."""
    userprofile = os.environ.get("USERPROFILE") or os.path.expanduser("~")
    docs_dir = os.path.join(userprofile, "Documents")
    if not os.path.exists(docs_dir):
        docs_dir_es = os.path.join(userprofile, "Documentos")
        if os.path.exists(docs_dir_es):
            docs_dir = docs_dir_es
    backup_docs_dir = os.path.join(docs_dir, "Backup")
    os.makedirs(backup_docs_dir, exist_ok=True)
    return backup_docs_dir

def obtener_config_gdrive():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT clave, valor FROM configuracion 
        WHERE clave IN (
            'gdrive_connected', 'gdrive_user_email', 'gdrive_folder_id', 
            'gdrive_folder_name', 'gdrive_auto_backup', 'gdrive_last_backup',
            'gdrive_credentials_json', 'gdrive_folder_path'
        )
    """)
    filas = dict(cursor.fetchall())
    conn.close()

    return {
        "conectado": filas.get("gdrive_connected", "0") == "1",
        "email": filas.get("gdrive_user_email", ""),
        "folder_id": filas.get("gdrive_folder_id", "root"),
        "folder_name": filas.get("gdrive_folder_name", "Recursos Hidricos Backups"),
        "folder_path": filas.get("gdrive_folder_path", BACKUPS_LOCAL_DIR),
        "auto_backup": filas.get("gdrive_auto_backup", "1") == "1",
        "last_backup": filas.get("gdrive_last_backup", ""),
        "has_credentials": bool(filas.get("gdrive_credentials_json", ""))
    }

def guardar_config_gdrive(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in data.items():
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()

def autenticar_simulado_o_credenciales(email: str, credentials_json: str = "", folder_path: str = ""):
    """Guarda la conexión de Google Drive y la ruta de sincronización."""
    config = {
        "gdrive_connected": "1",
        "gdrive_user_email": email.strip() or "admin.recursoshidricos@gmail.com",
        "gdrive_folder_name": "Recursos Hidricos Backups",
        "gdrive_auto_backup": "1"
    }
    if folder_path and folder_path.strip():
        config["gdrive_folder_path"] = folder_path.strip()
    if credentials_json:
        config["gdrive_credentials_json"] = credentials_json
    guardar_config_gdrive(config)
    registrar_auditoria("CONFIGURACION", "gdrive", None, f"Google Drive conectado con cuenta {config['gdrive_user_email']}")
    return {"success": True, "email": config["gdrive_user_email"]}

def desconectar_gdrive():
    guardar_config_gdrive({
        "gdrive_connected": "0",
        "gdrive_user_email": "",
        "gdrive_credentials_json": ""
    })
    registrar_auditoria("CONFIGURACION", "gdrive", None, "Google Drive desconectado")
    return {"success": True}

def listar_backups_gdrive():
    """
    Retorna la lista de backups disponibles manteniendo política de 3 copias.
    """
    dir_backups = obtener_directorio_backups()
    if not os.path.exists(dir_backups):
        return []

    archivos = []
    for f in os.listdir(dir_backups):
        if f.endswith(".db"):
            ruta = os.path.join(dir_backups, f)
            stat = os.stat(ruta)
            archivos.append({
                "nombre": f,
                "ruta": ruta,
                "tamano": stat.st_size,
                "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": stat.st_mtime
            })

    # Ordenar de más reciente a más antiguo (por mtime y por nombre descendente)
    archivos.sort(key=lambda x: (x["timestamp"], x["nombre"]), reverse=True)
    return archivos

def realizar_backup_gdrive(usuario: str = "Admin"):
    """
    Crea una copia de la base de datos actual en la carpeta sincronizada con Google Drive.
    Aplica rotación estricta de máximo 3 copias (elimina la más antigua).
    """
    dir_backups = obtener_directorio_backups()
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_nombre = f"recursos_hidricos_backup_{timestamp_str}.db"
    destino = os.path.join(dir_backups, backup_nombre)

    # Copiar con checkpoint seguro de SQLite
    try:
        conn = get_db_connection()
        conn.execute("PRAGMA wal_checkpoint(FULL);")
        conn.close()
    except Exception:
        pass

    shutil.copy2(DB_PATH, destino)

    # Sincronizar copia única en Documentos/Backup
    try:
        docs_backup_dir = obtener_directorio_documentos_backup()
        docs_backup_path = os.path.join(docs_backup_dir, "recursos_hidricos_backup.db")
        shutil.copy2(DB_PATH, docs_backup_path)
    except Exception as e_docs:
        print(f"[Backup Documentos Aviso] No se pudo copiar a Documentos/Backup: {e_docs}")

    # Rotación: mantener exactamente máximo 3 copias
    backups = listar_backups_gdrive()
    eliminados = []
    if len(backups) > 3:
        for b in backups[3:]:
            try:
                os.remove(b["ruta"])
                eliminados.append(b["nombre"])
            except Exception as e:
                print(f"Error eliminando backup antiguo: {e}")

    # Guardar último backup en configuración
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    guardar_config_gdrive({"gdrive_last_backup": now_str})
    registrar_auditoria("BACKUP", "database", None, f"Backup generado: {backup_nombre}. Rotación aplicó sobre {len(eliminados)} archivos.", usuario)

    return {
        "success": True,
        "backup_creado": backup_nombre,
        "fecha": now_str,
        "total_backups_vigentes": min(len(backups), 3),
        "eliminados_rotacion": eliminados
    }

def restaurar_backup_gdrive(backup_nombre: str, usuario: str = "Admin"):
    """
    Restaura la base de datos a partir de una de las copias existentes.
    """
    dir_backups = obtener_directorio_backups()
    origen = os.path.join(dir_backups, backup_nombre)
    if not os.path.exists(origen):
        raise FileNotFoundError(f"El archivo de respaldo {backup_nombre} no existe.")

    # Crear backup de rescate antes de sobreescribir
    rescate = f"{DB_PATH}.previo_restauracion.bak"
    try:
        shutil.copy2(DB_PATH, rescate)
    except Exception:
        pass

    shutil.copy2(origen, DB_PATH)
    registrar_auditoria("RESTAURAR", "database", None, f"Base de datos restaurada desde copia {backup_nombre}", usuario)
    return {"success": True, "mensaje": f"Base de datos restaurada exitosamente desde {backup_nombre}"}

def _verificar_y_ejecutar_backup_si_corresponde():
    cfg = obtener_config_gdrive()
    if not cfg.get("conectado") or not cfg.get("auto_backup"):
        return
    
    last_backup_str = cfg.get("last_backup", "")
    debe_ejecutar = False
    if not last_backup_str:
        debe_ejecutar = True
    else:
        try:
            last_dt = datetime.strptime(last_backup_str, "%Y-%m-%d %H:%M:%S")
            delta = datetime.now() - last_dt
            if delta.total_seconds() >= (GDRIVE_STATE["interval_hours"] * 3600):
                debe_ejecutar = True
        except Exception:
            debe_ejecutar = True

    if debe_ejecutar:
        print("[Google Drive AutoBackup] Ejecutando respaldo automático (intervalo 5h cumplido)...")
        realizar_backup_gdrive(usuario="Sistema_Programado_5h")

def _bucle_backup_automatico():
    """Ejecuta un respaldo cada 5 horas si está habilitado y al iniciar si correspondiera."""
    while GDRIVE_STATE["running"]:
        try:
            _verificar_y_ejecutar_backup_si_corresponde()
        except Exception as e:
            print(f"[Google Drive AutoBackup Error] {e}")
        # Revisar cada 30 segundos si se cumplieron las 5 horas
        for _ in range(30):
            if not GDRIVE_STATE["running"]:
                break
            time.sleep(1)

def iniciar_demonio_backup():
    if not GDRIVE_STATE["running"]:
        GDRIVE_STATE["running"] = True
        t = threading.Thread(target=_bucle_backup_automatico, daemon=True)
        t.start()
        GDRIVE_STATE["timer_thread"] = t

import os
import sys
import io
import shutil
from datetime import datetime, timedelta, timezone
from backend.security import hash_password, verify_password, generar_token_sesion

# Asegurar que el directorio raíz esté en sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Silenciar WinError 10054 en Windows (desconexión abrupta de clientes HTTP en asyncio)
if sys.platform == "win32":
    try:
        from asyncio.proactor_events import _ProactorBasePipeTransport
        _orig_call_connection_lost = _ProactorBasePipeTransport._call_connection_lost

        def _silenced_call_connection_lost(self, exc):
            try:
                _orig_call_connection_lost(self, exc)
            except (ConnectionResetError, OSError):
                pass

        _ProactorBasePipeTransport._call_connection_lost = _silenced_call_connection_lost
    except Exception:
        pass

# Directorio de subida para legajos digitales
UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads_legajos")
os.makedirs(UPLOADS_DIR, exist_ok=True)

from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, Request, Response, Body
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from backend.database import init_db, get_db_connection, DB_PATH
from backend.models import (
    PersonalCreate, PersonalUpdate, LicenciaCreate, LicenciaUpdate, 
    AreaModel, ConfigItem, FamiliarCreate, HistorialFuncionCreate,
    UsuarioLogin, UsuarioCreate, UsuarioUpdate, SuspensionLicenciaCreate,
    CompensatorioCargaCreate, CompensatorioSolicitudCreate, CompensatorioEstadoUpdate, FeriadoCreate
)
from backend.services import (
    personal_service, licencias_service, organigrama_service, 
    excel_service, auditoria_service, vba_generator, pdf_service,
    compensatorios_service, gdrive_service, github_sync_service,
    git_manager_service, catalogos_service, auto_readme_sync
)


from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Iniciar demonio de respaldo cada 5 horas para Google Drive
    try:
        gdrive_service.iniciar_demonio_backup()
    except Exception as e:
        print(f"[Google Drive] Advertencia al iniciar demonio de backup: {e}")

    # Auto-inicio de Auto-README Sync
    try:
        auto_readme_sync.iniciar_demonio_auto_readme()
    except Exception as e:
        print(f"[AutoReadme] Advertencia al iniciar demonio: {e}")

    # Auto-inicio autónomo de Cloudflare Quick Tunnel al abrir el programa
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT clave, valor FROM configuracion WHERE clave IN ('cf_quick_autostart')")
        filas = dict(cursor.fetchall())
        conn.close()
        
        autostart_quick = filas.get("cf_quick_autostart", "1") == "1"
        if autostart_quick:
            print("[Cloudflare] Iniciando túnel temporal y sincronización autónoma en segundo plano...")
            import threading
            def _iniciar_autonomo():
                import time
                time.sleep(2)
                try:
                    iniciar_tunel_remoto()
                except Exception as ex:
                    print(f"[Cloudflare Autostart Warning] {ex}")
            threading.Thread(target=_iniciar_autonomo, daemon=True).start()
    except Exception as e:
        print(f"[Cloudflare] Advertencia al auto-iniciar túnel temporal: {e}")

    # Demonio de reintento automático para GitHub Pages / Git Sync (cada 1 hora)
    try:
        def _bucle_reintento_git():
            import time
            while True:
                time.sleep(3600)
                try:
                    github_sync_service.reintentar_push_fallidos()
                except Exception as e:
                    print(f"[Git Sync Retry Error] {e}")

        import threading
        threading.Thread(target=_bucle_reintento_git, daemon=True).start()
    except Exception as e:
        print(f"[Git Sync] Advertencia al iniciar demonio de reintento: {e}")
    yield
    # Limpieza de subprocesos y recursos en el shutdown de FastAPI
    print("[Shutdown] Finalizando servicios y limpiando subprocesos...")
    try:
        detener_proceso_tunel()
    except Exception as e:
        print(f"[Shutdown] Advertencia al detener túnel Cloudflare: {e}")

app = FastAPI(title="Sistema de Gestión de Personal - Recursos Hídricos", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verificar_token_db(token: str):
    if not token:
        return None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.usuario_id, s.expiracion, u.username, u.rol 
            FROM sesiones s
            JOIN usuarios u ON s.usuario_id = u.id
            WHERE s.token = ? AND u.activo = 1
        """, (token,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None

        expiracion_str = row[1]
        try:
            exp_dt = datetime.fromisoformat(expiracion_str)
            now_dt = datetime.now(timezone.utc) if exp_dt.tzinfo is not None else datetime.utcnow()
            if now_dt > exp_dt:
                return None
        except Exception:
            return None

        return {"id": row[0], "username": row[2], "rol": row[3]}
    except Exception:
        return None

def verificar_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Header Authorization Bearer requerido")
    token = auth_header.split(" ", 1)[1].strip()
    user = verificar_token_db(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user

@app.middleware("http")
async def auth_and_tunnel_middleware(request: Request, call_next):
    path = request.url.path
    method = request.method.upper()

    # 1. Exención para OPTIONS, login, health y archivos estáticos públicos (rutas fuera de /api/)
    if method == "OPTIONS" or path in ("/api/auth/login", "/api/health") or not path.startswith("/api/"):
        return await call_next(request)

    # 2. Verificación de token Bearer para todos los endpoints de API /api/*
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Header Authorization Bearer requerido"}
        )

    token = auth_header.split(" ", 1)[1].strip()
    user = verificar_token_db(token)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token inválido o sesión expirada"}
        )

    request.state.user = user

    # 3. Control de acceso remoto vía túnel TryCloudflare
    # Se permite escritura (POST/PUT/DELETE/PATCH) a usuarios autenticados
    return await call_next(request)

# -------------------------------------------------------------
# ENDPOINT DE HEALTH CHECK (PÚBLICO PARA ELECTRON & MONITORING)
# -------------------------------------------------------------
@app.get("/api/health")
def get_health_status():
    return {"ok": True}

# -------------------------------------------------------------
# MÓDULO 1: DASHBOARD / INICIO
# -------------------------------------------------------------
@app.get("/api/dashboard")
def get_dashboard_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Personal Activo
    cursor.execute("SELECT COUNT(*) FROM personal WHERE deleted_at IS NULL")
    total_personal = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM personal WHERE estado = 'Activo' AND deleted_at IS NULL")
    total_activos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM personal WHERE estado = 'Licencia' AND deleted_at IS NULL")
    total_en_licencia = cursor.fetchone()[0]

    # Licencias Médicas pendientes
    cursor.execute("SELECT COUNT(*) FROM licencias WHERE estado_justificacion = 'Pendiente' AND deleted_at IS NULL")
    licencias_pendientes = cursor.fetchone()[0]

    # Distribución por Situación de Revista
    cursor.execute("""
        SELECT situacion_revista, COUNT(*) as cantidad 
        FROM personal 
        WHERE deleted_at IS NULL 
        GROUP BY situacion_revista
    """)
    distribucion_revista = [{"label": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

    # Distribución por Área
    cursor.execute("""
        SELECT COALESCE(a.nombre, 'Sin Área Asignada') as area, COUNT(p.id) as cantidad
        FROM personal p
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE p.deleted_at IS NULL
        GROUP BY p.area_id
        ORDER BY cantidad DESC
    """)
    distribucion_area = [{"area": row[0], "cantidad": row[1]} for row in cursor.fetchall()]

    # Licencias activas hoy
    cursor.execute("""
        SELECT l.*, (p.apellido || ', ' || p.nombre) as agente, p.dni, a.nombre as area
        FROM licencias l
        JOIN personal p ON l.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE l.deleted_at IS NULL
        ORDER BY l.fecha_inicio DESC
        LIMIT 5
    """)
    licencias_recientes = [dict(row) for row in cursor.fetchall()]

    # Últimas actividades de auditoría
    cursor.execute("SELECT * FROM auditoria_logs ORDER BY id DESC LIMIT 6")
    actividades_recientes = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Novedades diarias de hoy
    novedades_diarias = compensatorios_service.listar_novedades_diarias()

    return {
        "kpis": {
            "total_personal": total_personal,
            "total_activos": total_activos,
            "total_en_licencia": total_en_licencia,
            "licencias_pendientes": licencias_pendientes
        },
        "distribucion_revista": distribucion_revista,
        "distribucion_area": distribucion_area,
        "licencias_recientes": licencias_recientes,
        "actividades_recientes": actividades_recientes,
        "novedades_diarias": novedades_diarias
    }

# -------------------------------------------------------------
# MÓDULO 4: GESTIÓN Y DESCUENTO DE COMPENSATORIOS
# -------------------------------------------------------------
@app.get("/api/compensatorios/saldo/{personal_id}")
def obtener_saldo_compensatorio(personal_id: int):
    return compensatorios_service.obtener_saldo_agente(personal_id)

@app.post("/api/compensatorios/cargar")
def cargar_compensatorios(data: CompensatorioCargaCreate):
    return compensatorios_service.cargar_dias_compensatorios(data.dict())

@app.post("/api/compensatorios/solicitar")
def solicitar_compensatorio(data: CompensatorioSolicitudCreate):
    try:
        return compensatorios_service.solicitar_compensatorio(data.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/compensatorios/solicitudes/{solicitud_id}/estado")
def cambiar_estado_compensatorio(solicitud_id: int, data: CompensatorioEstadoUpdate):
    try:
        return compensatorios_service.cambiar_estado_solicitud(solicitud_id, data.estado, data.observaciones or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/compensatorios/solicitudes")
def listar_compensatorios(personal_id: Optional[int] = Query(None), estado: Optional[str] = Query(None)):
    return compensatorios_service.listar_solicitudes_compensatorios(personal_id=personal_id, estado=estado)

@app.get("/api/compensatorios/novedades-diarias")
def obtener_novedades_diarias(fecha: Optional[str] = Query(None)):
    return compensatorios_service.listar_novedades_diarias(fecha)

@app.get("/api/compensatorios/solicitudes/{solicitud_id}/pdf")
def descargar_pdf_compensatorio(solicitud_id: int):
    try:
        pdf_bytes = pdf_service.generar_pdf_formulario_compensatorio(solicitud_id)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename=Formulario_Compensatorio_{solicitud_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/compensatorios/calcular-dias-habiles")
def calcular_dias_habiles_endpoint(fecha_inicio: str = Query(...), fecha_fin: str = Query(...)):
    """Calcula la cantidad de días hábiles entre dos fechas excluyendo fines de semana y feriados."""
    try:
        return compensatorios_service.calcular_dias_habiles_detalle(fecha_inicio, fecha_fin)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/feriados")
def listar_feriados_endpoint():
    """Retorna la lista de feriados registrados en el sistema."""
    return compensatorios_service.listar_feriados()

@app.post("/api/feriados")
def crear_feriado_endpoint(data: FeriadoCreate):
    """Permite registrar un nuevo feriado oficial o provincial."""
    try:
        return compensatorios_service.crear_feriado(data.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/feriados/{feriado_id}")
def eliminar_feriado_endpoint(feriado_id: int):
    """Permite eliminar un feriado por su ID."""
    try:
        return compensatorios_service.eliminar_feriado(feriado_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------
# MÓDULO 2 & 4: PERSONAL (CRUD, LISTADO, BÚSQUEDA)
# -------------------------------------------------------------
@app.get("/api/personal")
def listar_personal(
    busqueda: str = Query("", description="Búsqueda por nombre, DNI, legajo, cargo, función o área"),
    area_id: Optional[int] = Query(None),
    situacion_revista: str = Query(""),
    estado: str = Query(""),
    ordenar_por: str = Query("apellido"),
    orden: str = Query("ASC")
):
    return personal_service.listar_personal(
        busqueda=busqueda,
        area_id=area_id,
        situacion_revista=situacion_revista,
        estado=estado,
        ordenar_por=ordenar_por,
        orden=orden,
        incluir_eliminados=False
    )

@app.get("/api/personal/{personal_id}")
def obtener_personal(personal_id: int):
    item = personal_service.obtener_personal_por_id(personal_id)
    if not item:
        raise HTTPException(status_code=404, detail="Personal no encontrado")
    
    # Obtener historial de licencias del agente
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM licencias WHERE personal_id = ? AND deleted_at IS NULL ORDER BY fecha_inicio DESC", (personal_id,))
    item["historial_licencias"] = [dict(r) for r in cursor.fetchall()]

    # Obtener contrato
    cursor.execute("SELECT * FROM contratos WHERE personal_id = ? ORDER BY id DESC LIMIT 1", (personal_id,))
    c_row = cursor.fetchone()
    item["contrato_actual"] = dict(c_row) if c_row else None
    conn.close()

    return item

@app.post("/api/personal")
def crear_personal(data: PersonalCreate):
    return personal_service.crear_personal(data.dict())

@app.put("/api/personal/{personal_id}")
def actualizar_personal(personal_id: int, data: PersonalUpdate):
    return personal_service.actualizar_personal(personal_id, data.dict())

@app.delete("/api/personal/{personal_id}")
def mover_personal_a_papelera(personal_id: int):
    return {"success": personal_service.mover_a_papelera(personal_id)}

@app.post("/api/personal/{personal_id}/restaurar")
def restaurar_personal(personal_id: int):
    return {"success": personal_service.restaurar_personal(personal_id)}

@app.delete("/api/personal/{personal_id}/definitivo")
def eliminar_personal_definitivo(personal_id: int):
    return {"success": personal_service.eliminar_definitivo(personal_id)}

# -------------------------------------------------------------
# CATÁLOGOS DINÁMICOS (Principio de cero información estática)
# -------------------------------------------------------------

from typing import Any

# 1. Situaciones de Revista
@app.get("/api/catalogos/situacion_revista")
def obtener_catalogo_situacion_revista():
    return catalogos_service.listar_situaciones_revista()

@app.post("/api/catalogos/situacion_revista")
def agregar_catalogo_situacion_revista(data: Any = Body(None)):
    if isinstance(data, list):
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", ("catalogo_situacion_revista", json.dumps(data)))
        try:
            cursor.execute("DELETE FROM situaciones_revista_catalogo")
            for idx, nom in enumerate(data):
                cursor.execute("INSERT INTO situaciones_revista_catalogo (nombre, descripcion, activo, orden) VALUES (?, '', 1, ?)", (nom, idx + 1))
        except Exception:
            pass
        conn.commit()
        conn.close()
        return {"success": True}
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.agregar_situacion_revista(data_dict)

actualizar_catalogo_situacion_revista = agregar_catalogo_situacion_revista

@app.put("/api/catalogos/situacion_revista/{item_id}")
def editar_catalogo_situacion_revista(item_id: int, data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.editar_situacion_revista(item_id, data_dict)

@app.put("/api/catalogos/situacion_revista")
def editar_catalogo_situacion_revista_body(data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    item_id = data_dict.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="ID requerido para editar")
    return catalogos_service.editar_situacion_revista(int(item_id), data_dict)

@app.delete("/api/catalogos/situacion_revista/{item_id}")
def eliminar_catalogo_situacion_revista(item_id: int):
    return catalogos_service.eliminar_situacion_revista(item_id)

# 2. Lugares de Trabajo
@app.get("/api/catalogos/lugares_trabajo")
def obtener_catalogo_lugares_trabajo():
    return catalogos_service.listar_lugares_trabajo()

@app.post("/api/catalogos/lugares_trabajo")
def agregar_catalogo_lugares_trabajo(data: Any = Body(None)):
    if isinstance(data, list):
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", ("catalogo_lugares_trabajo", json.dumps(data)))
        try:
            cursor.execute("DELETE FROM lugares_trabajo_catalogo")
            for idx, nom in enumerate(data):
                cursor.execute("INSERT INTO lugares_trabajo_catalogo (nombre, descripcion, activo, orden) VALUES (?, '', 1, ?)", (nom, idx + 1))
        except Exception:
            pass
        conn.commit()
        conn.close()
        return {"success": True}
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.agregar_lugar_trabajo(data_dict)

@app.put("/api/catalogos/lugares_trabajo/{item_id}")
def editar_catalogo_lugares_trabajo(item_id: int, data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.editar_lugar_trabajo(item_id, data_dict)

@app.put("/api/catalogos/lugares_trabajo")
def editar_catalogo_lugares_trabajo_body(data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    item_id = data_dict.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="ID requerido para editar")
    return catalogos_service.editar_lugar_trabajo(int(item_id), data_dict)

@app.delete("/api/catalogos/lugares_trabajo/{item_id}")
def eliminar_catalogo_lugares_trabajo(item_id: int):
    return catalogos_service.eliminar_lugar_trabajo(item_id)

# 3. Funciones Oficiales
@app.get("/api/catalogos/funciones")
def obtener_catalogo_funciones():
    return catalogos_service.listar_funciones()

@app.post("/api/catalogos/funciones")
def agregar_catalogo_funciones(data: Any = Body(None)):
    if isinstance(data, list):
        import json
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", ("catalogo_funciones", json.dumps(data)))
        try:
            cursor.execute("DELETE FROM funciones_catalogo")
            for idx, nom in enumerate(data):
                cursor.execute("INSERT INTO funciones_catalogo (nombre, descripcion, activo, orden) VALUES (?, '', 1, ?)", (nom, idx + 1))
        except Exception:
            pass
        conn.commit()
        conn.close()
        return {"success": True}
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.agregar_funcion(data_dict)

@app.put("/api/catalogos/funciones/{item_id}")
def editar_catalogo_funciones(item_id: int, data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.editar_funcion(item_id, data_dict)

@app.put("/api/catalogos/funciones")
def editar_catalogo_funciones_body(data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    item_id = data_dict.get("id")
    if not item_id:
        raise HTTPException(status_code=400, detail="ID requerido para editar")
    return catalogos_service.editar_funcion(int(item_id), data_dict)

@app.delete("/api/catalogos/funciones/{item_id}")
def eliminar_catalogo_funciones(item_id: int):
    return catalogos_service.eliminar_funcion(item_id)

# 4. Áreas / Dependencias (Integrado con organigrama)
@app.get("/api/catalogos/areas")
def obtener_catalogo_areas():
    return catalogos_service.listar_areas()

@app.post("/api/catalogos/areas")
def agregar_catalogo_areas(data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.agregar_area(data_dict)

@app.put("/api/catalogos/areas/{area_id}")
def editar_catalogo_areas(area_id: int, data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    return catalogos_service.editar_area(area_id, data_dict)

@app.put("/api/catalogos/areas")
def editar_catalogo_areas_body(data: Any = Body(None)):
    data_dict = data if isinstance(data, dict) else (data.dict() if hasattr(data, "dict") else (dict(data) if data else {}))
    area_id = data_dict.get("id")
    if not area_id:
        raise HTTPException(status_code=400, detail="ID requerido para editar")
    return catalogos_service.editar_area(int(area_id), data_dict)

@app.delete("/api/catalogos/areas/{area_id}")
def eliminar_catalogo_areas(area_id: int):
    return catalogos_service.eliminar_area(area_id)

@app.post('/api/catalogos/normativa')
def actualizar_catalogo_normativa(data: Any = Body(None)):
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)', ('catalogo_normativa', json.dumps(data or [])))
    conn.commit()
    conn.close()
    return {'success': True}

@app.get("/api/catalogos")
def obtener_catalogos():
    import json
    areas = catalogos_service.listar_areas()
    normativa = licencias_service.obtener_normativa()
    tipos_licencia = [n["tipo"] for n in normativa]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clave, valor FROM configuracion WHERE clave IN ('catalogo_situacion_revista', 'catalogo_lugares_trabajo', 'catalogo_funciones')")
    config_dict = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()

    try:
        situaciones_obj = catalogos_service.listar_situaciones_revista()
        situaciones_revista = [s["nombre"] for s in situaciones_obj]
    except Exception:
        situaciones_revista = catalogos_service.SITUACIONES_REVISTA
        situaciones_obj = []

    if 'catalogo_situacion_revista' in config_dict and config_dict['catalogo_situacion_revista']:
        try:
            situaciones_revista = json.loads(config_dict['catalogo_situacion_revista'])
        except Exception:
            pass

    try:
        lugares_obj = catalogos_service.listar_lugares_trabajo()
        lugares_trabajo = [l["nombre"] for l in lugares_obj]
    except Exception:
        lugares_trabajo = catalogos_service.LUGARES_TRABAJO
        lugares_obj = []

    if 'catalogo_lugares_trabajo' in config_dict and config_dict['catalogo_lugares_trabajo']:
        try:
            lugares_trabajo = json.loads(config_dict['catalogo_lugares_trabajo'])
        except Exception:
            pass

    try:
        funciones_obj = catalogos_service.listar_funciones()
        funciones = [f["nombre"] for f in funciones_obj]
    except Exception:
        funciones = catalogos_service.FUNCIONES
        funciones_obj = []

    if 'catalogo_funciones' in config_dict and config_dict['catalogo_funciones']:
        try:
            funciones = json.loads(config_dict['catalogo_funciones'])
        except Exception:
            pass

    return {
        "situaciones_revista": situaciones_revista,
        "lugares_trabajo": lugares_trabajo,
        "funciones": funciones,
        "tipos_licencia": tipos_licencia,
        "parentescos": [
            "Hijo/a", 
            "Cónyuge", 
            "Concubino/a", 
            "Padre/Madre", 
            "Familiar a cargo", 
            "Otro"
        ],
        "tipos_documento": [
            "Decreto / Resolución", 
            "Contrato Escaneado", 
            "DNI Copia", 
            "Título Profesional", 
            "Certificado Médico", 
            "Currículum Vitae", 
            "Otro"
        ],
        "tipos_contrato": [
            "Contrato de Empleo Público Ley 5473", 
            "Contrato de Obra", 
            "Locación de Servicios Profesionales", 
            "Locación de Servicios Técnicos", 
            "Pasantía"
        ],
        "estados_personal": ["Activo", "Licencia", "Baja Transitoria"],
        "estados_justificacion": ["Justificada", "Pendiente", "Observada", "Rechazada"],
        "areas": areas,
        "catalogo_detalles": {
            "situaciones_revista": situaciones_obj,
            "lugares_trabajo": lugares_obj,
            "funciones": funciones_obj,
            "areas": areas
        }
    }

# -------------------------------------------------------------
# FAMILIARES Y BENEFICIARIOS (Req B2)
# -------------------------------------------------------------
@app.get("/api/personal/{personal_id}/familiares")
def listar_familiares_personal(personal_id: int):
    return personal_service.listar_familiares(personal_id)

@app.post("/api/personal/{personal_id}/familiares")
def agregar_familiar_personal(personal_id: int, data: FamiliarCreate):
    d = data.dict()
    d["personal_id"] = personal_id
    return personal_service.agregar_familiar(d)

@app.delete("/api/familiares/{familiar_id}")
def eliminar_familiar(familiar_id: int):
    return personal_service.eliminar_familiar(familiar_id)

# -------------------------------------------------------------
# HISTORIAL DE FUNCIONES / CAMBIOS DE CARGO (Req F6)
# -------------------------------------------------------------
@app.post("/api/personal/{personal_id}/historial")
def registrar_cambio_funcion(personal_id: int, data: HistorialFuncionCreate):
    d = data.dict()
    d["personal_id"] = personal_id
    return personal_service.registrar_cambio_funcion(d)

# -------------------------------------------------------------
# DOCUMENTOS DE LEGAJO DIGITAL (Req B3)
# -------------------------------------------------------------
@app.post("/api/personal/{personal_id}/documentos")
async def subir_documento_legajo(
    personal_id: int, 
    file: UploadFile = File(...), 
    tipo_documento: str = Form("Otro"), 
    titulo: str = Form(...),
    observaciones: str = Form("")
):
    safe_filename = f"{personal_id}_{int(datetime.now().timestamp())}_{file.filename}"
    file_path = os.path.join(UPLOADS_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return personal_service.registrar_documento_legajo(
        personal_id=personal_id,
        tipo_documento=tipo_documento,
        titulo=titulo,
        nombre_archivo=file.filename,
        ruta_archivo=file_path,
        observaciones=observaciones
    )

@app.delete("/api/documentos/{documento_id}")
def eliminar_documento_legajo(documento_id: int):
    return personal_service.eliminar_documento_legajo(documento_id)

@app.get("/api/documentos/{documento_id}/descargar")
def descargar_documento_legajo(documento_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ruta_archivo, nombre_archivo FROM documentos_legajo WHERE id = ?", (documento_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not os.path.exists(row[0]):
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return FileResponse(row[0], filename=row[1])

# -------------------------------------------------------------
# GENERACIÓN DE DOCUMENTOS PDF OFICIALES (xhtml2pdf)
# -------------------------------------------------------------
@app.get("/api/personal/{personal_id}/pdf")
def descargar_pdf_ficha_personal(personal_id: int):
    """Genera y descarga la Ficha Oficial del Agente en PDF."""
    try:
        pdf_bytes = pdf_service.generar_pdf_ficha_personal(personal_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Ficha_Personal_{personal_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/licencias/{licencia_id}/pdf")
def descargar_pdf_constancia_licencia(licencia_id: int):
    """Genera y descarga la Constancia Oficial de Concesión de Licencia en PDF."""
    try:
        pdf_bytes = pdf_service.generar_pdf_constancia_licencia(licencia_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Constancia_Licencia_{licencia_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/personal/pdf/nomina")
def descargar_pdf_nomina_personal(
    busqueda: str = Query(""),
    area_id: Optional[int] = Query(None),
    situacion_revista: str = Query(""),
    estado: str = Query(""),
    ids: Optional[str] = Query(None, description="Lista de IDs separados por coma para generar nómina de agentes seleccionados")
):
    """Genera y descarga la Nómina General de Personal en PDF, opcionalmente filtrada por IDs seleccionados."""
    try:
        id_list = None
        if ids and ids.strip():
            id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]

        personal_list = personal_service.listar_personal(
            busqueda=busqueda, area_id=area_id,
            situacion_revista=situacion_revista, estado=estado,
            ids=id_list
        )
        pdf_bytes = pdf_service.generar_pdf_nomina_personal(personal_list)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=Nomina_Personal_DPRH.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/personal/excel/seleccion")
def descargar_excel_personal_seleccion(
    ids: str = Query(..., description="Lista de IDs separados por coma")
):
    """Exporta a Excel (.xlsx) únicamente los agentes seleccionados mediante checkboxes."""
    try:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        if not id_list:
            raise HTTPException(status_code=400, detail="No se enviaron IDs válidos de personal.")

        excel_bytes = excel_service.exportar_personal_seleccion_excel(id_list)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=Personal_Seleccionado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------
# MÓDULO 3: LICENCIAS & CERTIFICADOS MÉDICOS
# -------------------------------------------------------------
@app.get("/api/licencias")
def listar_licencias(
    busqueda: str = Query(""),
    estado_justificacion: str = Query(""),
    tipo_licencia: str = Query(""),
    personal_id: Optional[int] = Query(None)
):
    return licencias_service.listar_licencias(
        busqueda=busqueda,
        estado_justificacion=estado_justificacion,
        tipo_licencia=tipo_licencia,
        personal_id=personal_id,
        incluir_eliminados=False
    )

@app.post("/api/licencias")
def crear_licencia(data: LicenciaCreate):
    return licencias_service.crear_licencia(data.dict())

@app.put("/api/licencias/{licencia_id}/estado")
def cambiar_estado_justificacion(licencia_id: int, estado: str = Form(...)):
    return licencias_service.cambiar_estado_justificacion(licencia_id, estado)

@app.put("/api/licencias/{licencia_id}/auditoria")
def actualizar_auditoria_medica(licencia_id: int, auditado: int = Form(...), observacion: str = Form("")):
    return licencias_service.actualizar_auditoria_medica(licencia_id, auditado, observacion)

@app.get("/api/licencias/alertas")
def obtener_alertas_licencias():
    return licencias_service.obtener_alertas_licencias()

@app.get("/api/licencias/resumen-anual")
def obtener_resumen_anual_licencias(personal_id: Optional[int] = Query(None), anio: Optional[int] = Query(None)):
    return licencias_service.obtener_resumen_anual_licencias(personal_id, anio)

@app.delete("/api/licencias/{licencia_id}")
def mover_licencia_a_papelera(licencia_id: int):
    return {"success": licencias_service.mover_licencia_a_papelera(licencia_id)}

@app.post("/api/licencias/{licencia_id}/restaurar")
def restaurar_licencia(licencia_id: int):
    return {"success": licencias_service.restaurar_licencia(licencia_id)}

@app.get("/api/licencias/normativa")
def obtener_normativa():
    return licencias_service.obtener_normativa()

@app.get("/api/licencias/tipos")
def obtener_tipos_licencia():
    """Lista dinámica de todos los tipos de licencia del catálogo DPRH."""
    return licencias_service.obtener_tipos_licencia()

@app.get("/api/licencias/pendientes")
def obtener_dias_pendientes(personal_id: Optional[int] = Query(None)):
    """Retorna resumen de suspensiones con días pendientes por agente."""
    return licencias_service.obtener_resumen_pendientes_personal(personal_id)

@app.post("/api/licencias/{licencia_id}/suspender")
def suspender_licencia(licencia_id: int, data: SuspensionLicenciaCreate):
    """Registra la suspensión de una licencia en curso con sus días pendientes."""
    d = data.dict()
    d["licencia_id"] = licencia_id
    return licencias_service.registrar_suspension(d)

@app.get("/api/licencias/{licencia_id}/suspensiones")
def obtener_suspensiones_licencia(licencia_id: int):
    """Obtiene las suspensiones registradas para una licencia específica."""
    return licencias_service.obtener_suspensiones_por_licencia(licencia_id)

@app.put("/api/suspensiones/{suspension_id}/retomar")
def retomar_suspension_licencia(suspension_id: int, fecha_alta: str = Form(...), observaciones: str = Form("")):
    """Marca una suspensión como retomada (cuando el agente toma los días pendientes)."""
    return licencias_service.retomar_suspension(suspension_id, fecha_alta, observaciones)

@app.get("/api/personal/{personal_id}/suspensiones")
def obtener_suspensiones_personal(personal_id: int):
    """Obtiene todas las suspensiones de un agente."""
    return licencias_service.obtener_suspensiones_por_personal(personal_id)


# -------------------------------------------------------------
# MÓDULO 5: IMPORTAR EXCEL
# -------------------------------------------------------------
@app.post("/api/excel/inspeccionar")
async def inspeccionar_excel(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        sheets_info = excel_service.inspeccionar_archivo_excel(contents)
        return {"success": True, "hojas": sheets_info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer archivo Excel: {str(e)}")

@app.post("/api/excel/importar")
async def importar_excel(file: UploadFile = File(...), sheet_name: str = Form("Personal"), modo: str = Form("upsert")):
    contents = await file.read()
    try:
        resultado = excel_service.importar_personal_excel(contents, sheet_name, modo)
        if "error" in resultado:
            raise HTTPException(status_code=400, detail=resultado["error"])
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al importar: {str(e)}")

@app.get("/api/excel/plantilla-ejemplo")
def descargar_plantilla_ejemplo():
    excel_stream = excel_service.generar_plantilla_excel_ejemplo()
    if isinstance(excel_stream, bytes):
        excel_stream = io.BytesIO(excel_stream)
    filename = "Plantilla_Ejemplo_Personal_DPRH.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# -------------------------------------------------------------
# MÓDULO 6: EXPORTAR EXCEL (4 PESTAÑAS)
# -------------------------------------------------------------
@app.get("/api/excel/exportar")
def exportar_excel():
    excel_stream = excel_service.exportar_libro_completo()
    filename = f"Gestion_Personal_Recursos_Hidricos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# -------------------------------------------------------------
# MÓDULO 7: ORGANIGRAMA Y ÁREAS
# -------------------------------------------------------------
@app.get("/api/organigrama")
def obtener_organigrama():
    return organigrama_service.obtener_arbol_organigrama()

@app.get("/api/areas")
def listar_areas():
    return organigrama_service.listar_areas()

@app.post("/api/areas")
def crear_area(data: AreaModel):
    nuevo_id = organigrama_service.crear_area(data.dict())
    return {"id": nuevo_id, "success": True}

@app.put("/api/areas/{area_id}")
def actualizar_area(area_id: int, data: AreaModel):
    return organigrama_service.actualizar_area(area_id, data.dict())

@app.delete("/api/areas/{area_id}")
def eliminar_area(area_id: int):
    return organigrama_service.eliminar_area(area_id)

# -------------------------------------------------------------
# AUTENTICACIÓN Y USUARIOS (MÓDULO 1: CONTROL DE ACCESO Y PERMISOS)
# -------------------------------------------------------------
import json

@app.post("/api/auth/login")
def login(data: UsuarioLogin):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, nombre_completo, rol, permisos, activo FROM usuarios WHERE username = ? AND activo = 1", (data.username,))
    user = cursor.fetchone()
    
    if not user or not verify_password(data.password, user[2]):
        conn.close()
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    user_id = user[0]
    username = user[1]
    stored_hash = user[2]

    # Migración transparente si la contraseña no está en formato PBKDF2
    if not stored_hash.startswith("pbkdf2$"):
        nuevo_hash = hash_password(data.password)
        cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (nuevo_hash, user_id))
        conn.commit()

    # Generación de token de sesión de 256 bits y expiración a las 12 horas
    token = generar_token_sesion()
    expiracion = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
    cursor.execute("INSERT INTO sesiones (usuario_id, token, expiracion) VALUES (?, ?, ?)", (user_id, token, expiracion))
    conn.commit()
    conn.close()

    permisos_list = []
    if user[5]:
        try:
            permisos_list = json.loads(user[5])
        except Exception:
            permisos_list = []

    auditoria_service.registrar_auditoria("LOGIN", "usuarios", user_id, f"Inicio de sesión exitoso: {username}")

    return {
        "success": True,
        "token": token,
        "usuario": {
            "id": user_id,
            "username": username,
            "nombre_completo": user[3],
            "rol": user[4],
            "permisos": permisos_list
        }
    }

@app.get("/api/usuarios")
def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, nombre_completo, rol, permisos, activo, created_at FROM usuarios ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    res = []
    for r in rows:
        u = dict(r)
        if u.get("permisos"):
            try:
                u["permisos"] = json.loads(u["permisos"])
            except Exception:
                u["permisos"] = []
        else:
            u["permisos"] = []
        res.append(u)
    return res

@app.post("/api/usuarios")
def crear_usuario(data: UsuarioCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="El nombre de usuario ya se encuentra registrado")
    
    permisos_str = json.dumps(data.permisos or [])
    pwd_hash = hash_password(data.password)
    cursor.execute("""
        INSERT INTO usuarios (username, password_hash, nombre_completo, rol, permisos, activo)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (data.username, pwd_hash, data.nombre_completo, data.rol, permisos_str))
    nuevo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    auditoria_service.registrar_auditoria("CREAR", "usuarios", nuevo_id, f"Usuario creado: {data.username} con rol {data.rol}")
    return {"success": True, "id": nuevo_id}

@app.put("/api/usuarios/{usuario_id}")
def actualizar_usuario(usuario_id: str, data: UsuarioUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Permitir buscar tanto por id numérico como por username ('admin' o '1')
    if str(usuario_id).isdigit():
        cursor.execute("SELECT id, username, rol FROM usuarios WHERE id = ?", (int(usuario_id),))
    else:
        cursor.execute("SELECT id, username, rol FROM usuarios WHERE username = ?", (str(usuario_id),))

    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    target_id = user_row[0]
    username = user_row[1]
    is_admin = (username == 'admin')

    campos = []
    valores = []

    if data.nombre_completo is not None and data.nombre_completo.strip():
        campos.append("nombre_completo = ?")
        valores.append(data.nombre_completo.strip())

    if data.password is not None and data.password.strip():
        campos.append("password_hash = ?")
        valores.append(hash_password(data.password.strip()))

    if data.rol is not None:
        rol_final = 'admin' if is_admin else data.rol
        campos.append("rol = ?")
        valores.append(rol_final)

    if data.permisos is not None:
        permisos_final = ["*"] if is_admin else data.permisos
        campos.append("permisos = ?")
        valores.append(json.dumps(permisos_final))

    if data.activo is not None:
        activo_final = 1 if is_admin else data.activo
        campos.append("activo = ?")
        valores.append(activo_final)

    if campos:
        valores.append(target_id)
        sql = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(sql, valores)
        conn.commit()

    conn.close()
    auditoria_service.registrar_auditoria("EDITAR", "usuarios", target_id, f"Actualización de usuario '{username}'")
    return {"success": True, "id": target_id}

@app.delete("/api/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if row[0] == 'admin':
        conn.close()
        raise HTTPException(status_code=400, detail="No se puede eliminar el usuario administrador principal")

    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    conn.commit()
    conn.close()
    auditoria_service.registrar_auditoria("ELIMINAR", "usuarios", usuario_id, f"Usuario eliminado: {row[0]}")
    return {"success": True}


# -------------------------------------------------------------
# MÓDULO 8: PAPELERA DE RECICLAJE
# -------------------------------------------------------------
@app.get("/api/papelera")
def obtener_papelera():
    personal_del = personal_service.listar_personal(incluir_eliminados=True)
    licencias_del = licencias_service.listar_licencias(incluir_eliminados=True)
    return {
        "personal": personal_del,
        "licencias": licencias_del,
        "total": len(personal_del) + len(licencias_del)
    }

@app.delete("/api/papelera/vaciar")
def vaciar_papelera():
    return {"success": personal_service.vaciar_papelera()}

# -------------------------------------------------------------
# CONFIGURACIÓN, AUDITORÍA, VBA Y BASE DE DATOS
# -------------------------------------------------------------
@app.get("/api/auditoria")
def obtener_auditoria(limite: int = Query(100), accion: Optional[str] = Query(None)):
    return auditoria_service.obtener_logs(limite=limite, filtro_accion=accion)

@app.get("/api/vba/codigo")
def obtener_codigo_vba():
    return vba_generator.obtener_codigo_vba()

@app.get("/api/sistema/db-backup")
def descargar_backup_db():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Base de datos no encontrada")
    return FileResponse(DB_PATH, media_type="application/x-sqlite3", filename=f"recursos_hidricos_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db")

@app.get("/api/sistema/auto-launch")
def obtener_estado_autolaunch():
    enabled = False
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, "GestionPersonalRecursosHidricos")
            winreg.CloseKey(key)
            enabled = True
        except Exception:
            enabled = False
    return {"enabled": enabled}

@app.post("/api/sistema/auto-launch")
def configurar_autolaunch(enabled: bool = Form(...)):
    if sys.platform == "win32":
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            if enabled:
                bat_path = os.path.join(ROOT_DIR, "iniciar_sistema.bat")
                cmd = f'"{bat_path}"' if os.path.exists(bat_path) else f'"{sys.executable}" -m backend.main'
                winreg.SetValueEx(key, "GestionPersonalRecursosHidricos", 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, "GestionPersonalRecursosHidricos")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return {"success": True, "enabled": enabled}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"success": False, "detail": "Plataforma no soportada"}

# -------------------------------------------------------------
# CLOUDFLARE TUNNEL (Token Oficial Permanente & Quick Tunnel)
# -------------------------------------------------------------
CLOUDFLARE_TUNNEL_STATE = {"activo": False, "url": None, "proceso": None, "tipo": None}

def _drain_cloudflared_pipe(proc, log_file_path):
    """Lee continuamente la salida de cloudflared para evitar bloqueos del buffer en Windows."""
    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            for line in proc.stderr:
                f.write(line)
                f.flush()
    except Exception:
        pass

def extraer_token_cloudflare(texto_crudo: str) -> str:
    """Extrae de forma universal el token limpio descartando comandos previos sin depender del prefijo."""
    if not texto_crudo:
        return ""
    import re
    texto = texto_crudo.strip().strip('"').strip("'")
    
    # 1. Si contiene "service install <TOKEN>", extraer lo que esté a la derecha
    m_install = re.split(r'service\s+install\s+', texto, flags=re.IGNORECASE)
    if len(m_install) > 1:
        return m_install[1].strip().strip('"').strip("'")

    # 2. Si contiene "--token <TOKEN>", extraer lo que esté a la derecha
    m_token = re.split(r'--token\s+', texto, flags=re.IGNORECASE)
    if len(m_token) > 1:
        return m_token[1].strip().strip('"').strip("'")

    # 3. Si empieza con comando de cloudflared (ej: cloudflared.exe ... <TOKEN>)
    if re.match(r'^cloudflared(?:\.exe)?\s+', texto, flags=re.IGNORECASE):
        partes = texto.split()
        if partes:
            return partes[-1].strip().strip('"').strip("'")

    # 4. Si es el token directo, retornar tal cual
    return texto

def iniciar_proceso_tunel_token(token_crudo: str):
    global CLOUDFLARE_TUNNEL_STATE
    import subprocess, threading
    from pycloudflared.util import get_info, download
    from pathlib import Path

    token = extraer_token_cloudflare(token_crudo)
    if not token:
        raise ValueError("Token de Cloudflare inválido o vacío")

    # Detener si hubiera uno anterior
    detener_proceso_tunel()

    info = get_info()
    if not Path(info.executable).exists():
        download(info)

    args = [
        info.executable,
        "tunnel",
        "run",
        "--token", token,
        "--heartbeat-interval", "5s",
        "--heartbeat-count", "5"
    ]

    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        bufsize=1
    )

    log_path = os.path.join(ROOT_DIR, "cloudflared_token.log")
    t = threading.Thread(target=_drain_cloudflared_pipe, args=(proc, log_path), daemon=True)
    t.start()

    CLOUDFLARE_TUNNEL_STATE["activo"] = True
    CLOUDFLARE_TUNNEL_STATE["proceso"] = proc
    CLOUDFLARE_TUNNEL_STATE["tipo"] = "token"
    return True

def detener_proceso_tunel():
    global CLOUDFLARE_TUNNEL_STATE
    proc = CLOUDFLARE_TUNNEL_STATE.get("proceso")
    if proc:
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()
        except Exception:
            pass
    CLOUDFLARE_TUNNEL_STATE["activo"] = False
    CLOUDFLARE_TUNNEL_STATE["url"] = None
    CLOUDFLARE_TUNNEL_STATE["proceso"] = None
    CLOUDFLARE_TUNNEL_STATE["tipo"] = None

@app.get("/api/sistema/tunel-token")
def obtener_config_tunel_token():
    global CLOUDFLARE_TUNNEL_STATE
    proc = CLOUDFLARE_TUNNEL_STATE.get("proceso")
    activo = bool(proc and proc.poll() is None)
    if not activo and CLOUDFLARE_TUNNEL_STATE.get("activo"):
        CLOUDFLARE_TUNNEL_STATE["activo"] = False
        CLOUDFLARE_TUNNEL_STATE["proceso"] = None

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clave, valor FROM configuracion WHERE clave IN ('cf_tunnel_token', 'cf_tunnel_autostart', 'cf_tunnel_hostname')")
    filas = dict(cursor.fetchall())
    conn.close()

    return {
        "token": filas.get("cf_tunnel_token", ""),
        "autostart": filas.get("cf_tunnel_autostart", "0") == "1",
        "hostname": filas.get("cf_tunnel_hostname", ""),
        "activo": activo,
        "tipo": CLOUDFLARE_TUNNEL_STATE.get("tipo")
    }

@app.post("/api/sistema/tunel-token")
def guardar_config_tunel_token(
    token: str = Form(""),
    autostart: bool = Form(False),
    hostname: str = Form("")
):
    token_limpio = extraer_token_cloudflare(token)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('cf_tunnel_token', ?)", (token_limpio,))
    cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('cf_tunnel_autostart', ?)", ("1" if autostart else "0",))
    cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('cf_tunnel_hostname', ?)", (hostname.strip(),))
    conn.commit()
    conn.close()
    return {"success": True, "token": token_limpio, "autostart": autostart, "hostname": hostname.strip()}

@app.post("/api/sistema/tunel-token/iniciar")
def iniciar_tunel_token_endpoint():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracion WHERE clave = 'cf_tunnel_token'")
    row = cursor.fetchone()
    conn.close()

    token = row["valor"] if row else ""
    if not token:
        raise HTTPException(status_code=400, detail="No hay ningún Token de Cloudflare configurado. Ingréselo y guarde primero.")

    try:
        iniciar_proceso_tunel_token(token)
        return {"success": True, "activo": True, "mensaje": "Túnel Cloudflare Oficial conectado exitosamente."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar túnel con token: {str(e)}")

@app.post("/api/sistema/tunel-token/detener")
def detener_tunel_endpoint():
    detener_proceso_tunel()
    return {"success": True, "activo": False, "mensaje": "Túnel detenido."}

@app.get("/api/sistema/tunel-cloudflare")
def obtener_estado_tunel():
    global CLOUDFLARE_TUNNEL_STATE
    proc = CLOUDFLARE_TUNNEL_STATE.get("proceso")
    if proc and proc.poll() is not None:
        CLOUDFLARE_TUNNEL_STATE["activo"] = False
        CLOUDFLARE_TUNNEL_STATE["url"] = None
        CLOUDFLARE_TUNNEL_STATE["proceso"] = None

    return {
        "activo": CLOUDFLARE_TUNNEL_STATE["activo"],
        "url": CLOUDFLARE_TUNNEL_STATE["url"],
        "tipo": CLOUDFLARE_TUNNEL_STATE.get("tipo")
    }

@app.post("/api/sistema/tunel-cloudflare/iniciar")
def iniciar_tunel_remoto():
    global CLOUDFLARE_TUNNEL_STATE
    try:
        import subprocess, re, threading
        from pycloudflared.util import get_info, download
        from pathlib import Path

        proc = CLOUDFLARE_TUNNEL_STATE.get("proceso")
        if proc and proc.poll() is None and CLOUDFLARE_TUNNEL_STATE["url"]:
            return {"success": True, "url": CLOUDFLARE_TUNNEL_STATE["url"]}

        # Limpiar cualquier instancia previa o bloqueada de cloudflared.exe
        try:
            subprocess.run(["taskkill", "/IM", "cloudflared.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        info = get_info()
        if not Path(info.executable).exists():
            download(info)

        target_url = "https://127.0.0.1:8000"
        args = [
            info.executable, 
            "tunnel", 
            "--url", target_url, 
            "--no-tls-verify",
            "--heartbeat-interval", "5s",
            "--heartbeat-count", "5"
        ]
        
        proc = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            bufsize=1
        )
        
        url_pat = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
        found_url = None
        
        log_path = os.path.join(ROOT_DIR, "cloudflared.log")
        with open(log_path, "w", encoding="utf-8") as log_f:
            for _ in range(80):
                line = proc.stderr.readline()
                if not line:
                    break
                log_f.write(line)
                log_f.flush()
                m = url_pat.search(line)
                if m:
                    found_url = m.group(0)
                    break
        
        if not found_url:
            proc.terminate()
            raise RuntimeError("No se pudo obtener la URL de Cloudflare Tunnel")

        # Mantener el proceso consumiendo stderr para que nunca se congele
        t = threading.Thread(target=_drain_cloudflared_pipe, args=(proc, log_path), daemon=True)
        t.start()

        CLOUDFLARE_TUNNEL_STATE["activo"] = True
        CLOUDFLARE_TUNNEL_STATE["url"] = found_url
        CLOUDFLARE_TUNNEL_STATE["proceso"] = proc
        CLOUDFLARE_TUNNEL_STATE["tipo"] = "quick"
        
        # Sincronización automática autónoma de la URL con el README.md en la rama gh-pages (solo si la clave está autorizada)
        try:
            if auto_readme_sync.tiene_senal_verde():
                print(f"[AutoSync] Enlace Cloudflare detectado: {found_url}. Publicando README.md autónomamente en gh-pages...")
                res_sync = auto_readme_sync.actualizar_readme_gh_pages(found_url)
                if res_sync.get("success"):
                    print(f"[AutoSync] ¡README.md actualizado y publicado en gh-pages con éxito!")
                else:
                    print(f"[AutoSync Warning] No se pudo hacer push a gh-pages: {res_sync.get('error') or res_sync.get('mensaje')}")
            else:
                print(f"[AutoSync Info] Enlace Cloudflare listo: {found_url}. Sincronización con GitHub Pages pausada (copie la Deploy Key al repositorio de GitHub y presione 'Probar Conexión').")
        except Exception as e_sync:
            print(f"[Sync Warning] {e_sync}")

        return {"success": True, "url": found_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al iniciar Cloudflare Tunnel: {str(e)}")

@app.post("/api/sistema/tunel-cloudflare/detener")
def detener_tunel_remoto_endpoint():
    detener_proceso_tunel()
    return {"success": True, "activo": False, "mensaje": "Túnel temporal detenido."}

@app.get("/api/sistema/tunel-rapido-config")
def obtener_config_tunel_rapido():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT clave, valor FROM configuracion WHERE clave = 'cf_quick_autostart'")
    row = cursor.fetchone()
    conn.close()
    autostart = row["valor"] == "1" if row else False
    
    global CLOUDFLARE_TUNNEL_STATE
    proc = CLOUDFLARE_TUNNEL_STATE.get("proceso")
    activo = bool(proc and proc.poll() is None and CLOUDFLARE_TUNNEL_STATE.get("url"))
    
    return {
        "autostart": autostart,
        "activo": activo,
        "url": CLOUDFLARE_TUNNEL_STATE.get("url") if activo else None
    }

@app.post("/api/sistema/tunel-rapido-config")
def guardar_config_tunel_rapido(autostart: bool = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES ('cf_quick_autostart', ?)", ("1" if autostart else "0",))
    conn.commit()
    conn.close()
    return {"success": True, "autostart": autostart}

# -------------------------------------------------------------
# MÓDULO PUBLICACIÓN WEB / GITHUB PAGES SYNC
# -------------------------------------------------------------
@app.get("/api/sistema/github-sync-config")
def obtener_config_github_sync():
    return github_sync_service.obtener_config_github_sync()

@app.post("/api/sistema/github-sync-config")
def guardar_config_github_sync(
    repo_dir: str = Form(""),
    enabled: bool = Form(True),
    remote_url: Optional[str] = Form(None),
    branch: Optional[str] = Form(None),
    token: Optional[str] = Form(None)
):
    repo_dir_val = repo_dir.strip() if isinstance(repo_dir, str) else ""
    enabled_val = enabled if isinstance(enabled, bool) else True
    remote_val = remote_url.strip() if isinstance(remote_url, str) and remote_url else "https://github.com/ulises47123/Recursos-H-dricos.git"
    branch_val = branch.strip() if isinstance(branch, str) and branch else "gh-pages"

    data = {
        "github_repo_dir": repo_dir_val,
        "github_sync_enabled": "1" if enabled_val else "0",
        "github_remote_url": remote_val,
        "github_branch": branch_val
    }
    if isinstance(token, str) and token.strip():
        data["github_token"] = token.strip()
    return github_sync_service.guardar_config_github_sync(data)

@app.post("/api/sistema/github-sync/reintentar")
def reintentar_git_push_endpoint():
    res = github_sync_service.reintentar_push_fallidos()
    return res

# -------------------------------------------------------------
# GESTOR DE GIT Y DEPLOY KEYS SSH (GUI ADMINISTRADOR)
# -------------------------------------------------------------
@app.get("/api/sistema/git-estado")
def get_git_estado():
    git_info = git_manager_service.verificar_git_instalado()
    key_info = git_manager_service.obtener_o_generar_deploy_key()
    return {
        "git": git_info,
        "deploy_key": key_info
    }

@app.post("/api/sistema/git-instalar")
def post_git_instalar():
    return git_manager_service.instalar_git_sistema()

@app.post("/api/sistema/git-generar-deploy-key")
def post_git_generar_deploy_key():
    return git_manager_service.obtener_o_generar_deploy_key()

@app.post("/api/sistema/git-probar-conexion")
def post_git_probar_conexion():
    return git_manager_service.probar_conexion_ssh_github()

@app.post("/api/sistema/git-subir-proyecto")
def post_git_subir_proyecto(mensaje: str = Form("")):
    return git_manager_service.subir_todo_el_proyecto_github(mensaje)

@app.post("/api/sistema/git-subir-portal")
def post_git_subir_portal():
    return git_manager_service.subir_portal_github_pages()

# -------------------------------------------------------------
# MÓDULO AUTO-README SYNC / PUBLICACIÓN AUTOMÁTICA DEL PORTAL
# -------------------------------------------------------------
@app.get("/api/sistema/github/llave-publica")
def get_github_llave_publica():
    return {
        "llave_publica": auto_readme_sync.obtener_llave_publica(),
        "senal_verde": auto_readme_sync.tiene_senal_verde()
    }

@app.post("/api/sistema/github/probar")
def post_github_probar():
    res = auto_readme_sync.probar_conexion()
    ok = bool(res.get("success") or res.get("autenticado"))
    msg = res.get("mensaje", "")
    return {"ok": ok, "mensaje": msg}

@app.get("/api/sistema/github/estado")
def get_github_estado():
    st = auto_readme_sync.obtener_estado_sync()
    return {
        "senal_verde": bool(st.get("github_signal_ok")),
        "tunnel_url": st.get("tunnel_url") or "",
        "ultimo_sync": st.get("ultimo_sync") or st.get("ultimo_error") or ""
    }

@app.get("/api/auto-readme/status")
def get_auto_readme_status():
    return auto_readme_sync.obtener_estado_sync()

@app.post("/api/auto-readme/probar-conexion")
def probar_conexion_auto_readme():
    return auto_readme_sync.probar_conexion()

@app.post("/api/auto-readme/sincronizar")
def sincronizar_auto_readme():
    return auto_readme_sync.sincronizacion_automatica()

# -------------------------------------------------------------
# MÓDULO GOOGLE DRIVE: COPIAS DE SEGURIDAD Y RESTAURACIÓN
# -------------------------------------------------------------
@app.get("/api/sistema/gdrive/config")
def get_gdrive_config():
    return gdrive_service.obtener_config_gdrive()

@app.post("/api/sistema/gdrive/conectar")
def conectar_gdrive(email: str = Form(...), credentials_json: str = Form(""), folder_path: str = Form("")):
    try:
        return gdrive_service.autenticar_simulado_o_credenciales(email, credentials_json, folder_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/sistema/gdrive/desconectar")
def desconectar_gdrive_endpoint():
    return gdrive_service.desconectar_gdrive()

@app.get("/api/sistema/gdrive/backups")
def listar_backups_gdrive_endpoint():
    return gdrive_service.listar_backups_gdrive()

@app.post("/api/sistema/gdrive/backup-ahora")
def realizar_backup_gdrive_endpoint():
    try:
        return gdrive_service.realizar_backup_gdrive(usuario="Admin")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando backup: {str(e)}")

@app.post("/api/sistema/gdrive/restaurar")
def restaurar_backup_gdrive_endpoint(backup_nombre: str = Form(...)):
    try:
        return gdrive_service.restaurar_backup_gdrive(backup_nombre, usuario="Admin")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restaurando backup: {str(e)}")


# Servir Frontend Estático
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    from backend.ssl_generator import ensure_ssl_certificates
    
    ssl_key, ssl_cert, _ = ensure_ssl_certificates()
    if os.path.exists(ssl_key) and os.path.exists(ssl_cert):
        uvicorn.run(
            "backend.main:app", 
            host="0.0.0.0", 
            port=8000, 
            ssl_keyfile=ssl_key, 
            ssl_certfile=ssl_cert,
            reload=False
        )
    else:
        uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)

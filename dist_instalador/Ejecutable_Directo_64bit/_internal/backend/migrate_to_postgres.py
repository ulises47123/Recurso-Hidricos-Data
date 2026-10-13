#!/usr/bin/env python3
"""
backend/migrate_to_postgres.py
Script interactivo y por línea de comandos para migrar automáticamente
todo el esquema y datos desde 'recursos_hidricos.db' (SQLite) a PostgreSQL.

Características:
  - Conexión mediante URL (postgresql://...) o parámetros independientes.
  - Modo interactivo (solicita datos si no se especifican por CLI).
  - Conversión estricta de tipos de datos SQLite -> PostgreSQL (SERIAL, DOUBLE PRECISION, TIMESTAMP).
  - Desactivación temporal de triggers y restricciones de claves foráneas para carga masiva sin bloqueos.
  - Inserción en lote (batch insert) de alta velocidad.
  - Reajuste automático de secuencias (SERIAL / setval) para evitar colisiones de IDs futuros.
  - Creación de índices optimizados.
  - Verificación y reporte detallado de filas migradas por tabla.
"""

import os
import sys
import argparse
import getpass
import sqlite3
import time
from typing import Dict, List, Tuple, Any, Optional

try:
    import psycopg2
    from psycopg2 import extras, sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2 = None

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SQLITE_PATH = os.path.join(ROOT_DIR, "recursos_hidricos.db")

# Orden topológico recomendado de migración para respetar dependencias foráneas
TABLES_TOPOLOGICAL_ORDER = [
    "configuracion",
    "feriados",
    "areas",
    "personal",
    "usuarios",
    "auditoria_logs",
    "licencias",
    "contratos",
    "familiares",
    "historial_funciones",
    "documentos_legajo",
    "adicionales_personal",
    "historial_categorias",
    "beneficios_articulo_79",
    "suspensiones_licencia",
    "compensatorios_saldo",
    "compensatorios_cargas",
    "compensatorios_solicitudes"
]

# Esquema DDL oficial optimizado para PostgreSQL
POSTGRES_SCHEMA_DDL = {
    "areas": """
    CREATE TABLE IF NOT EXISTS areas (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        codigo TEXT UNIQUE,
        nivel INTEGER DEFAULT 1,
        parent_id INTEGER,
        responsable TEXT,
        descripcion TEXT,
        orden INTEGER DEFAULT 0,
        FOREIGN KEY (parent_id) REFERENCES areas(id) ON DELETE SET NULL
    );
    """,

    "personal": """
    CREATE TABLE IF NOT EXISTS personal (
        id SERIAL PRIMARY KEY,
        dni TEXT UNIQUE NOT NULL,
        legajo TEXT UNIQUE,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        email TEXT,
        telefono TEXT,
        fecha_nacimiento TEXT,
        genero TEXT,
        direccion TEXT,
        fecha_ingreso TEXT,
        situacion_revista TEXT NOT NULL,
        cargo TEXT,
        funcion TEXT,
        area_id INTEGER,
        estado TEXT DEFAULT 'Activo',
        deleted_at TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cuil TEXT,
        fecha_ingreso_admin_pub TEXT,
        fecha_ingreso_recursos_hidricos_obra TEXT,
        fecha_ingreso_recursos_hidricos_planta TEXT,
        asistencia TEXT DEFAULT 'Reloj',
        categoria_actual TEXT,
        categoria_fecha_alta TEXT,
        situacion_revista_obs TEXT,
        lugar_trabajo TEXT DEFAULT 'Oficina Central',
        lugar_trabajo_otro TEXT,
        sentencia TEXT,
        actividad TEXT,
        profesional_titulo TEXT,
        direccion_organismo TEXT DEFAULT 'Dirección Provincial de Recursos Hídricos',
        area_trabajo TEXT,
        departamento_trabajo TEXT,
        division_trabajo TEXT,
        sector_trabajo TEXT,
        horario TEXT DEFAULT '07:00 a 13:00',
        gremio TEXT,
        FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
    );
    """,

    "licencias": """
    CREATE TABLE IF NOT EXISTS licencias (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        tipo_licencia TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        dias_totales INTEGER NOT NULL,
        diagnostico TEXT,
        certificado_numero TEXT,
        medico_nombre TEXT,
        medico_matricula TEXT,
        estado_justificacion TEXT DEFAULT 'Pendiente',
        observaciones TEXT,
        deleted_at TEXT DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        auditado_salud_provincial INTEGER DEFAULT 0,
        observacion_auditoria TEXT DEFAULT '',
        periodo_anual INTEGER,
        familiar_nombre TEXT,
        familiar_parentesco TEXT,
        km_distancia INTEGER,
        dias_adicionales_viaje INTEGER DEFAULT 0,
        constancia_adjunto TEXT,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "contratos": """
    CREATE TABLE IF NOT EXISTS contratos (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        tipo_contrato TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT,
        monto_honorarios DOUBLE PRECISION DEFAULT 0.0,
        resolucion_numero TEXT,
        estado TEXT DEFAULT 'Vigente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "familiares": """
    CREATE TABLE IF NOT EXISTS familiares (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        dni TEXT,
        parentesco TEXT NOT NULL,
        fecha_nacimiento TEXT,
        es_beneficiario INTEGER DEFAULT 1,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "historial_funciones": """
    CREATE TABLE IF NOT EXISTS historial_funciones (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        cargo TEXT NOT NULL,
        funcion TEXT,
        area_id INTEGER,
        fecha_desde TEXT NOT NULL,
        fecha_hasta TEXT,
        motivo_cambio TEXT,
        instrumento_legal TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE,
        FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
    );
    """,

    "documentos_legajo": """
    CREATE TABLE IF NOT EXISTS documentos_legajo (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        tipo_documento TEXT NOT NULL,
        titulo TEXT NOT NULL,
        nombre_archivo TEXT NOT NULL,
        ruta_archivo TEXT NOT NULL,
        fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        observaciones TEXT,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "usuarios": """
    CREATE TABLE IF NOT EXISTS usuarios (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'admin',
        permisos TEXT,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """,

    "adicionales_personal": """
    CREATE TABLE IF NOT EXISTS adicionales_personal (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        tipo_adicional TEXT NOT NULL,
        monto_o_porcentaje TEXT,
        fecha_alta TEXT NOT NULL,
        fecha_baja TEXT,
        resolucion_numero TEXT,
        motivo_cambio TEXT,
        ruta_archivo TEXT,
        nombre_archivo TEXT,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "historial_categorias": """
    CREATE TABLE IF NOT EXISTS historial_categorias (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        fecha_cambio TEXT NOT NULL,
        resolucion_numero TEXT,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "beneficios_articulo_79": """
    CREATE TABLE IF NOT EXISTS beneficios_articulo_79 (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        anio_periodo INTEGER NOT NULL,
        edad_cumplida INTEGER,
        fecha_cumpleanios TEXT,
        fecha_cobro TEXT NOT NULL,
        monto_asignado DOUBLE PRECISION DEFAULT 0.0,
        estado_pago TEXT DEFAULT 'Cobrado',
        resolucion_numero TEXT,
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "suspensiones_licencia": """
    CREATE TABLE IF NOT EXISTS suspensiones_licencia (
        id SERIAL PRIMARY KEY,
        licencia_id INTEGER NOT NULL,
        personal_id INTEGER NOT NULL,
        fecha_suspension TEXT NOT NULL,
        dias_tomados_hasta_suspension INTEGER NOT NULL,
        dias_pendientes INTEGER NOT NULL,
        motivo_suspension TEXT,
        autorizado_por TEXT,
        fecha_alta TEXT,
        observaciones TEXT,
        estado TEXT DEFAULT 'Pendiente',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (licencia_id) REFERENCES licencias(id) ON DELETE CASCADE,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "auditoria_logs": """
    CREATE TABLE IF NOT EXISTS auditoria_logs (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT DEFAULT 'admin',
        accion TEXT NOT NULL,
        tabla_afectada TEXT NOT NULL,
        registro_id INTEGER,
        detalles TEXT,
        ip TEXT DEFAULT '127.0.0.1'
    );
    """,

    "configuracion": """
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT,
        descripcion TEXT
    );
    """,

    "compensatorios_saldo": """
    CREATE TABLE IF NOT EXISTS compensatorios_saldo (
        personal_id INTEGER PRIMARY KEY,
        dias_disponibles DOUBLE PRECISION DEFAULT 0.0,
        fecha_ultima_carga TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "compensatorios_cargas": """
    CREATE TABLE IF NOT EXISTS compensatorios_cargas (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        dias DOUBLE PRECISION NOT NULL,
        fecha_carga TEXT NOT NULL,
        motivo TEXT,
        acta_numero TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "compensatorios_solicitudes": """
    CREATE TABLE IF NOT EXISTS compensatorios_solicitudes (
        id SERIAL PRIMARY KEY,
        personal_id INTEGER NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        dias_descontados DOUBLE PRECISION NOT NULL,
        acta_numero TEXT,
        estado TEXT DEFAULT 'Pendiente',
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    );
    """,

    "feriados": """
    CREATE TABLE IF NOT EXISTS feriados (
        id SERIAL PRIMARY KEY,
        fecha TEXT UNIQUE NOT NULL,
        descripcion TEXT NOT NULL
    );
    """
}

POSTGRES_INDEXES_DDL = [
    "CREATE INDEX IF NOT EXISTS idx_personal_dni ON personal(dni);",
    "CREATE INDEX IF NOT EXISTS idx_personal_legajo ON personal(legajo);",
    "CREATE INDEX IF NOT EXISTS idx_personal_apellido_nombre ON personal(apellido, nombre);",
    "CREATE INDEX IF NOT EXISTS idx_personal_area_id ON personal(area_id);",
    "CREATE INDEX IF NOT EXISTS idx_personal_estado ON personal(estado);",
    "CREATE INDEX IF NOT EXISTS idx_personal_deleted ON personal(deleted_at);",
    "CREATE INDEX IF NOT EXISTS idx_licencias_personal ON licencias(personal_id);",
    "CREATE INDEX IF NOT EXISTS idx_licencias_fechas ON licencias(fecha_inicio, fecha_fin);",
    "CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria_logs(usuario);"
]


def convertir_tipo_sqlite_a_postgres(col_nombre: str, col_tipo: str, pk: bool = False, autoincrement: bool = False) -> str:
    """Convierte tipos de datos de SQLite a su equivalente óptimo en PostgreSQL."""
    col_tipo_upper = col_tipo.upper().strip()
    if pk and autoincrement:
        return "SERIAL PRIMARY KEY"
    if "INT" in col_tipo_upper:
        return "INTEGER"
    if "REAL" in col_tipo_upper or "FLOA" in col_tipo_upper or "DOUB" in col_tipo_upper:
        return "DOUBLE PRECISION"
    if "TEXT" in col_tipo_upper or "CHAR" in col_tipo_upper or "CLOB" in col_tipo_upper:
        return "TEXT"
    if "BLOB" in col_tipo_upper:
        return "BYTEA"
    return "TEXT"


def generar_ddl_tabla_dinamica(sqlite_conn: sqlite3.Connection, table_name: str) -> str:
    """Genera DDL PostgreSQL para tablas dinámicas que no estén en el diccionario predefinido."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = cursor.fetchall()
    
    col_defs = []
    for c in cols:
        cid, name, c_type, notnull, dflt_value, pk = c
        is_auto = bool(pk and "INT" in (c_type or "").upper())
        pg_type = convertir_tipo_sqlite_a_postgres(name, c_type or "TEXT", pk=bool(pk), autoincrement=is_auto)
        
        parts = [f'"{name}"', pg_type]
        if not pk and notnull:
            parts.append("NOT NULL")
        if dflt_value is not None:
            parts.append(f"DEFAULT {dflt_value}")
        col_defs.append(" ".join(parts))
        
    return f"CREATE TABLE IF NOT EXISTS {table_name} (\n  " + ",\n  ".join(col_defs) + "\n);"


def obtener_tablas_sqlite(sqlite_conn: sqlite3.Connection) -> List[str]:
    """Obtiene la lista de todas las tablas en la base de datos SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tablas_existentes = [r[0] for r in cursor.fetchall()]
    
    # Ordenar primero según el orden topológico y luego las demás tablas
    ordenadas = [t for t in TABLES_TOPOLOGICAL_ORDER if t in tablas_existentes]
    extras = [t for t in tablas_existentes if t not in ordenadas]
    return ordenadas + extras


def obtener_columnas_sqlite(sqlite_conn: sqlite3.Connection, table_name: str) -> List[str]:
    """Retorna los nombres de columnas de una tabla SQLite."""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [col[1] for col in cursor.fetchall()]


def reajustar_secuencias_postgres(pg_cursor) -> List[str]:
    """
    Reajusta todas las secuencias de las tablas con columnas SERIAL/IDENTITY
    al valor máximo actual (setval(seq, MAX(id))).
    """
    ajustes = []
    pg_cursor.execute("""
        SELECT table_name, column_name, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
          AND (column_default LIKE 'nextval(%' OR is_identity = 'YES')
    """)
    rows = pg_cursor.fetchall()
    
    for table_name, column_name, default_val in rows:
        try:
            # Obtener nombre de la secuencia asociado a la columna
            pg_cursor.execute(
                "SELECT pg_get_serial_sequence(%s, %s)",
                (table_name, column_name)
            )
            seq_res = pg_cursor.fetchone()
            seq_name = seq_res[0] if seq_res else None
            
            if seq_name:
                sql_setval = f"""
                    SELECT setval(
                        %s,
                        COALESCE((SELECT MAX({column_name}) FROM {table_name}), 1),
                        (SELECT MAX({column_name}) IS NOT NULL FROM {table_name})
                    )
                """
                pg_cursor.execute(sql_setval, (seq_name,))
                val = pg_cursor.fetchone()[0]
                ajustes.append(f"{table_name}.{column_name} -> secuencia '{seq_name}' en {val}")
        except Exception as e:
            ajustes.append(f"Error ajustando secuencia {table_name}.{column_name}: {e}")
            
    return ajustes


def migrar_sqlite_a_postgres(
    sqlite_path: str = DEFAULT_SQLITE_PATH,
    postgres_url: Optional[str] = None,
    host: Optional[str] = "localhost",
    port: int = 5432,
    user: Optional[str] = "postgres",
    password: Optional[str] = None,
    dbname: Optional[str] = "recursos_hidricos",
    drop_existing: bool = False,
    batch_size: int = 1000,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Ejecuta el proceso completo de migración desde SQLite a PostgreSQL.
    """
    if psycopg2 is None:
        raise ImportError(
            "La biblioteca 'psycopg2' no está instalada. Ejecute 'pip install psycopg2-binary' para continuar."
        )

    if not os.path.exists(sqlite_path):
        raise FileNotFoundError(f"La base de datos SQLite no existe en la ruta: {sqlite_path}")

    start_time = time.time()
    resumen = {
        "success": False,
        "tablas_migradas": {},
        "secuencias_reajustadas": [],
        "tiempo_segundos": 0.0,
        "errores": []
    }

    if verbose:
        print("=" * 65)
        print("  MIGRACIÓN OFICIAL SQLITE -> POSTGRESQL (RECURSOS HÍDRICOS)")
        print("=" * 65)
        print(f"[*] Origen SQLite: {sqlite_path}")

    # 1. Establecer conexión con PostgreSQL
    pg_conn = None
    try:
        if postgres_url:
            if verbose:
                print(f"[*] Conectando a PostgreSQL mediante URL...")
            pg_conn = psycopg2.connect(postgres_url)
        else:
            if verbose:
                print(f"[*] Conectando a PostgreSQL en {user}@{host}:{port}/{dbname}...")
            pg_conn = psycopg2.connect(
                host=host,
                port=port,
                user=user,
                password=password or "",
                dbname=dbname
            )
        pg_conn.autocommit = False
    except Exception as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos PostgreSQL: {e}")

    # 2. Conexión SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    try:
        pg_cur = pg_conn.cursor()

        # 3. Desactivar temporalmente triggers y comprobaciones de FK para carga masiva
        if verbose:
            print("[*] Desactivando temporalmente triggers y claves foráneas en PostgreSQL...")
        try:
            pg_cur.execute("SET session_replication_role = 'replica';")
        except Exception:
            pg_conn.rollback()

        tablas = obtener_tablas_sqlite(sqlite_conn)

        # 4. Limpieza previa si se solicitó drop_existing
        if drop_existing:
            if verbose:
                print("[!] Opción --drop-existing activa: eliminando tablas existentes en PostgreSQL...")
            for tabla in reversed(tablas):
                pg_cur.execute(f'DROP TABLE IF EXISTS "{tabla}" CASCADE;')
            pg_conn.commit()
            try:
                pg_cur.execute("SET session_replication_role = 'replica';")
            except Exception:
                pass

        # 5. Crear esquema en PostgreSQL
        if verbose:
            print("[*] Creando esquemas de tablas en PostgreSQL...")
        for tabla in tablas:
            ddl = POSTGRES_SCHEMA_DDL.get(tabla)
            if not ddl:
                ddl = generar_ddl_tabla_dinamica(sqlite_conn, tabla)
            pg_cur.execute(ddl)
        pg_conn.commit()

        # 6. Desactivar triggers específicos por tabla
        for tabla in tablas:
            try:
                pg_cur.execute(f'ALTER TABLE "{tabla}" DISABLE TRIGGER ALL;')
            except Exception:
                pass

        # 7. Migración de datos tabla por tabla
        for tabla in tablas:
            columnas = obtener_columnas_sqlite(sqlite_conn, tabla)
            if not columnas:
                continue

            # Leer datos de SQLite
            sql_select = f'SELECT {", ".join([f"`{c}`" for c in columnas])} FROM `{tabla}`'
            sqlite_cur = sqlite_conn.cursor()
            sqlite_cur.execute(sql_select)
            filas = sqlite_cur.fetchall()
            total_filas = len(filas)

            if total_filas > 0:
                cols_pg = [f'"{c}"' for c in columnas]
                col_list_str = ", ".join(cols_pg)
                placeholders = ", ".join(["%s"] * len(columnas))
                insert_query = f'INSERT INTO "{tabla}" ({col_list_str}) VALUES ({placeholders})'

                # Convertir objetos Row a tuplas limpias
                filas_tuplas = [tuple(f) for f in filas]

                # Inserción en bloques
                extras.execute_batch(pg_cur, insert_query, filas_tuplas, page_size=batch_size)

            resumen["tablas_migradas"][tabla] = total_filas
            if verbose:
                print(f"  -> {tabla:<26}: {total_filas} registros migrados con éxito.")

        pg_conn.commit()

        # 8. Re-activar triggers y claves foráneas
        if verbose:
            print("[*] Reactivando triggers y comprobaciones de integridad...")
        for tabla in tablas:
            try:
                pg_cur.execute(f'ALTER TABLE "{tabla}" ENABLE TRIGGER ALL;')
            except Exception:
                pass

        try:
            pg_cur.execute("SET session_replication_role = 'origin';")
        except Exception:
            pass

        # 9. Crear índices optimizados
        if verbose:
            print("[*] Creando índices de alto rendimiento en PostgreSQL...")
        for idx_sql in POSTGRES_INDEXES_DDL:
            try:
                pg_cur.execute(idx_sql)
            except Exception as e_idx:
                resumen["errores"].append(f"Error creando índice: {e_idx}")

        # 10. Reajustar secuencias (SERIAL / setval)
        if verbose:
            print("[*] Reajustando secuencias (SERIAL / setval)...")
        secuencias = reajustar_secuencias_postgres(pg_cur)
        resumen["secuencias_reajustadas"] = secuencias
        for s in secuencias:
            if verbose:
                print(f"  -> Secuencia sincronizada: {s}")

        pg_conn.commit()
        resumen["success"] = True

    except Exception as e:
        pg_conn.rollback()
        resumen["errores"].append(str(e))
        if verbose:
            print(f"\n[X] Error durante la migración: {e}")
        raise
    finally:
        sqlite_conn.close()
        if pg_conn:
            pg_conn.close()

    resumen["tiempo_segundos"] = round(time.time() - start_time, 2)
    if verbose:
        print("=" * 65)
        print(f"[V] ¡MIGRACIÓN COMPLETADA EXITOSAMENTE EN {resumen['tiempo_segundos']}s!")
        print("=" * 65)

    return resumen


def prompt_interactive_config() -> Dict[str, Any]:
    """Solicita parámetros de conexión de forma interactiva con valores por defecto."""
    print("\n--- CONFIGURACIÓN INTERACTIVA DE CONEXIÓN A POSTGRESQL ---")
    url_input = input("¿Desea ingresar una URL completa (ej: postgresql://...)? [s/N]: ").strip().lower()
    if url_input == "s" or url_input == "si":
        url = input("URL de conexión: ").strip()
        return {"postgres_url": url}

    host = input("Host [localhost]: ").strip() or "localhost"
    port_str = input("Puerto [5432]: ").strip() or "5432"
    port = int(port_str)
    user = input("Usuario [postgres]: ").strip() or "postgres"
    password = getpass.getpass("Contraseña: ")
    dbname = input("Nombre de base de datos [recursos_hidricos]: ").strip() or "recursos_hidricos"
    
    drop_str = input("¿Eliminar tablas existentes antes de migrar (drop)? [s/N]: ").strip().lower()
    drop_existing = (drop_str == "s" or drop_str == "si")

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "dbname": dbname,
        "drop_existing": drop_existing
    }


def main():
    parser = argparse.ArgumentParser(
        description="Migra automáticamente la base de datos SQLite de Recursos Hídricos a PostgreSQL."
    )
    parser.add_argument("--url", "-u", dest="postgres_url", help="URL de PostgreSQL (ej: postgresql://usuario:pass@host:5432/dbname)")
    parser.add_argument("--host", "-H", default=None, help="Host de PostgreSQL (default: localhost)")
    parser.add_argument("--port", "-p", type=int, default=5432, help="Puerto de PostgreSQL (default: 5432)")
    parser.add_argument("--user", "-U", default=None, help="Usuario de PostgreSQL (default: postgres)")
    parser.add_argument("--password", "-P", default=None, help="Contraseña de PostgreSQL")
    parser.add_argument("--dbname", "-d", default=None, help="Nombre de base de datos (default: recursos_hidricos)")
    parser.add_argument("--sqlite-path", "-s", default=DEFAULT_SQLITE_PATH, help="Ruta al archivo SQLite .db")
    parser.add_argument("--drop-existing", action="store_true", help="Elimina las tablas existentes en Postgres antes de importar")
    parser.add_argument("--interactive", "-i", action="store_true", help="Forzar modo interactivo para ingresar credenciales")

    args = parser.parse_args()

    # Si se pide modo interactivo o si no se proveyó URL ni host/user ni canal automatizado
    tiene_args = bool(args.postgres_url or args.host or args.user or args.dbname)
    es_tty = sys.stdin.isatty()

    if args.interactive or (not tiene_args and es_tty):
        inter_cfg = prompt_interactive_config()
        migrar_sqlite_a_postgres(
            sqlite_path=args.sqlite_path,
            postgres_url=inter_cfg.get("postgres_url"),
            host=inter_cfg.get("host", "localhost"),
            port=inter_cfg.get("port", 5432),
            user=inter_cfg.get("user", "postgres"),
            password=inter_cfg.get("password"),
            dbname=inter_cfg.get("dbname", "recursos_hidricos"),
            drop_existing=inter_cfg.get("drop_existing", False),
            verbose=True
        )
    else:
        migrar_sqlite_a_postgres(
            sqlite_path=args.sqlite_path,
            postgres_url=args.postgres_url,
            host=args.host or "localhost",
            port=args.port,
            user=args.user or "postgres",
            password=args.password,
            dbname=args.dbname or "recursos_hidricos",
            drop_existing=args.drop_existing,
            verbose=True
        )


if __name__ == "__main__":
    main()

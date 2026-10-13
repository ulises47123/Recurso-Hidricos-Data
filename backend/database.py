import sqlite3
import os
import re
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recursos_hidricos.db")

class PostgresCursorWrapper:
    """Adaptador de cursor para compatibilidad entre PostgreSQL (psycopg2) y SQLite."""
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self._lastrowid = None

    @property
    def lastrowid(self):
        return self._lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def description(self):
        return self._cursor.description

    def _adapt_query(self, sql: str) -> str:
        s = sql.strip()
        # Adaptar PRAGMA de SQLite
        if s.upper().startswith("PRAGMA"):
            m = re.match(r"PRAGMA\s+table_info\((\w+)\)", s, re.IGNORECASE)
            if m:
                tbl = m.group(1).lower()
                return (
                    f"SELECT ordinal_position - 1 AS cid, column_name AS name, data_type AS type, "
                    f"0 AS notnull, NULL AS dflt_value, 0 AS pk "
                    f"FROM information_schema.columns WHERE table_name = '{tbl}'"
                )
            return "SELECT 1"

        # Adaptar tipos y sintaxis específicas de SQLite a PostgreSQL
        s = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "SERIAL PRIMARY KEY", s, flags=re.IGNORECASE)
        s = re.sub(
            r"INSERT\s+OR\s+REPLACE\s+INTO\s+configuracion\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
            r"INSERT INTO configuracion (\1) VALUES (\2) ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor",
            s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"INSERT\s+OR\s+IGNORE\s+INTO\s+feriados\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
            r"INSERT INTO feriados (\1) VALUES (\2) ON CONFLICT (fecha) DO NOTHING",
            s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)",
            r"INSERT INTO \1 (\2) VALUES (\3) ON CONFLICT DO NOTHING",
            s, flags=re.IGNORECASE
        )
        s = re.sub(r"TEXT\s+DEFAULT\s+CURRENT_TIMESTAMP", "TEXT DEFAULT (CURRENT_TIMESTAMP::text)", s, flags=re.IGNORECASE)

        # Reemplazar '?' por '%s' fuera de comillas literales
        parts = []
        in_quote = False
        quote_char = ""
        i = 0
        while i < len(s):
            c = s[i]
            if in_quote:
                parts.append(c)
                if c == quote_char:
                    if i + 1 < len(s) and s[i+1] == quote_char:
                        parts.append(s[i+1])
                        i += 1
                    else:
                        in_quote = False
            else:
                if c in ("'", '"'):
                    in_quote = True
                    quote_char = c
                    parts.append(c)
                elif c == "?":
                    parts.append("%s")
                else:
                    parts.append(c)
            i += 1
        return "".join(parts)

    def execute(self, sql, params=None):
        adapted_sql = self._adapt_query(sql)
        is_insert = adapted_sql.strip().upper().startswith("INSERT INTO")
        has_returning = "RETURNING" in adapted_sql.upper()

        if is_insert and not has_returning:
            sql_returning = f"{adapted_sql.rstrip(';')} RETURNING id;"
            try:
                self._cursor.execute("SAVEPOINT sp_insert")
                if params is not None:
                    self._cursor.execute(sql_returning, params)
                else:
                    self._cursor.execute(sql_returning)
                row = self._cursor.fetchone()
                if row:
                    self._lastrowid = row[0]
                self._cursor.execute("RELEASE SAVEPOINT sp_insert")
                return self
            except Exception:
                try:
                    self._cursor.execute("ROLLBACK TO SAVEPOINT sp_insert")
                    self._cursor.execute("RELEASE SAVEPOINT sp_insert")
                except Exception:
                    pass

        if params is not None:
            self._cursor.execute(adapted_sql, params)
        else:
            self._cursor.execute(adapted_sql)
        return self

    def executemany(self, sql, params_list):
        adapted_sql = self._adapt_query(sql)
        self._cursor.executemany(adapted_sql, params_list)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def close(self):
        self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class PostgresConnectionWrapper:
    """Wrapper de conexión PostgreSQL que replica la API de sqlite3.Connection."""
    def __init__(self, pg_conn):
        self._conn = pg_conn

    def cursor(self):
        return PostgresCursorWrapper(self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor))

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def execute(self, sql, params=None):
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executemany(self, sql, params_list):
        cur = self.cursor()
        cur.executemany(sql, params_list)
        return cur

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

def get_db_connection():
    """
    Obtiene la conexión a la base de datos.
    Soporta PostgreSQL a través de DATABASE_URL (ej. postgresql://user:pass@localhost:5432/recursos_hidricos)
    con fallback automático a SQLite si no está configurada o si falla la conexión.
    """
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url and PSYCOPG2_AVAILABLE:
        try:
            if db_url.startswith("postgres://"):
                db_url = "postgresql://" + db_url[len("postgres://"):]
            pg_conn = psycopg2.connect(db_url)
            return PostgresConnectionWrapper(pg_conn)
        except Exception as e:
            print(f"[DATABASE] Advertencia: No se pudo conectar a PostgreSQL ({e}). Usando fallback automático a SQLite.")

    conn = sqlite3.connect(DB_PATH, timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de Áreas / Estructura Organizacional
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS areas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        codigo TEXT UNIQUE,
        nivel INTEGER DEFAULT 1,
        parent_id INTEGER,
        responsable TEXT,
        descripcion TEXT,
        orden INTEGER DEFAULT 0,
        FOREIGN KEY (parent_id) REFERENCES areas(id) ON DELETE SET NULL
    )
    """)

    # Tabla de Personal
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS personal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        situacion_revista TEXT NOT NULL, -- 'Planta Permanente', 'Contratado Ley', 'Locación de Servicios', 'Gabinete'
        cargo TEXT,
        funcion TEXT,
        area_id INTEGER,
        estado TEXT DEFAULT 'Activo', -- 'Activo', 'Licencia', 'Baja Transitoria'
        deleted_at TEXT DEFAULT NULL, -- Soft delete
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
    )
    """)

    # Tabla de Licencias y Certificados Médicos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS licencias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        tipo_licencia TEXT NOT NULL, -- 'Médica Corto Tratamiento', 'Médica Largo Tratamiento', 'Maternidad/Paternidad', 'Anual Ordinaria', 'Examen', 'Razones Particulares'
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        dias_totales INTEGER NOT NULL,
        diagnostico TEXT,
        certificado_numero TEXT,
        medico_nombre TEXT,
        medico_matricula TEXT,
        estado_justificacion TEXT DEFAULT 'Pendiente', -- 'Justificada', 'Pendiente', 'Rechazada', 'Observada'
        observaciones TEXT,
        deleted_at TEXT DEFAULT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Contratos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contratos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        tipo_contrato TEXT NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT,
        monto_honorarios REAL DEFAULT 0.0,
        resolucion_numero TEXT,
        estado TEXT DEFAULT 'Vigente', -- 'Vigente', 'Renovado', 'Finalizado', 'Rescindido'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Familiares y Beneficiarios (Requerimiento B2)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS familiares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        apellido TEXT NOT NULL,
        dni TEXT,
        parentesco TEXT NOT NULL, -- 'Hijo/a', 'Cónyuge', 'Concubino/a', 'Padre/Madre', 'Otro'
        fecha_nacimiento TEXT,
        es_beneficiario INTEGER DEFAULT 1,
        observaciones TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Historial de Cargos y Funciones (Requerimiento F6 - Cambios de función)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_funciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        cargo TEXT NOT NULL,
        funcion TEXT,
        area_id INTEGER,
        fecha_desde TEXT NOT NULL,
        fecha_hasta TEXT, -- NULL si es el cargo/función actual
        motivo_cambio TEXT,
        instrumento_legal TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE,
        FOREIGN KEY (area_id) REFERENCES areas(id) ON DELETE SET NULL
    )
    """)

    # Tabla de Documentos de Legajo Digital (Requerimiento B3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documentos_legajo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        tipo_documento TEXT NOT NULL,
        titulo TEXT NOT NULL,
        nombre_archivo TEXT NOT NULL,
        ruta_archivo TEXT NOT NULL,
        fecha_subida TEXT DEFAULT CURRENT_TIMESTAMP,
        observaciones TEXT,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Usuarios y Permisos Granulares
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'admin', -- 'admin', 'personalizado'
        permisos TEXT, -- JSON con lista de permisos otorgados
        activo INTEGER DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Tabla de Sesiones de Usuario (Tokens de Acceso)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        token TEXT UNIQUE NOT NULL,
        expiracion TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
    )
    """)

    # Migración de columna permisos si no existe
    cursor.execute("PRAGMA table_info(usuarios)")
    columnas_usuarios = [col[1] for col in cursor.fetchall()]
    if "permisos" not in columnas_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN permisos TEXT")

    # Precargar usuario admin por defecto si no existe o asegurar contraseña admin123
    cursor.execute("SELECT id, password_hash FROM usuarios WHERE username = 'admin'")
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute("""
            INSERT INTO usuarios (username, password_hash, nombre_completo, rol, permisos, activo)
            VALUES ('admin', 'admin123', 'Administrador Principal', 'admin', '["*"]', 1)
        """)
    else:
        # Asegurar que el usuario por defecto 'admin' tenga 'admin123' si mantiene 'admin' o está vacío
        if admin_row[1] in ('admin', '', None):
            cursor.execute("UPDATE usuarios SET password_hash = 'admin123' WHERE username = 'admin'")

    # Tablas para Catálogos Dinámicos Oficiales DPRH (Principio de cero información estática)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS situaciones_revista_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        activo INTEGER DEFAULT 1,
        orden INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lugares_trabajo_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        activo INTEGER DEFAULT 1,
        orden INTEGER DEFAULT 0
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS funciones_catalogo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE NOT NULL,
        descripcion TEXT,
        activo INTEGER DEFAULT 1,
        orden INTEGER DEFAULT 0
    )
    """)

    # Precargar Situaciones de Revista oficiales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM situaciones_revista_catalogo")
    if cursor.fetchone()[0] == 0:
        default_situaciones = [
            ("Planta Permanente", "Personal permanente bajo régimen de estabilidad", 1, 1),
            ("Contrato de Locación de Servicios", "Contrato de servicios técnicos o profesionales", 1, 2),
            ("Decreto", "Designación por Decreto provincial", 1, 3),
            ("Contrato de Obra", "Contrato específico para obras hídricas", 1, 4),
            ("Adscrito", "Personal en comisión de servicios o adscripción", 1, 5),
            ("Gabinete", "Personal asignado a funciones de gabinete", 1, 6)
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO situaciones_revista_catalogo (nombre, descripcion, activo, orden) VALUES (?, ?, ?, ?)",
            default_situaciones
        )

    # Precargar Lugares de Trabajo oficiales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM lugares_trabajo_catalogo")
    if cursor.fetchone()[0] == 0:
        default_lugares = [
            ("Oficina Central", "Sede central de la DPRH", 1, 1),
            ("Lote", "Campamento o lote operativo", 1, 2),
            ("COREBE", "Comisión Regional del Río Bermejo", 1, 3),
            ("Maimará", "Delegación Quebrada Maimará", 1, 4),
            ("Unidad Operativa El Carmen", "Base operativa El Carmen", 1, 5),
            ("Catamontaña", "Puesto operativo Catamontaña", 1, 6),
            ("Las Maderas", "Dique Las Maderas", 1, 7),
            ("La Ciénaga", "Dique La Ciénaga", 1, 8),
            ("Derivador El Tipal", "Estación derivadora El Tipal", 1, 9),
            ("Los Alisos", "Dique Los Alisos", 1, 10),
            ("Derivador Los Molinos", "Estación derivadora Los Molinos", 1, 11),
            ("Otro", "Otro destino o comisión", 1, 12)
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO lugares_trabajo_catalogo (nombre, descripcion, activo, orden) VALUES (?, ?, ?, ?)",
            default_lugares
        )

    # Precargar Funciones oficiales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM funciones_catalogo")
    if cursor.fetchone()[0] == 0:
        default_funciones = [
            ("Jefe", "Jefatura de departamento, división o sector", 1, 1),
            ("Electricista", "Mantenimiento eléctrico de infraestructura", 1, 2),
            ("Compartidor de Riego", "Operación de compuertas y sistemas de riego", 1, 3),
            ("Soldador", "Mantenimiento metalúrgico y soldadura", 1, 4),
            ("Limpieza", "Servicio general de higiene", 1, 5),
            ("Maestranza", "Mantenimiento edilicio y servicios", 1, 6),
            ("Mecánico", "Mantenimiento mecánico de bombas y maquinaria", 1, 7),
            ("Maquinista", "Operador de maquinaria vial y pesada", 1, 8),
            ("Encargado de Combustible", "Control y abastecimiento de combustible", 1, 9),
            ("Administrativo", "Gestión administrativa y despacho", 1, 10),
            ("Inspector", "Inspección técnica de obras y riego", 1, 11),
            ("Observador Meteorológico", "Registro de variables hidrometeorológicas", 1, 12),
            ("Cajero", "Cobranza de cánones y aranceles", 1, 13),
            ("Electromecánico", "Sistemas electromecánicos de bombeo", 1, 14),
            ("Fotógrafo", "Registro gráfico y documentación", 1, 15),
            ("Guardadique", "Custodia y monitoreo de presas y diques", 1, 16),
            ("Telefonista", "Atención telefónica y comunicaciones", 1, 17),
            ("Profesional", "Ingeniería, agrimensura, legal o contable", 1, 18)
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO funciones_catalogo (nombre, descripcion, activo, orden) VALUES (?, ?, ?, ?)",
            default_funciones
        )

    # Tabla de Adicionales de Personal (Requerimiento Geovana - DPRH)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS adicionales_personal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Historial de Categorías (Requerimiento Geovana - DPRH)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        categoria TEXT NOT NULL,
        fecha_cambio TEXT NOT NULL,
        resolucion_numero TEXT,
        observaciones TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Beneficios Artículo 79 - Cumpleaños (Requerimiento Geovana - DPRH)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS beneficios_articulo_79 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        anio_periodo INTEGER NOT NULL,
        edad_cumplida INTEGER,
        fecha_cumpleanios TEXT,
        fecha_cobro TEXT NOT NULL,
        monto_asignado REAL DEFAULT 0.0,
        estado_pago TEXT DEFAULT 'Cobrado',
        resolucion_numero TEXT,
        observaciones TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Suspensiones de Licencias (Requerimiento Geovana DPRH)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suspensiones_licencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        licencia_id INTEGER NOT NULL,
        personal_id INTEGER NOT NULL,
        fecha_suspension TEXT NOT NULL,
        dias_tomados_hasta_suspension INTEGER NOT NULL,
        dias_pendientes INTEGER NOT NULL,
        motivo_suspension TEXT,
        autorizado_por TEXT,
        fecha_alta TEXT,
        observaciones TEXT,
        estado TEXT DEFAULT 'Pendiente',  -- 'Pendiente', 'Retomada', 'Vencida'
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (licencia_id) REFERENCES licencias(id) ON DELETE CASCADE,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Migración de columnas adicionales en tabla licencias si no existen
    cursor.execute("PRAGMA table_info(licencias)")
    columnas_licencias = [col[1] for col in cursor.fetchall()]
    if "auditado_salud_provincial" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN auditado_salud_provincial INTEGER DEFAULT 0")
    if "observacion_auditoria" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN observacion_auditoria TEXT DEFAULT ''")
    if "periodo_anual" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN periodo_anual INTEGER")
    if "familiar_nombre" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN familiar_nombre TEXT")
    if "familiar_parentesco" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN familiar_parentesco TEXT")
    if "km_distancia" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN km_distancia INTEGER")
    if "dias_adicionales_viaje" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN dias_adicionales_viaje INTEGER DEFAULT 0")
    if "constancia_adjunto" not in columnas_licencias:
        cursor.execute("ALTER TABLE licencias ADD COLUMN constancia_adjunto TEXT")

    # Migración de columnas extendidas en tabla personal para la Ficha Personal oficial DPRH
    cursor.execute("PRAGMA table_info(personal)")
    columnas_personal = [col[1] for col in cursor.fetchall()]
    nuevas_columnas_personal = {
        "cuil": "TEXT",
        "fecha_ingreso_admin_pub": "TEXT",
        "fecha_ingreso_recursos_hidricos_obra": "TEXT",
        "fecha_ingreso_recursos_hidricos_planta": "TEXT",
        "asistencia": "TEXT DEFAULT 'Reloj'",
        "categoria_actual": "TEXT",
        "categoria_fecha_alta": "TEXT",
        "situacion_revista_obs": "TEXT",
        "lugar_trabajo": "TEXT DEFAULT 'Oficina Central'",
        "lugar_trabajo_otro": "TEXT",
        "sentencia": "TEXT",
        "actividad": "TEXT",
        "profesional_titulo": "TEXT",
        "direccion_organismo": "TEXT DEFAULT 'Dirección Provincial de Recursos Hídricos'",
        "area_trabajo": "TEXT",
        "departamento_trabajo": "TEXT",
        "division_trabajo": "TEXT",
        "sector_trabajo": "TEXT",
        "horario": "TEXT DEFAULT '07:00 a 13:00'",
        "gremio": "TEXT"
    }
    for col_nombre, col_tipo in nuevas_columnas_personal.items():
        if col_nombre not in columnas_personal:
            cursor.execute(f"ALTER TABLE personal ADD COLUMN {col_nombre} {col_tipo}")


    # Tabla de Auditoría (Logs de operaciones)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auditoria_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT DEFAULT 'admin',
        accion TEXT NOT NULL, -- 'CREAR', 'EDITAR', 'ELIMINAR_PAPELERA', 'RESTAURAR', 'ELIMINAR_DEFINITIVO', 'IMPORTAR_EXCEL', 'EXPORTAR_EXCEL'
        tabla_afectada TEXT NOT NULL,
        registro_id INTEGER,
        detalles TEXT,
        ip TEXT DEFAULT '127.0.0.1'
    )
    """)

    # Tabla de Configuración
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (
        clave TEXT PRIMARY KEY,
        valor TEXT,
        descripcion TEXT
    )
    """)

    # Tabla de Saldo de Compensatorios por Agente
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compensatorios_saldo (
        personal_id INTEGER PRIMARY KEY,
        dias_disponibles REAL DEFAULT 0.0,
        fecha_ultima_carga TEXT,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Cargas de Horas/Días Compensatorios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compensatorios_cargas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        dias REAL NOT NULL,
        fecha_carga TEXT NOT NULL,
        motivo TEXT,
        acta_numero TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Solicitudes/Descuento de Compensatorios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compensatorios_solicitudes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personal_id INTEGER NOT NULL,
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        dias_descontados REAL NOT NULL,
        acta_numero TEXT,
        estado TEXT DEFAULT 'Pendiente', -- 'Aprobada', 'Pendiente', 'Observada', 'Rechazada'
        observaciones TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (personal_id) REFERENCES personal(id) ON DELETE CASCADE
    )
    """)

    # Tabla de Feriados para cálculo de días hábiles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feriados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT UNIQUE NOT NULL,
        descripcion TEXT NOT NULL
    )
    """)

    # Precargar feriados nacionales y provinciales oficiales si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM feriados")
    if cursor.fetchone()[0] == 0:
        feriados_oficiales = [
            # 2024
            ("2024-01-01", "Año Nuevo"),
            ("2024-02-12", "Carnaval"),
            ("2024-02-13", "Carnaval"),
            ("2024-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia"),
            ("2024-03-29", "Viernes Santo"),
            ("2024-04-01", "Feriado Puente Turístico"),
            ("2024-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas"),
            ("2024-05-01", "Día del Trabajador"),
            ("2024-05-25", "Día de la Revolución de Mayo"),
            ("2024-06-17", "Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes"),
            ("2024-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano"),
            ("2024-06-21", "Feriado Puente Turístico"),
            ("2024-07-09", "Día de la Independencia"),
            ("2024-08-17", "Paso a la Inmortalidad del Gral. José de San Martín"),
            ("2024-08-23", "Éxodo Jujeño"),
            ("2024-10-11", "Feriado Puente Turístico"),
            ("2024-10-12", "Día del Respeto a la Diversidad Cultural"),
            ("2024-11-18", "Día de la Soberanía Nacional"),
            ("2024-12-08", "Inmaculada Concepción de María"),
            ("2024-12-25", "Navidad"),
            # 2025
            ("2025-01-01", "Año Nuevo"),
            ("2025-03-03", "Carnaval"),
            ("2025-03-04", "Carnaval"),
            ("2025-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia"),
            ("2025-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas"),
            ("2025-04-18", "Viernes Santo"),
            ("2025-05-01", "Día del Trabajador"),
            ("2025-05-02", "Feriado Puente Turístico"),
            ("2025-05-25", "Día de la Revolución de Mayo"),
            ("2025-06-16", "Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes"),
            ("2025-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano"),
            ("2025-07-09", "Día de la Independencia"),
            ("2025-08-15", "Feriado Puente Turístico"),
            ("2025-08-17", "Paso a la Inmortalidad del Gral. José de San Martín"),
            ("2025-08-23", "Éxodo Jujeño"),
            ("2025-10-12", "Día del Respeto a la Diversidad Cultural"),
            ("2025-10-13", "Día del Respeto a la Diversidad Cultural (Trasladado)"),
            ("2025-11-20", "Día de la Soberanía Nacional"),
            ("2025-11-24", "Día de la Soberanía Nacional (Trasladado)"),
            ("2025-12-08", "Inmaculada Concepción de María"),
            ("2025-12-25", "Navidad"),
            # 2026
            ("2026-01-01", "Año Nuevo"),
            ("2026-02-16", "Carnaval"),
            ("2026-02-17", "Carnaval"),
            ("2026-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia"),
            ("2026-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas"),
            ("2026-04-03", "Viernes Santo"),
            ("2026-05-01", "Día del Trabajador"),
            ("2026-05-25", "Día de la Revolución de Mayo"),
            ("2026-06-15", "Paso a la Inmortalidad del Gral. Don Martín Miguel de Güemes (Trasladado)"),
            ("2026-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano"),
            ("2026-07-09", "Día de la Independencia"),
            ("2026-08-17", "Paso a la Inmortalidad del Gral. José de San Martín"),
            ("2026-08-23", "Éxodo Jujeño"),
            ("2026-10-12", "Día del Respeto a la Diversidad Cultural"),
            ("2026-11-20", "Día de la Soberanía Nacional"),
            ("2026-11-23", "Día de la Soberanía Nacional (Trasladado)"),
            ("2026-12-08", "Inmaculada Concepción de María"),
            ("2026-12-25", "Navidad"),
            # 2027
            ("2027-01-01", "Año Nuevo"),
            ("2027-02-08", "Carnaval"),
            ("2027-02-09", "Carnaval"),
            ("2027-03-24", "Día Nacional de la Memoria por la Verdad y la Justicia"),
            ("2027-03-26", "Viernes Santo"),
            ("2027-04-02", "Día del Veterano y de los Caídos en la Guerra de Malvinas"),
            ("2027-05-01", "Día del Trabajador"),
            ("2027-05-25", "Día de la Revolución de Mayo"),
            ("2027-06-20", "Paso a la Inmortalidad del Gral. Manuel Belgrano"),
            ("2027-07-09", "Día de la Independencia"),
            ("2027-08-16", "Paso a la Inmortalidad del Gral. José de San Martín"),
            ("2027-08-23", "Éxodo Jujeño"),
            ("2027-10-11", "Día del Respeto a la Diversidad Cultural (Trasladado)"),
            ("2027-10-12", "Día del Respeto a la Diversidad Cultural"),
            ("2027-11-22", "Día de la Soberanía Nacional"),
            ("2027-12-08", "Inmaculada Concepción de María"),
            ("2027-12-25", "Navidad")
        ]
        cursor.executemany("INSERT OR IGNORE INTO feriados (fecha, descripcion) VALUES (?, ?)", feriados_oficiales)

    # Índices de Alto Rendimiento para escalar a cientos de miles de registros
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_dni ON personal(dni)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_legajo ON personal(legajo)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_apellido_nombre ON personal(apellido, nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_area_id ON personal(area_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_estado ON personal(estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_deleted ON personal(deleted_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licencias_personal ON licencias(personal_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_licencias_fechas ON licencias(fecha_inicio, fecha_fin)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_auditoria_usuario ON auditoria_logs(usuario)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_revista_nombre ON situaciones_revista_catalogo(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_lugares_nombre ON lugares_trabajo_catalogo(nombre)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cat_funciones_nombre ON funciones_catalogo(nombre)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")


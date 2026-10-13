from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class AreaModel(BaseModel):
    id: Optional[int] = None
    nombre: str
    codigo: Optional[str] = None
    nivel: int = 1
    parent_id: Optional[int] = None
    responsable: Optional[str] = None
    descripcion: Optional[str] = None
    orden: int = 0

class PersonalBase(BaseModel):
    dni: str
    cuil: Optional[str] = None
    legajo: Optional[str] = None
    nombre: str
    apellido: str
    email: Optional[str] = None
    telefono: Optional[str] = None
    fecha_nacimiento: Optional[str] = None
    genero: Optional[str] = "Otro"
    direccion: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    fecha_ingreso_admin_pub: Optional[str] = None
    fecha_ingreso_recursos_hidricos_obra: Optional[str] = None
    fecha_ingreso_recursos_hidricos_planta: Optional[str] = None
    asistencia: Optional[str] = "Reloj"
    categoria_actual: Optional[str] = None
    categoria_fecha_alta: Optional[str] = None
    situacion_revista: str = "Planta Permanente"
    situacion_revista_obs: Optional[str] = None
    lugar_trabajo: Optional[str] = "Oficina Central"
    lugar_trabajo_otro: Optional[str] = None
    sentencia: Optional[str] = None
    actividad: Optional[str] = None
    cargo: Optional[str] = None
    funcion: Optional[str] = None
    profesional_titulo: Optional[str] = None
    direccion_organismo: Optional[str] = "Dirección Provincial de Recursos Hídricos"
    area_trabajo: Optional[str] = None
    departamento_trabajo: Optional[str] = None
    division_trabajo: Optional[str] = None
    sector_trabajo: Optional[str] = None
    area_id: Optional[int] = None
    horario: Optional[str] = "07:00 a 13:00"
    gremio: Optional[str] = None
    estado: str = "Activo"

class PersonalCreate(PersonalBase):
    pass

class PersonalUpdate(PersonalBase):
    pass

class AdicionalPersonalCreate(BaseModel):
    personal_id: int
    tipo_adicional: str
    monto_o_porcentaje: Optional[str] = None
    fecha_alta: str
    fecha_baja: Optional[str] = None
    resolucion_numero: Optional[str] = None
    motivo_cambio: Optional[str] = None
    observaciones: Optional[str] = None

class HistorialCategoriaCreate(BaseModel):
    personal_id: int
    categoria: str
    fecha_cambio: str
    resolucion_numero: Optional[str] = None
    observaciones: Optional[str] = None

class BeneficioArticulo79Create(BaseModel):
    personal_id: int
    anio_periodo: int
    edad_cumplida: Optional[int] = None
    fecha_cumpleanios: Optional[str] = None
    fecha_cobro: str
    monto_asignado: float = 0.0
    estado_pago: str = "Cobrado"
    resolucion_numero: Optional[str] = None
    observaciones: Optional[str] = None


class LicenciaBase(BaseModel):
    personal_id: int
    tipo_licencia: str
    fecha_inicio: str
    fecha_fin: str
    dias_totales: int
    diagnostico: Optional[str] = None
    certificado_numero: Optional[str] = None
    medico_nombre: Optional[str] = None
    medico_matricula: Optional[str] = None
    estado_justificacion: str = "Pendiente"
    auditado_salud_provincial: Optional[int] = 0
    observacion_auditoria: Optional[str] = ""
    observaciones: Optional[str] = None
    # Campos extendidos DPRH
    periodo_anual: Optional[int] = None
    familiar_nombre: Optional[str] = None
    familiar_parentesco: Optional[str] = None
    km_distancia: Optional[int] = None
    dias_adicionales_viaje: Optional[int] = 0

class LicenciaCreate(LicenciaBase):
    pass

class LicenciaUpdate(LicenciaBase):
    pass

class SuspensionLicenciaCreate(BaseModel):
    licencia_id: int
    personal_id: int
    fecha_suspension: str
    dias_tomados_hasta_suspension: int
    dias_pendientes: int
    motivo_suspension: Optional[str] = None
    autorizado_por: Optional[str] = None
    fecha_alta: Optional[str] = None
    observaciones: Optional[str] = None

class ContratoBase(BaseModel):
    personal_id: int
    tipo_contrato: str
    fecha_inicio: str
    fecha_fin: Optional[str] = None
    monto_honorarios: float = 0.0
    resolucion_numero: Optional[str] = None
    estado: str = "Vigente"

class FamiliarCreate(BaseModel):
    personal_id: int
    nombre: str
    apellido: str
    dni: Optional[str] = None
    parentesco: str # 'Hijo/a', 'Cónyuge', 'Concubino/a', 'Padre/Madre', 'Otro'
    fecha_nacimiento: Optional[str] = None
    es_beneficiario: int = 1
    observaciones: Optional[str] = None

class HistorialFuncionCreate(BaseModel):
    personal_id: int
    cargo: str
    funcion: Optional[str] = None
    area_id: Optional[int] = None
    fecha_desde: str
    fecha_hasta: Optional[str] = None
    motivo_cambio: Optional[str] = None
    instrumento_legal: Optional[str] = None

class UsuarioLogin(BaseModel):
    username: str
    password: str

class UsuarioCreate(BaseModel):
    username: str
    password: str
    nombre_completo: str
    rol: str = "personalizado" # 'admin', 'personalizado'
    permisos: Optional[List[str]] = []

class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    nombre_completo: Optional[str] = None
    password: Optional[str] = None
    rol: Optional[str] = None
    permisos: Optional[List[str]] = None
    activo: Optional[int] = None

class CatalogoItemCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    activo: Optional[int] = 1
    orden: Optional[int] = 0

class CatalogoItemUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[int] = None
    orden: Optional[int] = None

class UsuarioResponse(BaseModel):
    id: int
    username: str
    nombre_completo: str
    rol: str
    permisos: Optional[List[str]] = []
    activo: int

class ConfigItem(BaseModel):
    clave: str
    valor: str
    descripcion: Optional[str] = None

class CompensatorioCargaCreate(BaseModel):
    personal_id: int
    dias: float
    fecha_carga: str
    motivo: Optional[str] = None
    acta_numero: Optional[str] = None

class CompensatorioSolicitudCreate(BaseModel):
    personal_id: int
    fecha_inicio: str
    fecha_fin: str
    acta_numero: Optional[str] = None
    observaciones: Optional[str] = None

class CompensatorioEstadoUpdate(BaseModel):
    estado: str # 'Aprobada', 'Pendiente', 'Observada', 'Rechazada'
    observaciones: Optional[str] = None

class FeriadoCreate(BaseModel):
    fecha: str
    descripcion: str



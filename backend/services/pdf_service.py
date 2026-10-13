"""
Servicio de Generación de Documentos PDF Oficiales - DPRH Jujuy
Utiliza xhtml2pdf (100% Python nativo, compatible con Windows sin dependencias externas)
"""

import io
from datetime import datetime
from xhtml2pdf import pisa
from backend.database import get_db_connection
from backend.services import personal_service, licencias_service

import os
import base64

def _get_logo_base64() -> str:
    """Obtiene el logo en formato base64 data URI para embeber en los documentos PDF."""
    try:
        logo_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "img", "logo.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
    except Exception:
        pass
    return ""

def html_to_pdf_bytes(html_content: str) -> bytes:
    """Convierte una cadena de HTML con estilos CSS a un buffer de bytes PDF."""
    result = io.BytesIO()
    pisa_status = pisa.pisaDocument(
        io.BytesIO(html_content.encode("utf-8")),
        result,
        encoding="utf-8"
    )
    if pisa_status.err:
        raise RuntimeError("Error al renderizar el documento PDF con xhtml2pdf")
    return result.getvalue()


def generar_pdf_constancia_licencia(licencia_id: int) -> bytes:
    """
    Genera la Constancia Oficial de Concesión de Licencia en PDF
    con membrete formal de la Dirección Provincial de Recursos Hídricos y firmas en 1 sola página.
    """
    licencia = licencias_service.obtener_licencia_por_id(licencia_id)
    if not licencia:
        raise ValueError("Licencia no encontrada")

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    
    logo_b64 = _get_logo_base64()
    logo_img_tag = f'<img src="{logo_b64}" style="height: 42px; width: auto; margin-right: 10px;">' if logo_b64 else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 1.2cm 1.5cm;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 10pt;
                color: #1e293b;
                line-height: 1.35;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 6px;
                margin-bottom: 12px;
            }}
            .header-title {{
                font-size: 13pt;
                font-weight: bold;
                color: #0f2444;
            }}
            .header-subtitle {{
                font-size: 10.5pt;
                font-weight: bold;
                color: #2b6cb0;
            }}
            .header-dept {{
                font-size: 8.5pt;
                color: #64748b;
            }}
            .doc-title {{
                text-align: center;
                font-size: 12pt;
                font-weight: bold;
                text-decoration: underline;
                color: #1a365d;
                margin-top: 8px;
                margin-bottom: 12px;
            }}
            .intro-text {{
                text-align: justify;
                margin-bottom: 10px;
                font-size: 9.5pt;
            }}
            .section-header {{
                font-size: 10pt;
                font-weight: bold;
                color: #1a365d;
                background-color: #f1f5f9;
                padding: 4px 8px;
                border-left: 4px solid #2b6cb0;
                margin-top: 10px;
                margin-bottom: 6px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 8px;
            }}
            .data-table td {{
                padding: 4px 6px;
                font-size: 9.5pt;
                border-bottom: 1px solid #e2e8f0;
            }}
            .data-label {{
                font-weight: bold;
                color: #475569;
                width: 38%;
            }}
            .box-licencia {{
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 6px 8px;
                margin-bottom: 10px;
            }}
            .signatures-table {{
                width: 100%;
                margin-top: 35px;
            }}
            .signature-cell {{
                width: 25%;
                text-align: center;
                vertical-align: top;
                padding: 0 4px;
            }}
            .signature-line {{
                border-top: 1px solid #000;
                margin-bottom: 4px;
            }}
            .footer-note {{
                font-size: 8.5pt;
                color: #64748b;
                text-align: justify;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                {f'<td style="width: 48px; vertical-align: middle;">{logo_img_tag}</td>' if logo_img_tag else ''}
                <td style="vertical-align: middle;">
                    <div class="header-title">GOBIERNO DE LA PROVINCIA DE JUJUY</div>
                    <div class="header-subtitle">Dirección Provincial de Recursos Hídricos</div>
                    <div class="header-dept">Departamento de Recursos Humanos — Legajo de Personal</div>
                </td>
                <td style="text-align: right; vertical-align: top;">
                    <div style="font-size: 8.5pt; color: #64748b;">San Salvador de Jujuy<br>Fecha: <strong>{fecha_hoy}</strong></div>
                </td>
            </tr>
        </table>

        <div class="doc-title">CONSTANCIA OFICIAL DE CONCESIÓN DE LICENCIA</div>

        <p class="intro-text">
            Por la presente, la <strong>Dirección Provincial de Recursos Hídricos</strong> certifica que al agente cuyos datos se consignan a continuación, se le ha acordado y registrado formalmente en el sistema la siguiente licencia:
        </p>

        <div class="section-header">1. DATOS IDENTIFICATORIOS DEL AGENTE</div>
        <table class="data-table">
            <tr>
                <td class="data-label">Apellido y Nombre:</td>
                <td><strong>{licencia.get('personal_apellido', '')}, {licencia.get('personal_nombre', '')}</strong></td>
            </tr>
            <tr>
                <td class="data-label">Documento Nacional de Identidad:</td>
                <td>{licencia.get('personal_dni', '-')}</td>
            </tr>
            <tr>
                <td class="data-label">Situación de Revista:</td>
                <td>{licencia.get('situacion_revista', '-')}</td>
            </tr>
            <tr>
                <td class="data-label">Dependencia / Área Asignada:</td>
                <td>{licencia.get('area_nombre', 'Recursos Hídricos')}</td>
            </tr>
        </table>

        <div class="section-header">2. DETALLE DE LA LICENCIA AUTORIZADA</div>
        <div class="box-licencia">
            <table class="data-table" style="margin-bottom: 0;">
                <tr>
                    <td class="data-label">Régimen / Tipo de Licencia:</td>
                    <td><strong>{licencia.get('tipo_licencia', '-')}</strong></td>
                </tr>
                <tr>
                    <td class="data-label">Período de Usufructo:</td>
                    <td>Desde el <strong>{licencia.get('fecha_inicio', '-')}</strong> hasta el <strong>{licencia.get('fecha_fin', '-')}</strong></td>
                </tr>
                <tr>
                    <td class="data-label">Cantidad Total de Días:</td>
                    <td><strong>{licencia.get('dias_totales', 1)} día(s)</strong></td>
                </tr>
                <tr>
                    <td class="data-label">Período Anual Imputado:</td>
                    <td>{licencia.get('periodo_anual') or datetime.now().year}</td>
                </tr>
                <tr>
                    <td class="data-label">Estado de Justificación:</td>
                    <td><strong>{licencia.get('estado_justificacion', 'Pendiente')}</strong></td>
                </tr>
                <tr>
                    <td class="data-label">Número de Resolución:</td>
                    <td><strong>{licencia.get('certificado_numero') or 'Sin número de resolución'}</strong></td>
                </tr>
                {f"<tr><td class='data-label'>Médico / Matrícula:</td><td>{licencia.get('medico_nombre')} ({licencia.get('medico_matricula') or '-'})</td></tr>" if licencia.get('medico_nombre') else ""}
                {f"<tr><td class='data-label'>Diagnóstico / Causa:</td><td>{licencia.get('diagnostico')}</td></tr>" if licencia.get('diagnostico') else ""}
                {f"<tr><td class='data-label'>Observaciones:</td><td>{licencia.get('observaciones')}</td></tr>" if licencia.get('observaciones') else ""}
            </table>
        </div>

        <p class="footer-note">
            La presente constancia tiene validez oficial ante las autoridades provinciales pertinentes y queda asentada en el legajo digital del agente.
        </p>

        <table class="signatures-table" style="width: 100%; margin-top: 50px;">
            <tr>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <strong style="font-size: 8.5pt;">Firma del Agente</strong><br>
                    <span style="font-size: 7.5pt; color: #64748b;">Aclaración / DNI</span>
                </td>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <strong style="font-size: 8.5pt;">Firma Jefe Inmediato</strong><br>
                    <span style="font-size: 7.5pt; color: #64748b;">Sector / Departamento</span>
                </td>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <strong style="font-size: 8.5pt;">Jefatura RRHH</strong><br>
                    <span style="font-size: 7.5pt; color: #64748b;">DPRH Jujuy</span>
                </td>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <strong style="font-size: 8.5pt;">Firma del Director</strong><br>
                    <span style="font-size: 7.5pt; color: #64748b;">Dirección Provincial</span>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_to_pdf_bytes(html)


def generar_pdf_ficha_personal(personal_id: int) -> bytes:
    """
    Genera la Ficha Oficial del Agente en PDF con datos personales,
    antigüedades calculadas, situación de revista, familiares y licencias.
    """
    p = personal_service.obtener_personal_por_id(personal_id)
    if not p:
        raise ValueError("Personal no encontrado")

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    logo_b64 = _get_logo_base64()
    logo_img_tag = f'<img src="{logo_b64}" style="height: 44px; width: auto; margin-right: 10px;">' if logo_b64 else ''

    # Armado de filas de licencias
    licencias_html = ""
    if p.get("historial_licencias"):
        for l in p["historial_licencias"][:10]:
            licencias_html += f"""
            <tr>
                <td>{l.get('tipo_licencia', '-')}</td>
                <td>{l.get('fecha_inicio', '-')} al {l.get('fecha_fin', '-')}</td>
                <td>{l.get('dias_totales', 0)} d</td>
                <td>{l.get('estado_justificacion', '-')}</td>
            </tr>
            """
    else:
        licencias_html = "<tr><td colspan='4' style='text-align:center;'>Sin licencias registradas</td></tr>"

    # Armado de filas de familiares
    familiares_html = ""
    if p.get("familiares"):
        for f in p["familiares"]:
            familiares_html += f"""
            <tr>
                <td>{f.get('apellido', '')}, {f.get('nombre', '')}</td>
                <td>{f.get('parentesco', '-')}</td>
                <td>{f.get('dni', '-')}</td>
            </tr>
            """
    else:
        familiares_html = "<tr><td colspan='3' style='text-align:center;'>Sin familiares a cargo registrados</td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 1.8cm;
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 8pt;
                    color: #666;
                }}
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 10pt;
                color: #1e293b;
                line-height: 1.4;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 8px;
                margin-bottom: 16px;
            }}
            .header-title {{
                font-size: 13pt;
                font-weight: bold;
                color: #0f2444;
            }}
            .header-subtitle {{
                font-size: 10pt;
                font-weight: bold;
                color: #2b6cb0;
            }}
            .doc-title {{
                text-align: center;
                font-size: 12pt;
                font-weight: bold;
                color: #1a365d;
                margin: 10px 0 16px 0;
            }}
            .section-title {{
                font-size: 10pt;
                font-weight: bold;
                color: #1a365d;
                background-color: #f1f5f9;
                padding: 4px 8px;
                border-left: 3px solid #2b6cb0;
                margin-top: 10px;
                margin-bottom: 6px;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 10px;
            }}
            .info-table td {{
                padding: 4px 6px;
                font-size: 9.5pt;
                border-bottom: 1px solid #e2e8f0;
            }}
            .label {{
                font-weight: bold;
                color: #475569;
                width: 25%;
            }}
            .subtable {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 6px;
                margin-bottom: 10px;
            }}
            .subtable th {{
                background-color: #1e3a5f;
                color: #ffffff;
                font-size: 8.5pt;
                font-weight: bold;
                padding: 5px;
                text-align: left;
            }}
            .subtable td {{
                padding: 4px 5px;
                font-size: 8.5pt;
                border-bottom: 1px solid #cbd5e1;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                {f'<td style="width: 55px; vertical-align: middle;">{logo_img_tag}</td>' if logo_img_tag else ''}
                <td style="vertical-align: middle;">
                    <div class="header-title">GOBIERNO DE LA PROVINCIA DE JUJUY</div>
                    <div class="header-subtitle">Dirección Provincial de Recursos Hídricos</div>
                    <div style="font-size: 8pt; color:#64748b;">Legajo Único de Personal — Ficha Individual Oficial</div>
                </td>
                <td style="text-align: right; vertical-align: top;">
                    <div style="font-size: 8.5pt; color: #64748b;">Estado: <strong>{p.get('estado', 'Activo')}</strong><br>Emitido: {fecha_hoy}</div>
                </td>
            </tr>
        </table>

        <div class="doc-title">LEGAJO DE AGENTE: {p.get('apellido', '').upper()}, {p.get('nombre', '').upper()}</div>

        <div class="section-title">1. IDENTIFICACIÓN Y DATOS PERSONALES</div>
        <table class="info-table">
            <tr>
                <td class="label">D.N.I. N°:</td>
                <td>{p.get('dni', '-')}</td>
                <td class="label">CUIL:</td>
                <td>{p.get('cuil') or '-'}</td>
            </tr>
            <tr>
                <td class="label">Legajo N°:</td>
                <td>{p.get('legajo') or 'S/L'}</td>
                <td class="label">Fecha Nacimiento:</td>
                <td>{p.get('fecha_nacimiento') or '-'} {f"({p.get('edad_calculada')} años)" if p.get('edad_calculada') else ""}</td>
            </tr>
            <tr>
                <td class="label">Teléfono:</td>
                <td>{p.get('telefono') or '-'}</td>
                <td class="label">Correo Electrónico:</td>
                <td>{p.get('email') or '-'}</td>
            </tr>
            <tr>
                <td class="label">Domicilio:</td>
                <td colspan="3">{p.get('direccion') or '-'}</td>
            </tr>
        </table>

        <div class="section-title">2. SITUACIÓN DE REVISTA Y ANTIGÜEDADES OFICIALES</div>
        <table class="info-table">
            <tr>
                <td class="label">Situación Revista:</td>
                <td><strong>{p.get('situacion_revista', '-')}</strong></td>
                <td class="label">Área / Sector:</td>
                <td>{p.get('area_nombre') or 'Sin asignar'}</td>
            </tr>
            <tr>
                <td class="label">Cargo Oficial:</td>
                <td>{p.get('cargo') or '-'}</td>
                <td class="label">Función Operativa:</td>
                <td>{p.get('funcion') or '-'}</td>
            </tr>
            <tr>
                <td class="label">Fecha Ingreso:</td>
                <td>{p.get('fecha_ingreso') or '-'}</td>
                <td class="label">Lugar de Trabajo:</td>
                <td>{p.get('lugar_trabajo') or 'Oficina Central'}</td>
            </tr>
            <tr>
                <td class="label">Antigüedad Adm. Pub.:</td>
                <td><strong>{p.get('antiguedad_admin_pub_calc') or '-'}</strong></td>
                <td class="label">Antigüedad Planta:</td>
                <td><strong>{p.get('antiguedad_planta_calc') or '-'}</strong></td>
            </tr>
        </table>

        <div class="section-title">3. FAMILIARES Y BENEFICIARIOS A CARGO</div>
        <table class="subtable">
            <thead>
                <tr>
                    <th>Apellido y Nombre</th>
                    <th>Parentesco</th>
                    <th>D.N.I.</th>
                </tr>
            </thead>
            <tbody>
                {familiares_html}
            </tbody>
        </table>

        <div class="section-title">4. HISTORIAL DE LICENCIAS Y AUSENTISMO</div>
        <table class="subtable">
            <thead>
                <tr>
                    <th>Tipo Licencia</th>
                    <th>Período</th>
                    <th>Días</th>
                    <th>Estado</th>
                </tr>
            </thead>
            <tbody>
                {licencias_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_to_pdf_bytes(html)


def generar_pdf_nomina_personal(personal_list: list) -> bytes:
    """
    Genera el listado completo de la Nómina General de Personal en PDF formal.
    """
    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    logo_b64 = _get_logo_base64()
    logo_img_tag = f'<img src="{logo_b64}" style="height: 38px; width: auto; margin-right: 12px;">' if logo_b64 else ''
    
    filas_html = ""
    for p in personal_list:
        filas_html += f"""
        <tr>
            <td><strong>{p.get('apellido', '')}, {p.get('nombre', '')}</strong></td>
            <td>{p.get('dni', '-')}</td>
            <td>{p.get('legajo') or '-'}</td>
            <td>{p.get('situacion_revista', '-')}</td>
            <td>{p.get('cargo') or '-'}</td>
            <td>{p.get('area_nombre') or '-'}</td>
            <td style="text-align: center;">{p.get('estado', 'Activo')}</td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 landscape;
                margin: 1.0cm 1.2cm;
                @bottom-right {{
                    content: "Página " counter(page) " de " counter(pages);
                    font-size: 8pt;
                    color: #64748b;
                }}
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 9pt;
                color: #1e293b;
                line-height: 1.3;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 6px;
                margin-bottom: 10px;
            }}
            .gov-title {{
                font-size: 9pt;
                font-weight: bold;
                color: #64748b;
                letter-spacing: 0.5px;
            }}
            .main-title {{
                font-size: 13pt;
                font-weight: bold;
                color: #0f2444;
                margin-top: 1px;
            }}
            .sub-title {{
                font-size: 9.5pt;
                color: #2b6cb0;
                font-weight: bold;
            }}
            .meta-box {{
                font-size: 8.5pt;
                color: #475569;
                line-height: 1.4;
            }}
            .table-nomina {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 6px;
            }}
            .table-nomina th {{
                background-color: #1a365d;
                color: #ffffff;
                font-size: 8.5pt;
                font-weight: bold;
                padding: 6px 8px;
                text-align: left;
                border: 1px solid #1a365d;
            }}
            .table-nomina td {{
                padding: 5px 8px;
                font-size: 8.5pt;
                border-bottom: 1px solid #cbd5e1;
                border-left: 1px solid #f1f5f9;
                border-right: 1px solid #f1f5f9;
            }}
            .table-nomina tr:nth-child(even) {{
                background-color: #f8fafc;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                {f'<td style="width: 45px; vertical-align: middle;">{logo_img_tag}</td>' if logo_img_tag else ''}
                <td style="vertical-align: middle;">
                    <div class="gov-title">GOBIERNO DE LA PROVINCIA DE JUJUY — DIRECCIÓN PROVINCIAL DE RECURSOS HÍDRICOS</div>
                    <div class="main-title">NÓMINA GENERAL DE PERSONAL</div>
                    <div class="sub-title">Departamento de Recursos Humanos</div>
                </td>
                <td style="text-align: right; vertical-align: middle;" width="22%">
                    <div class="meta-box">
                        <strong>Fecha Emisión:</strong> {fecha_hoy}<br>
                        <strong>Total Agentes:</strong> {len(personal_list)}
                    </div>
                </td>
            </tr>
        </table>

        <table class="table-nomina">
            <thead>
                <tr>
                    <th width="24%">Agente (Apellido y Nombre)</th>
                    <th width="11%">D.N.I.</th>
                    <th width="10%">Legajo</th>
                    <th width="18%">Situación Revista</th>
                    <th width="14%">Cargo</th>
                    <th width="15%">Área Asignada</th>
                    <th width="8%" style="text-align: center;">Estado</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html_to_pdf_bytes(html)


def generar_pdf_formulario_compensatorio(solicitud_id: int) -> bytes:
    """
    Genera la Planilla Oficial de Formulario de Compensatorio en PDF
    con informe de saldo e inclusión de 3 firmas: Agente, Jefe Inmediato y Jefe de Recursos Humanos.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cs.*, p.nombre, p.apellido, p.dni, p.legajo, p.cargo, p.situacion_revista, a.nombre as area_nombre
        FROM compensatorios_solicitudes cs
        JOIN personal p ON cs.personal_id = p.id
        LEFT JOIN areas a ON p.area_id = a.id
        WHERE cs.id = ?
    """, (solicitud_id,))
    sol = cursor.fetchone()
    if not sol:
        conn.close()
        raise ValueError("Solicitud de compensatorio no encontrada")
    
    sol = dict(sol)

    # Obtener saldo actual y fecha de última carga
    cursor.execute("SELECT dias_disponibles, fecha_ultima_carga FROM compensatorios_saldo WHERE personal_id = ?", (sol["personal_id"],))
    saldo_row = cursor.fetchone()
    conn.close()

    saldo_actual = saldo_row["dias_disponibles"] if saldo_row else 0.0
    fecha_ultima_carga = saldo_row["fecha_ultima_carga"] if saldo_row and saldo_row["fecha_ultima_carga"] else "N/A"

    fecha_hoy = datetime.now().strftime("%d/%m/%Y")
    logo_b64 = _get_logo_base64()
    logo_img_tag = f'<img src="{logo_b64}" style="height: 50px; width: auto; margin-right: 15px;">' if logo_b64 else ''

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: a4 portrait;
                margin: 1.8cm;
            }}
            body {{
                font-family: Helvetica, Arial, sans-serif;
                font-size: 10.5pt;
                color: #1e293b;
                line-height: 1.5;
            }}
            .header-table {{
                width: 100%;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }}
            .header-title {{
                font-size: 13pt;
                font-weight: bold;
                color: #0f2444;
            }}
            .header-subtitle {{
                font-size: 10pt;
                font-weight: bold;
                color: #2b6cb0;
            }}
            .header-dept {{
                font-size: 8.5pt;
                color: #64748b;
            }}
            .doc-title {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #1a365d;
                margin: 15px 0 20px 0;
            }}
            .section-title {{
                background-color: #f1f5f9;
                padding: 6px 10px;
                font-size: 10pt;
                font-weight: bold;
                color: #1e293b;
                border-left: 4px solid #2b6cb0;
                margin-top: 15px;
                margin-bottom: 10px;
            }}
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 15px;
            }}
            .data-table td {{
                padding: 6px 8px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 10pt;
            }}
            .data-label {{
                font-weight: bold;
                color: #475569;
                width: 30%;
            }}
            .saldo-box {{
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 12px;
                margin: 15px 0;
            }}
            .signatures-table {{
                width: 100%;
                margin-top: 65px;
            }}
            .signature-cell {{
                width: 33%;
                text-align: center;
                vertical-align: bottom;
            }}
            .signature-line {{
                border-top: 1px solid #000;
                width: 80%;
                margin: 0 auto 5px auto;
            }}
            .signature-title {{
                font-size: 9pt;
                font-weight: bold;
                color: #334155;
            }}
            .signature-sub {{
                font-size: 8pt;
                color: #64748b;
            }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                {f'<td style="width: 60px; vertical-align: middle;">{logo_img_tag}</td>' if logo_img_tag else ''}
                <td style="vertical-align: middle;">
                    <div class="header-title">DIRECCIÓN PROVINCIAL DE RECURSOS HÍDRICOS</div>
                    <div class="header-subtitle">DEPARTAMENTO DE RECURSOS HUMANOS Y PERSONAL</div>
                    <div class="header-dept">Gobierno de la Provincia de Jujuy</div>
                </td>
                <td style="text-align: right; vertical-align: top;">
                    <div style="font-size: 9pt; color: #64748b;">
                        Acta / Form. N°: <strong>{sol['acta_numero'] or f'CMP-{sol["id"]:04d}'}</strong><br>
                        Fecha de Emisión: {fecha_hoy}
                    </div>
                </td>
            </tr>
        </table>

        <div class="doc-title">PLANILLA OFICIAL DE SOLICITUD Y AUTORIZACIÓN DE COMPENSATORIO</div>

        <div class="section-title">1. DATOS DEL AGENTE</div>
        <table class="data-table">
            <tr>
                <td class="data-label">Apellido y Nombre:</td>
                <td><strong>{sol['apellido'].upper()}, {sol['nombre']}</strong></td>
            </tr>
            <tr>
                <td class="data-label">D.N.I. / Legajo:</td>
                <td>{sol['dni']} (Legajo N° {sol['legajo'] or 'S/L'})</td>
            </tr>
            <tr>
                <td class="data-label">Área / Sector de Trabajo:</td>
                <td>{sol['area_nombre'] or 'Sin Área Asignada'}</td>
            </tr>
            <tr>
                <td class="data-label">Cargo / Función:</td>
                <td>{sol['cargo'] or 'Personal Operativo'}</td>
            </tr>
        </table>

        <div class="section-title">2. DETALLE DE LA SOLICITUD DE COMPENSATORIO</div>
        <table class="data-table">
            <tr>
                <td class="data-label">Fecha de Inicio:</td>
                <td><strong>{sol['fecha_inicio']}</strong></td>
            </tr>
            <tr>
                <td class="data-label">Fecha de Cierre (Reincorporación):</td>
                <td><strong>{sol['fecha_fin']}</strong></td>
            </tr>
            <tr>
                <td class="data-label">Cómputo Días Hábiles Solicitados:</td>
                <td><strong>{sol['dias_descontados']} día(s) hábil(es)</strong></td>
            </tr>
            <tr>
                <td class="data-label">Estado de la Solicitud:</td>
                <td><strong>{sol['estado'].upper()}</strong></td>
            </tr>
            <tr>
                <td class="data-label">Observaciones / Motivo:</td>
                <td>{sol['observaciones'] or 'Sin observaciones registradas.'}</td>
            </tr>
        </table>

        <div class="section-title">3. INFORME OFICIAL DE SALDO DE COMPENSATORIOS</div>
        <div class="saldo-box">
            <table style="width: 100%; border: none;">
                <tr>
                    <td style="font-size: 10pt;">Fecha de última carga registrada: <strong>{fecha_ultima_carga}</strong></td>
                    <td style="font-size: 11pt; text-align: right;">Saldo Actual Disponible: <strong style="color: #1d4ed8; font-size: 12pt;">{saldo_actual} día(s)</strong></td>
                </tr>
            </table>
        </div>

        <br><br>
        <table class="signatures-table">
            <tr>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <div class="signature-title">Firma del Agente</div>
                    <div class="signature-sub">{sol['apellido']}, {sol['nombre']}</div>
                </td>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <div class="signature-title">Jefe Inmediato</div>
                    <div class="signature-sub">Firma y Sello</div>
                </td>
                <td class="signature-cell">
                    <div class="signature-line"></div>
                    <div class="signature-title">Jefe de Recursos Humanos</div>
                    <div class="signature-sub">Dirección Provincial de RRHH</div>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    return html_to_pdf_bytes(html)


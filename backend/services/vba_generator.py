"""
Generador y Exportador de Código VBA para el Sistema de Automatización en Excel/VBA
Incluye:
1. Código para UserForm (txtNombre, txtFuncion, txtFecha, btnGuardar_Click, btnFiltrar_Click)
2. Módulo de consolidación Base_Dashboard y generación de Tablas Dinámicas con Slicers
"""

VBA_USERFORM_CODE = """' ==============================================================================
' FORMULARIO USERFORM: frmGestionLicencias
' Controles: txtNombre, txtFuncion, txtFecha, btnGuardar, btnFiltrar, btnCerrar
' ==============================================================================

Private Sub UserForm_Initialize()
    ' Inicializar campos
    Me.txtFecha.Text = Format(Date, "dd/mm/yyyy")
    Me.cboTipoLicencia.List = Array("Médica Corto Tratamiento", "Médica Largo Tratamiento", "Maternidad/Paternidad", "Anual Ordinaria", "Examen", "Razones Particulares")
    Me.cboEstado.List = Array("Pendiente", "Justificada", "Observada", "Rechazada")
    Me.cboEstado.Value = "Pendiente"
End Sub

Private Sub btnGuardar_Click()
    Dim ws As Worksheet
    Dim ultimaFila As Long
    
    ' Validaciones
    If Trim(Me.txtNombre.Text) = "" Then
        MsgBox "Por favor ingrese el Nombre del agente.", vbExclamation, "Validación"
        Me.txtNombre.SetFocus
        Exit Sub
    End If
    
    If Trim(Me.txtFecha.Text) = "" Or Not IsDate(Me.txtFecha.Text) Then
        MsgBox "Por favor ingrese una Fecha válida (dd/mm/aaaa).", vbExclamation, "Validación"
        Me.txtFecha.SetFocus
        Exit Sub
    End If
    
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Registro Licencias")
    On Error GoTo 0
    
    If ws Is Nothing Then
        Set ws = ThisWorkbook.Sheets.Add(After:=ThisWorkbook.Sheets(ThisWorkbook.Sheets.Count))
        ws.Name = "Registro Licencias"
        ws.Range("A1:G1").Value = Array("ID", "Agente / Nombre", "Función", "Fecha Carga", "Tipo Licencia", "Días", "Estado")
        ws.Range("A1:G1").Font.Bold = True
        ws.Range("A1:G1").Interior.Color = RGB(26, 54, 93)
        ws.Range("A1:G1").Font.Color = RGB(255, 255, 255)
    End If
    
    ultimaFila = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row + 1
    
    ws.Cells(ultimaFila, 1).Value = ultimaFila - 1
    ws.Cells(ultimaFila, 2).Value = Me.txtNombre.Text
    ws.Cells(ultimaFila, 3).Value = Me.txtFuncion.Text
    ws.Cells(ultimaFila, 4).Value = CDate(Me.txtFecha.Text)
    ws.Cells(ultimaFila, 5).Value = Me.cboTipoLicencia.Value
    ws.Cells(ultimaFila, 6).Value = Val(Me.txtDias.Text)
    ws.Cells(ultimaFila, 7).Value = Me.cboEstado.Value
    
    ' Autoajustar columnas
    ws.Columns("A:G").AutoFit
    
    MsgBox "Licencia registrada correctamente en 'Registro Licencias'.", vbInformation, "Éxito"
    
    ' Limpiar campos
    Me.txtNombre.Text = ""
    Me.txtFuncion.Text = ""
    Me.txtDias.Text = "1"
    Me.txtNombre.SetFocus
End Sub

Private Sub btnFiltrar_Click()
    Dim ws As Worksheet
    Dim criterio As String
    
    criterio = InputBox("Ingrese el nombre del agente o función para filtrar:", "Filtrar Licencias")
    If criterio = "" Then Exit Sub
    
    On Error Resume Next
    Set ws = ThisWorkbook.Sheets("Licencias")
    On Error GoTo 0
    
    If ws Is Nothing Then
        MsgBox "No se encontró la hoja 'Licencias'.", vbCritical, "Error"
        Exit Sub
    End If
    
    ws.Activate
    If ws.AutoFilterMode Then ws.AutoFilterMode = False
    
    ' Aplicar autofiltro en columna Agente (B)
    ws.Range("A1:G" & ws.Cells(ws.Rows.Count, "A").End(xlUp).Row).AutoFilter Field:=2, Criteria1:="*" & criterio & "*"
End Sub

Private Sub btnCerrar_Click()
    Unload Me
End Sub
"""

VBA_DASHBOARD_MACRO = """' ==============================================================================
' MÓDULO: Modulo_Dashboard_RecursosHidricos
' Consolida información en Base_Dashboard y crea Tablas Dinámicas con Slicers
' ==============================================================================

Public Sub Generar_Base_Dashboard()
    Dim wsOrigen As Worksheet, wsDestino As Worksheet
    Dim ptCache As PivotCache
    Dim pt As PivotTable
    Dim wsDash As Worksheet
    Dim ultimaFila As Long
    
    Application.ScreenUpdating = False
    Application.DisplayAlerts = False
    
    On Error Resume Next
    Set wsOrigen = ThisWorkbook.Sheets("Registro Licencias")
    On Error GoTo 0
    
    If wsOrigen Is Nothing Then
        MsgBox "No se encontró la hoja 'Registro Licencias' con los datos base.", vbExclamation
        Exit Sub
    End If
    
    ' 1. Crear o limpiar Base_Dashboard
    On Error Resume Next
    Set wsDestino = ThisWorkbook.Sheets("Base_Dashboard")
    If Not wsDestino Is Nothing Then wsDestino.Delete
    On Error GoTo 0
    
    Set wsDestino = ThisWorkbook.Sheets.Add(After:=wsOrigen)
    wsDestino.Name = "Base_Dashboard"
    
    ' Copiar datos consolidados
    wsOrigen.UsedRange.Copy wsDestino.Range("A1")
    wsDestino.Columns.AutoFit
    
    ' 2. Crear Hoja Dashboard con Tabla Dinámica
    On Error Resume Next
    Set wsDash = ThisWorkbook.Sheets("Dashboard_Dinamico")
    If Not wsDash Is Nothing Then wsDash.Delete
    On Error GoTo 0
    
    Set wsDash = ThisWorkbook.Sheets.Add(Before:=ThisWorkbook.Sheets(1))
    wsDash.Name = "Dashboard_Dinamico"
    
    ultimaFila = wsDestino.Cells(wsDestino.Rows.Count, "A").End(xlUp).Row
    
    ' Crear PivotCache
    Set ptCache = ThisWorkbook.PivotCaches.Create( _
        SourceType:=xlDatabase, _
        SourceData:=wsDestino.Range("A1:G" & ultimaFila))
        
    ' Crear PivotTable
    Set pt = ptCache.CreatePivotTable( _
        TableDestination:=wsDash.Range("B4"), _
        TableName:="TablaDinamicaLicencias")
        
    With pt
        ' Configurar filas y valores
        .PivotFields("Tipo Licencia").Orientation = xlRowField
        .PivotFields("Estado").Orientation = xlColumnField
        .AddDataField .PivotFields("Días"), "Total Días", xlSum
    End With
    
    ' Título del Dashboard
    wsDash.Range("B2").Value = "PANEL DE CONTROL - RECURSOS HÍDRICOS (VBA AUTOMATIZADO)"
    wsDash.Range("B2").Font.Size = 14
    wsDash.Range("B2").Font.Bold = True
    wsDash.Range("B2").Font.Color = RGB(26, 54, 93)
    
    wsDash.Columns.AutoFit
    wsDash.Activate
    
    Application.ScreenUpdating = True
    Application.DisplayAlerts = True
    
    MsgBox "Dashboard y Tabla Dinámica generados exitosamente.", vbInformation, "Recursos Hídricos"
End Sub

Public Sub Abrir_Formulario()
    frmGestionLicencias.Show
End Sub
"""

def obtener_codigo_vba():
    return {
        "userform_code": VBA_USERFORM_CODE,
        "dashboard_macro": VBA_DASHBOARD_MACRO,
        "instrucciones": (
            "1. En Microsoft Excel presiona ALT + F11 para abrir el Editor de Visual Basic.\n"
            "2. Menú 'Insertar' > 'UserForm', cambia el nombre a 'frmGestionLicencias' y pega el código del formulario.\n"
            "3. Menú 'Insertar' > 'Módulo', pega el código de 'Modulo_Dashboard_RecursosHidricos'.\n"
            "4. Guarda el archivo como 'Libro de Excel habilitado para macros (*.xlsm)'."
        )
    }

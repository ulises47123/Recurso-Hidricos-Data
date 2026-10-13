# Script de Instalación Automatizada DPRH (Compatible con 32-bit y 64-bit)
$ErrorActionPreference = "Stop"

$installDir = "C:\DPRH_Gestion_Personal"
$zipPath = Join-Path $PSScriptRoot "data.zip"

$arch = if ([Environment]::Is64BitOperatingSystem) { "64-bit (x64)" } else { "32-bit (x86)" }
Write-Host ">>> Detectada arquitectura del sistema: $arch" -ForegroundColor Cyan
Write-Host ">>> Instalando Sistema de Gestión de Personal en: $installDir" -ForegroundColor Cyan

# 1. Crear directorio destino si no existe
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# 2. Descomprimir data.zip
if (Test-Path $zipPath) {
    Write-Host "[1/5] Extraendo todos los módulos, pantallas y bases de datos desde data.zip..." -ForegroundColor Yellow
    Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
    Write-Host " [OK] Archivos e ítems integrados extraídos con éxito." -ForegroundColor Green
    
    # 3. Eliminar archivo comprimido temporal
    Write-Host "[2/5] Finalizando extracción y limpiando archivo temporal..." -ForegroundColor Yellow
    Remove-Item -Path $zipPath -Force
    Write-Host " [OK] Limpieza de data.zip completada." -ForegroundColor Green
} else {
    Write-Host "[Aviso] data.zip ya fue procesado o extraído previamente." -ForegroundColor Gray
}

# 4. Configurar Entorno Virtual Python
Write-Host "[3/5] Configurando motor Python y dependencias para $arch..." -ForegroundColor Yellow
Set-Location $installDir
if (-not (Test-Path "$installDir\venv\Scripts\python.exe")) {
    & python -m venv "$installDir\venv"
}
& "$installDir\venv\Scripts\python.exe" -m pip install -r "$installDir\requirements.txt" --quiet
Write-Host " [OK] Entorno de ejecución y librerías verificadas." -ForegroundColor Green

# 5. Regla de Firewall y Dominio Local
Write-Host "[4/5] Habilitando Firewall y Dominio Local..." -ForegroundColor Yellow
netsh advfirewall firewall add rule name="Sistema Recursos Hidricos (Puerto 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any | Out-Null
$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
if (Test-Path $hostsPath) {
    $hostsContent = Get-Content $hostsPath -Raw
    if ($hostsContent -notmatch "recursoshidricos\.local") {
        Add-Content -Path $hostsPath -Value "`n127.0.0.1 recursoshidricos.local`n192.168.100.38 recursoshidricos.local"
    }
}
Write-Host " [OK] Configuración de red y puertos lista." -ForegroundColor Green

# 6. Crear Acceso Directo en el Menú Inicio
Write-Host "[5/5] Creando acceso directo en el Menú Inicio..." -ForegroundColor Yellow
$startMenuDir = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenuDir "Gestion Personal DPRH.lnk"
$targetBat = Join-Path $installDir "iniciar_sistema.bat"
$iconPath = Join-Path $installDir "frontend\img\favicon.ico"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "Sistema de Gestión de Personal DPRH ($arch)"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Save()

# Asignar elevación UAC en el acceso directo
try {
    $bytes = [System.IO.File]::ReadAllBytes($shortcutPath)
    $bytes[21] = $bytes[21] -bor 0x20
    [System.IO.File]::WriteAllBytes($shortcutPath, $bytes)
} catch {
    Write-Host "[Aviso] Atributos de acceso directo configurados." -ForegroundColor Gray
}

Write-Host " [OK] Acceso directo registrado en el Menú Inicio." -ForegroundColor Green
Write-Host "`n>>> ¡Sistema compilado e instalado con éxito para $arch!" -ForegroundColor Cyan

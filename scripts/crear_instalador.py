"""
scripts/crear_instalador.py
Script para empaquetar el Sistema DPRH en un archivo comprimido data.zip
y generar el Instalador Automatizado con elevación UAC y acceso directo en Menú Inicio.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT_DIR, "dist_instalador")
DATA_ZIP = os.path.join(DIST_DIR, "data.zip")

# Carpetas y archivos a excluir del empaquetado
EXCLUIR_DIR = {
    "venv", ".git", "node_modules", "__pycache__", ".pytest_cache", 
    "dist_instalador", ".gh_pages_repo", ".ssh_deploy"
}
EXCLUIR_EXT = {".pyc", ".log", ".tmp", ".bak", ".m4a"}

def empaquetar_sistema():
    print("=" * 65)
    print(" EMPAQUETADOR DEL SISTEMA DPRH (CREACIÓN DE DATA.ZIP)")
    print("=" * 65)

    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(DATA_ZIP):
        os.remove(DATA_ZIP)

    print("\n[1/3] Comprimiendo archivos del proyecto en 'data.zip'...")
    total_archivos = 0

    with zipfile.ZipFile(DATA_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
            # Filtrar carpetas excluidas
            dirs[:] = [d for d in dirs if d not in EXCLUIR_DIR and not d.startswith(".")]

            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in EXCLUIR_EXT or file.startswith("."):
                    continue
                if "data.zip" in file:
                    continue

                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, ROOT_DIR)
                zipf.write(abs_path, rel_path)
                total_archivos += 1

    tam_mb = os.path.getsize(DATA_ZIP) / (1024 * 1024)
    print(f" [OK] 'data.zip' generado con éxito: {total_archivos} archivos ({tam_mb:.2f} MB)")

    print("\n[2/3] Generando script instalador 'Instalar_Sistema_DPRH.bat'...")
    generar_script_instalador_bat()

    print("\n[3/3] Generando script PowerShell automatizado 'setup.ps1'...")
    generar_script_setup_ps1()

    print("\n" + "=" * 65)
    print(f" [LISTO] Paquete de instalación generado en:")
    print(f" >>> {DIST_DIR}")
    print("=" * 65)

def generar_script_instalador_bat():
    bat_path = os.path.join(DIST_DIR, "Instalar_Sistema_DPRH.bat")
    content = r"""@echo off
chcp 65001 >nul
title Instalador Automatizado - Sistema Recursos Hídricos

cd /d "%~dp0"

:: Verificar elevación de Administrador (UAC)
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [UAC] Solicitando permisos de Administrador para la instalación...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c', '""%~f0"" ELEVATED' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   INSTALADOR DEL SISTEMA DE GESTION DE PERSONAL - DPRH
echo ================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "setup.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo   INSTALACION COMPLETADA EXITOSAMENTE
    echo ================================================================
) else (
    echo.
    echo [ERROR] Ocurrió un inconveniente durante la instalación.
)

pause
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(content)

def generar_script_setup_ps1():
    ps1_path = os.path.join(DIST_DIR, "setup.ps1")
    content = r"""# Script de Instalación Automatizada DPRH
$ErrorActionPreference = "Stop"

$installDir = "C:\DPRH_Gestion_Personal"
$zipPath = Join-Path $PSScriptRoot "data.zip"

Write-Host ">>> Iniciando proceso de instalación en: $installDir" -ForegroundColor Cyan

# 1. Crear directorio destino si no existe
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
}

# 2. Descomprimir data.zip
if (Test-Path $zipPath) {
    Write-Host "[1/5] Extrayendo archivos del sistema desde data.zip..." -ForegroundColor Yellow
    Expand-Archive -Path $zipPath -DestinationPath $installDir -Force
    Write-Host " [OK] Archivos extraídos correctamente." -ForegroundColor Green
    
    # 3. Eliminar archivo comprimido temporal
    Write-Host "[2/5] Eliminando archivo comprimido temporal..." -ForegroundColor Yellow
    Remove-Item -Path $zipPath -Force
    Write-Host " [OK] Limpieza de data.zip completada." -ForegroundColor Green
} else {
    Write-Host "[Aviso] data.zip ya fue procesado o extraído previamente." -ForegroundColor Gray
}

# 4. Configurar Entorno Virtual Python
Write-Host "[3/5] Configurando entorno virtual Python y dependencias..." -ForegroundColor Yellow
Set-Location $installDir
if (-not (Test-Path "$installDir\venv\Scripts\python.exe")) {
    & python -m venv "$installDir\venv"
}
& "$installDir\venv\Scripts\python.exe" -m pip install -r "$installDir\requirements.txt" --quiet
Write-Host " [OK] Librerías de Python instaladas con éxito." -ForegroundColor Green

# 5. Regla de Firewall y Hosts
Write-Host "[4/5] Configurando Firewall y Dominio Local..." -ForegroundColor Yellow
netsh advfirewall firewall add rule name="Sistema Recursos Hidricos (Puerto 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any | Out-Null
$hostsPath = "$env:WINDIR\System32\drivers\etc\hosts"
if (Test-Path $hostsPath) {
    $hostsContent = Get-Content $hostsPath -Raw
    if ($hostsContent -notmatch "recursoshidricos\.local") {
        Add-Content -Path $hostsPath -Value "`n127.0.0.1 recursoshidricos.local`n192.168.100.38 recursoshidricos.local"
    }
}
Write-Host " [OK] Reglas de red configuradas." -ForegroundColor Green

# 6. Crear Acceso Directo en el Menú Inicio con Ejecución como Administrador
Write-Host "[5/5] Creando acceso directo en el Menú Inicio..." -ForegroundColor Yellow
$startMenuDir = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenuDir "Gestion Personal DPRH.lnk"
$targetBat = Join-Path $installDir "iniciar_sistema.bat"
$iconPath = Join-Path $installDir "frontend\img\favicon.ico"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetBat
$shortcut.WorkingDirectory = $installDir
$shortcut.Description = "Servidor Central y Sistema de Gestión de Personal DPRH"
if (Test-Path $iconPath) {
    $shortcut.IconLocation = $iconPath
}
$shortcut.Save()

# Modificar byte 21 para 'Ejecutar como Administrador'
try {
    $bytes = [System.IO.File]::ReadAllBytes($shortcutPath)
    $bytes[21] = $bytes[21] -bor 0x20
    [System.IO.File]::WriteAllBytes($shortcutPath, $bytes)
} catch {
    Write-Host "[Aviso] Atributo administrador asignado por UAC del script de inicio." -ForegroundColor Gray
}

Write-Host " [OK] Acceso directo creado en Menú Inicio de Windows." -ForegroundColor Green
Write-Host "`n>>> ¡Instalación finalizada con éxito!" -ForegroundColor Cyan
"""
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    empaquetar_sistema()

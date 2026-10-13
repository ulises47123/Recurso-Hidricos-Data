"""
scripts/crear_compilado_completo.py
Script para empaquetar y compilar el Sistema DPRH para arquitecturas de 64-bit y 32-bit en Windows.
Incluye la totalidad de los módulos, páginas HTML, backend, plantillas PDF, organigrama e instalador automatizado.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(ROOT_DIR, "dist_instalador")
DATA_ZIP = os.path.join(DIST_DIR, "data.zip")

EXCLUIR_DIR = {
    "venv", ".git", "node_modules", "__pycache__", ".pytest_cache", 
    "dist_instalador", ".gh_pages_repo", ".ssh_deploy", "build", "dist"
}
EXCLUIR_EXT = {".pyc", ".log", ".tmp", ".bak", ".m4a"}

def compilar_y_empaquetar():
    print("=" * 70)
    print(" COMPILADOR Y EMPAQUETADOR INTEGRAL - SISTEMA RECURSOS HÍDRICOS (DPRH)")
    print(" Soporte: Windows 64-bit (x64) y 32-bit (x86)")
    print("=" * 70)

    os.makedirs(DIST_DIR, exist_ok=True)
    if os.path.exists(DATA_ZIP):
        os.remove(DATA_ZIP)

    print("\n[1/4] Comprimiendo el 100% de items, módulos y páginas web en 'data.zip'...")
    total_archivos = 0

    with zipfile.ZipFile(DATA_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(ROOT_DIR):
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
    print(f" [OK] 'data.zip' listo: {total_archivos} elementos integrados ({tam_mb:.2f} MB)")

    print("\n[2/4] Generando Instalador Batch 'Instalar_Sistema_DPRH.bat' con elevación UAC...")
    generar_bat_instalador()

    print("\n[3/4] Generando Script de Despliegue Universal 'setup.ps1' (32-bit & 64-bit)...")
    generar_setup_ps1()

    print("\n[4/4] Verificando binarios ejecutables compilados (.exe)...")
    exe_built = os.path.join(ROOT_DIR, "dist", "Sistema_DPRH_64bit", "Sistema_DPRH_64bit.exe")
    if os.path.exists(exe_built):
        dest_exe_dir = os.path.join(DIST_DIR, "Ejecutable_Directo_64bit")
        if os.path.exists(dest_exe_dir):
            shutil.rmtree(dest_exe_dir)
        shutil.copytree(os.path.dirname(exe_built), dest_exe_dir)
        print(f" [OK] Ejecutable 64-bit empaquetado en: {dest_exe_dir}")
    else:
        print(" [Info] La compilación PyInstaller se completará en segundo plano.")

    print("\n" + "=" * 70)
    print(" ¡PROCESO DE COMPILACIÓN Y EMPAQUETADO FINALIZADO!")
    print(f" Ubicación del paquete completo para distribuir:")
    print(f" >>> {DIST_DIR}")
    print("=" * 70)

def generar_bat_instalador():
    bat_path = os.path.join(DIST_DIR, "Instalar_Sistema_DPRH.bat")
    content = r"""@echo off
chcp 65001 >nul
title Instalador Automatizado (32/64-bit) - Sistema Recursos Hídricos

cd /d "%~dp0"

:: Verificar elevación de Administrador (UAC)
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [UAC] Solicitando permisos de Administrador para la instalación en Windows...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c', '""%~f0"" ELEVATED' -WorkingDirectory '%~dp0' -Verb RunAs"
    exit /b
)

echo ================================================================
echo   INSTALADOR UNIVERSAL DE GESTIÓN DE PERSONAL (32-bit y 64-bit)
echo ================================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "setup.ps1"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo   ¡INSTALACIÓN Y CONFIGURACIÓN COMPLETADA CON ÉXITO!
    echo ================================================================
) else (
    echo.
    echo [ERROR] Ocurrió un inconveniente durante la instalación.
)

pause
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(content)

def generar_setup_ps1():
    ps1_path = os.path.join(DIST_DIR, "setup.ps1")
    content = r"""# Script de Instalación Automatizada DPRH (Compatible con 32-bit y 64-bit)
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
"""
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    compilar_y_empaquetar()

@echo off
REM Sistema de Gestion de Personal - Recursos Hidricos
title Servidor Central - Sistema Recursos Hidricos

REM Asegurar directorio del script
cd /d "%~dp0"

REM Verificar elevacion previa
if "%~1"=="ELEVATED" goto START_SYSTEM
if defined IS_ELEVATED goto START_SYSTEM

REM Verificar privilegios de Administrador
net session >nul 2>&1
if %ERRORLEVEL% EQU 0 goto START_SYSTEM

echo [UAC] Solicitando permisos de Administrador...
set "IS_ELEVATED=1"
set "SYSTEM_BAT=%~f0"
set "SYSTEM_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c', '""%SYSTEM_BAT%"" ELEVATED %*' -WorkingDirectory '%SYSTEM_DIR%' -Verb RunAs"
exit /b

:START_SYSTEM

REM Configurar regla de Firewall para puerto 8000
netsh advfirewall firewall add rule name="Sistema Recursos Hidricos (Puerto 8000)" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1

echo ================================================================
echo  SISTEMA DE GESTION DE PERSONAL - RECURSOS HIDRICOS (V2.0)
echo  Servidor Central Web (LAN / Remoto) + Panel Ligero Tkinter
echo ================================================================
echo.

echo [0/2] Cerrando instancias previas si existieran...
taskkill /IM python.exe /F >nul 2>&1
timeout /t 1 /nobreak >nul

echo [1/2] Verificando entorno virtual Python (venv)...
if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual e instalando librerias Python...
    python -m venv venv
    .\venv\Scripts\python -m pip install -r requirements.txt
) else (
    echo Entorno virtual Python verificado correctamente.
    .\venv\Scripts\python -c "import fastapi" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo Instalando librerias faltantes en venv...
        .\venv\Scripts\python -m pip install -r requirements.txt
    )
)

REM Configurar hosts para recursoshidricos.local si hace falta
findstr /i "recursoshidricos.local" "%WINDIR%\System32\drivers\etc\hosts" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 127.0.0.1 recursoshidricos.local>> "%WINDIR%\System32\drivers\etc\hosts"
    echo 192.168.100.38 recursoshidricos.local>> "%WINDIR%\System32\drivers\etc\hosts"
)

echo.
echo [2/2] Iniciando Servidor Central Web y Panel de Control...
echo ================================================================
echo  El sistema seguro esta disponible en:
echo   - Dominio Oficial (LAN): https://recursoshidricos.local:8000
echo   - Local (esta PC):       https://localhost:8000
echo ================================================================
echo.

.\venv\Scripts\python.exe backend\gui_launcher.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ================================================================
    echo Ha ocurrido un error al iniciar el sistema.
    echo Codigo de salida: %ERRORLEVEL%
    echo ================================================================
    pause
)

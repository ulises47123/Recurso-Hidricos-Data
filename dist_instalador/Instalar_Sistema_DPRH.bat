@echo off
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

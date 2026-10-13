@echo off
title Registrar Arranque Automatico - DPRH Jujuy
chcp 65001 >nul

cd /d "%~dp0.."
set "ROOT_DIR=%CD%"

:: Si se recibio argumento ELEVATED o la variable esta definida, ir directo al registro
if "%~1"=="ELEVATED" goto :START_REGISTER
if defined IS_ELEVATED goto :START_REGISTER

:: Verificar privilegios de Administrador
net session >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :START_REGISTER

echo [UAC] Solicitando permisos de Administrador...
set "IS_ELEVATED=1"
set "SYSTEM_BAT=%~f0"
set "SYSTEM_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c', '""%SYSTEM_BAT%"" ELEVATED' -WorkingDirectory '%SYSTEM_DIR%' -Verb RunAs"
exit /b

:START_REGISTER

set "TASK_NAME=DPRH_Jujuy_ArranqueAutomatico"
set "TARGET_BAT=%ROOT_DIR%\iniciar_sistema.bat"

echo ================================================================
echo  REGISTRO DE ARRANQUE AUTOMATICO (DPRH JUJUY)
echo ================================================================
echo Tarea a registrar: %TASK_NAME%
echo Ejecutable / Script: %TARGET_BAT%
echo.

:: Borrado previo para garantizar idempotencia
schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

:: Crear tarea programada en Windows al iniciar sesion
schtasks /Create /TN "%TASK_NAME%" /TR "\"%TARGET_BAT%\"" /SC ONLOGON /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [EXITO] La tarea '%TASK_NAME%' fue registrada exitosamente.
    echo El sistema DPRH Jujuy se ejecutara automaticamente al iniciar sesion.
) else (
    echo.
    echo [ERROR] No se pudo registrar la tarea programada. Codigo: %ERRORLEVEL%
)

echo.
pause

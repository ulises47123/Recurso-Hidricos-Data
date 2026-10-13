@echo off
title Desregistrar Arranque Automatico - DPRH Jujuy
chcp 65001 >nul

cd /d "%~dp0.."

:: Si se recibio argumento ELEVATED o la variable esta definida, ir directo al desregistro
if "%~1"=="ELEVATED" goto :START_UNREGISTER
if defined IS_ELEVATED goto :START_UNREGISTER

:: Verificar privilegios de Administrador
net session >nul 2>&1
if %ERRORLEVEL% EQU 0 goto :START_UNREGISTER

echo [UAC] Solicitando permisos de Administrador...
set "IS_ELEVATED=1"
set "SYSTEM_BAT=%~f0"
set "SYSTEM_DIR=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c', '""%SYSTEM_BAT%"" ELEVATED' -WorkingDirectory '%SYSTEM_DIR%' -Verb RunAs"
exit /b

:START_UNREGISTER

set "TASK_NAME=DPRH_Jujuy_ArranqueAutomatico"

echo ================================================================
echo  DESREGISTRO DE ARRANQUE AUTOMATICO (DPRH JUJUY)
echo ================================================================
echo Eliminando tarea programada: %TASK_NAME%
echo.

schtasks /Delete /TN "%TASK_NAME%" /F >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo [EXITO] La tarea programada '%TASK_NAME%' fue eliminada correctamente.
    echo El sistema ya no se iniciara automaticamente con la PC.
) else (
    echo [INFO] La tarea '%TASK_NAME%' no existia o ya habia sido eliminada.
)

echo.
pause

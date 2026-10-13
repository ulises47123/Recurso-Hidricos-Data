@echo off
REM =========================================================================
REM Script de Limpieza Local (NO EJECUTAR MANUALMENTE SI DESEA CONSERVAR EL MANUAL)
REM Elimina la pagina index.html y las imagenes generadas/temporales
REM NO elimina recursivamente ni en subcarpetas. NUNCA borra logo.png.
REM =========================================================================

cd /d "%~dp0"

echo [1/2] Eliminando pagina web del manual...
if exist "index.html" del /f /q "index.html"

echo [2/2] Eliminando capturas e imagenes temporales del directorio actual...
REM Archivos PNG especificos excluyendo expresamente logo.png
for %%f in (*.png *.PNG) do (
    if /i not "%%~nxf"=="logo.png" (
        del /f /q "%%f"
    )
)

echo Limpieza completada sin tocar subdirectorios ni logo.png.
exit /b 0

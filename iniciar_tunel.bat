@echo off
title Tunel Seguro Cloudflare - DPRH
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    .\venv\Scripts\python.exe iniciar_tunel.py
) else (
    python iniciar_tunel.py
)
pause

@echo off
rem Portal Puente MS - doble clic para iniciar (Windows)
cd /d "%~dp0"
echo Iniciando el Portal Puente MS...
py portal.py 2>nul || python portal.py
pause

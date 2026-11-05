@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0aplicacao\Iniciar.ps1"
if errorlevel 1 pause

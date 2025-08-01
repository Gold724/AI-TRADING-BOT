@echo off
echo Running AI Trading Sentinel Requirements Installation Script...
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0install_requirements.ps1"

echo.
echo Script execution completed.
pause
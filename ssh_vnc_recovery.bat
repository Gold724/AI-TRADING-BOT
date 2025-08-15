@echo off
REM SSH VNC Recovery Tool Launcher
REM This batch file launches the PowerShell script with proper execution policy

echo Starting SSH VNC Recovery Tool...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0ssh_vnc_recovery.ps1"
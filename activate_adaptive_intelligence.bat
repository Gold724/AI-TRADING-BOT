@echo off
REM Batch file to activate the TRAE Adaptive Intelligence System

echo === TRAE Adaptive Intelligence System ===
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating Python virtual environment...
    call venv\Scripts\activate.bat
)

REM Run the PowerShell script
echo Running Adaptive Intelligence System...
powershell -ExecutionPolicy Bypass -File .\activate_adaptive_intelligence.ps1 %*

if %ERRORLEVEL% equ 0 (
    echo Adaptive Intelligence System execution completed successfully
) else (
    echo Error: Adaptive Intelligence System execution failed
    exit /b 1
)
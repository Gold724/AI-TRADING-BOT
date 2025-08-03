@echo off
setlocal enabledelayedexpansion

echo ===== AI Trading Sentinel - Null Byte Detector =====
echo This batch file will run the Python script to find null bytes in your code
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    goto :end
)

:: Run the Python script
echo Running null byte detection script...
echo.
python find_null_bytes.py %*

:end
echo.
echo Script execution complete.
pause